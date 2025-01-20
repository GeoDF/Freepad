import json, os
from pathlib import Path

from qtpy.QtWidgets import QApplication, QMessageBox
from qtpy.QtCore import QSharedMemory, QThread, QSettings

from pad.path import FREEPAD_PATH
from pad.ui import FreepadWindow
from pad.padio import Mid, MidiConnectionListener





# for debug only
from qtpy import QtCore
import traceback, sys

# debug sous eclipse
if QtCore.QT_VERSION >= 0x50501:
	def excepthook(type_, value, traceback_):
		traceback.print_exception(type_, value, traceback_)
		QtCore.qFatal('')
sys.excepthook = excepthook








class FreepadApp(QApplication):
	def __init__(self, args):
		super().__init__(args)
		self.knownPads = {}
		self.knownPadsNames = []
		self.connectedPadsNames = {}
		self.openedPads = {}
		self.defaultKit = {}
		self.defaultControls = {}
		self.qsettings = QSettings('geomaticien.com', 'Freepad')

		# Read known pads
		pdir = os.path.join(FREEPAD_PATH, "pads")
		for p in os.listdir(pdir):
			jsonfile = os.path.join(pdir, p)
			if not os.path.isfile(jsonfile):
				continue
			with open(jsonfile) as f:
				pad = json.load(f)
				if 'midiname' in pad:
					mn = pad['midiname']
					self.knownPads[mn] = pad
					self.knownPadsNames.append(mn)
				else:
					print('midiname not found in ' + pad)
			f.close()

		# Load default kit and default controls
		self._loadKit(self.defaultKit, self.qsettings.value('lastkit', self._get1stDefault('kits')))
		self._loadKit(self.defaultControls, self.qsettings.value('lastcontrols', self._get1stDefault('controls')))

		_openUI = False
		# Read connected known pads and open UI
		for in_name in Mid.get_input_names():
			mn = Mid.shortMidiName(in_name)
			if mn in self.knownPadsNames:
				self.connectedPadsNames[mn] = in_name
				self.openUI(mn, in_name)
				_openUI = True

		if len(self.openedPads) == 0:
			virtual_pad = 'LPD8'
			self.openUI(virtual_pad, '')
			_openUI = True
		if _openUI:
		# Start a MidiConnectionListener in the background
			self.mlcThread = QThread(self)
			self.mlc = MidiConnectionListener()
			self.mlc.moveToThread(self.mlcThread)
			self.mlcThread.started.connect(self.mlc.run)
			self.mlcThread.finished.connect(self.mlc.cancel)
			self.mlc.devicePlugged.connect(self.devicePlugged)
			self.mlc.deviceUnplugged.connect(self.deviceUnplugged)
			self.mlcThread.start()


	def _get1stDefault(self, d):
		path = FREEPAD_PATH.joinpath('midi').joinpath(d)
		if not path.is_dir():
			return False
		for k in os.listdir(path):
			fp = path.joinpath(k)
			if not fp.is_file():
					continue
			break
		return fp

	def _loadKit(self, var, fp):
		fp = Path(fp)
		if not fp.is_file():
			return false
		with open(fp, 'r', encoding='UTF-8') as f:
			for line in f:
				line = line.strip()
				name = line.lstrip('0123456789')
				num = line[0:len(line) - len(name)]
				if num.isdigit():
					num = num.strip()
					var[int(num)] = name

	def openUI(self, mn, in_name):
		self.sharedM = QSharedMemory('Freepad/' + mn)
		self.sharedM.attach()
		self.sharedM.unlock()
		self.sharedM.detach()
		if not self.sharedM.create(1):
			msg = mn + ' already started'
			mb = QMessageBox(QMessageBox.Warning, 'Freepad', msg)
			mb.exec()
			sys.exit()
		else:
			setattr(self, mn, FreepadWindow(self.knownPads[mn], in_name, self.defaultKit, self.defaultControls, self.qsettings))
			self.openedPads[mn] = getattr(self, mn)
			self.openedPads[mn].setObjectName("Pads" + mn)
			self.openedPads[mn].destroyed.connect(self.cleanExit)
			self.openedPads[mn].show()

	def devicePlugged(self, midiports):
		for mn in self.openedPads:
			self.openedPads[mn].plugged(midiports)

	def deviceUnplugged(self, midiports):
		for mn in self.openedPads:
			self.openedPads[mn].unplugged(midiports)


	def cleanExit(self):
		self.sharedM.attach()
		self.sharedM.unlock()
		self.sharedM.detach()
		self.mlcThread.quit()




