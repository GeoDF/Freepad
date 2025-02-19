import json, os, argparse
from pathlib import Path

from qtpy.QtWidgets import QApplication, QMessageBox
from qtpy.QtCore import QSharedMemory, QThread

from pad.path import FREEPAD_PATH, FREEPAD_IS_COMPILED
from pad.ui.common import Debug, tr
from pad.freepad_settings import Fsettings
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
		self.setApplicationName('Freepad')
		self.setApplicationVersion('0.9.9')
		self.setApplicationDisplayName('Freepad')
		self.setStyle("fusion") # required
		self.knownPads = {}
		self.knownPadsNames = []
		self.connectedPadsNames = {}
		self.openedPads = {}
		self.defaultKit = {}
		self.defaultControls = {}
		self.padname = None
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
					Debug.dbg('midiname not found in ' + pad)
			f.close()
		parser = argparse.ArgumentParser(
			prog = 'freepad' if FREEPAD_IS_COMPILED else 'python -m pad',
			description = 'Freepad version ' + self.applicationVersion() +'. Virtual midi controller and editor for real devices.',
			epilog = '')
		parser.add_argument('model', nargs = '?', default = 'LPD8', help = ', '.join(['"{}"'.format(n) for n in self.knownPadsNames]))
		parser.add_argument('-d', '--debug', help = tr('debug mode'), action='store_true', default = False)
		args = parser.parse_args()
		Debug.set(args.debug)
		self.padname = args.model

		# Load default kit and default controls
		self._loadKit(self.defaultKit, Fsettings().get('lastkit', self._get1stDefault('kits')))
		self._loadKit(self.defaultControls, Fsettings().get('lastcontrols', self._get1stDefault('controls')))

		_openUI = False
		if self.padname is None:
			# Read connected known pads and open UI
			for in_name in Mid.get_input_names():
				mn = Mid.shortMidiName(in_name)
				if mn in self.knownPadsNames:
					self.connectedPadsNames[mn] = in_name
					self.openUI(mn, in_name)
					_openUI = True
		else:
			for in_name in Mid.get_input_names():
				mn = Mid.shortMidiName(in_name)
				if mn == self.padname:
					self.connectedPadsNames[mn] = in_name
					self.openUI(mn, in_name)
					_openUI = True
					break
		if len(self.openedPads) == 0:
			virtual_pad = self.padname.upper() if self.padname is not None else 'LPD8'
			if virtual_pad in self.knownPadsNames:
				self.openUI(virtual_pad, '')
				_openUI = True
			else:
				Debug.dbg('"' + self.padname + '" is not a known device.')
				self._quit()

		if _openUI:
		# Start a MidiConnectionListener in the background
			self.mlcThread = QThread(self)
			self.mlc = MidiConnectionListener(self.knownPadsNames)
			self.mlc.moveToThread(self.mlcThread)
			self.mlcThread.started.connect(self.mlc.run)
			self.mlcThread.finished.connect(self.mlc.cancel)
			self.mlc.devicePlugged.connect(self.devicePlugged)
			self.mlc.deviceUnplugged.connect(self.deviceUnplugged)
			self.mlcThread.start()
		else:
			Debug.dbg('No pads found.')
			self._quit()

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
			return False
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
			self._quit()
		else:
			params = {'device': self.knownPads[mn],
				'in_name': in_name,
				'defaultKit': self.defaultKit,
				'defaultControls': self.defaultControls
			}
			setattr(self, mn, FreepadWindow(params))
			self.openedPads[mn] = getattr(self, mn)
			self.openedPads[mn].setObjectName("Pads" + mn)
			self.openedPads[mn].destroyed.connect(self.cleanExit)
			self.openedPads[mn].show()
		

	def devicePlugged(self, midiports):
		in_midiname = midiports['in'][0]
		out_midiname = midiports['out'][0]
		for mn in self.openedPads:
			if mn == Mid.shortMidiName(in_midiname):
				self.openedPads[mn].plugged(in_midiname, out_midiname)

	def deviceUnplugged(self, midiports):
		in_midiname = midiports['in'][0]
		#out_midiname = midiports['out'][0]
		for mn in self.openedPads:
			if mn == Mid.shortMidiName(in_midiname):
				self.openedPads[mn].unplugged()

	def cleanExit(self):
		self.sharedM.attach()
		self.sharedM.unlock()
		self.sharedM.detach()
		self.mlcThread.quit()

	def _quit(self):
		self.quit()
		self.exit()
		sys.exit()



