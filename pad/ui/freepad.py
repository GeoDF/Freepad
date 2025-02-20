import os, json

from qtpy.QtCore import QDir, QMetaObject, Qt, QThread,QTimer
from qtpy.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QGridLayout, \
	QHBoxLayout, QLabel, QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, \
	QStyle, QVBoxLayout, QWidget
from qtpy.QtGui import QIcon, QKeyEvent

from pad.path import FREEPAD_PATH, FREEPAD_ICON_PATH, imgUrl
from pad.freepad_settings import Fsettings
from pad.ui.common import Creator, Debug, \
	PadException, tr, \
	FREEPAD_TITLE_COLOR, \
	FREEPAD_NOTE_COLOR, \
	FREEPAD_BORD_COLOR, \
	FREEPAD_LGRADIENT, \
	FREEPAD_RGRADIENT, \
	FREEPAD_RGRADIENT_OVER
	
from pad.ui.controls import Knob, Pad, Program
from pad.ui.options import FreepadOptionsWindow
from pad.padio import PadIO, MidiConnectionListener


class FreepadWindow(QWidget, Creator):
	def __init__(self, params):
		super().__init__()
		self.setWindowIcon(QIcon(FREEPAD_ICON_PATH))
		self.setAttribute(Qt.WA_DeleteOnClose) #noqa
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

		self.fontsize = '14px'
		self.fontsize_small = '12px'

		for p in ['device', 'defaultKit', 'defaultControls']:
			if p in params:
				setattr(self, p, params[p])
		self.io = PadIO(self.device)
		try: 
			self.io.receivedMidi.disconnect(self.receivedMidi)
		except:
			pass
		self.io.receivedMidi.connect(self.receivedMidi)
		self.midiname = self.device['midiname']
		if 'nb_programs' in self.device:
			self.nbPrograms = int(self.device['nb_programs'])
		else:
			self.nbPrograms = 0

		self._program = self.io.program

		self.setStyleSheet('''
FreepadWindow * {
	color: ''' + FREEPAD_TITLE_COLOR + ''';
	font-size: ''' + self.fontsize + ''';
}
FreepadWindow, #statusbar, Pad #padLW {
	background: ''' + FREEPAD_LGRADIENT + ''';
}
#cbName, Program #bTitle, #statusbar {
	font-size: ''' + self.fontsize_small + '''; color: ''' + FREEPAD_TITLE_COLOR + ''';
}
QComboBox:focus, QComboBox:hover {
	border: 1px inset ''' + FREEPAD_BORD_COLOR + ''';
	selection-color: #000022;
	selection-background-color: #8f2200;
}
QComboBox {
	border: 1px outset #111111;
	border-radius: 3px;
	background: transparent;
}
QComboBox QListView {
	border: 1px solid ''' + FREEPAD_BORD_COLOR + ''';
	border-radius: 3px;
	border-top-left-radius: 0;
}
QComboBox QListView QScrollBar:vertical {
	background: ''' + FREEPAD_LGRADIENT + ''';
}
QComboBox QListView QScrollBar::up-arrow {
	image: url("''' + imgUrl('spinup.png') + '''");
}
QComboBox QListView QScrollBar::down-arrow {
	image: url("''' + imgUrl('spindown.png') + '''");
}
QComboBox::drop-down {
	subcontrol-origin: border;
	subcontrol-position: center right;
	border: none;
}
QComboBox::down-arrow {
	width: 7px; height: 7px;
	image: url("''' + imgUrl('spindown.png') + '''");
}
QComboBox::down-arrow:hover {
	image: url("''' + imgUrl('spindown_hover.png') + '''");
}
QComboBox QListView {
	selection-background-color: #8f2200; selection-color: #000022;
}
Pad #btnNote, #statusbar {
	font-size: ''' + self.fontsize_small + '''; color: ''' + FREEPAD_NOTE_COLOR + ''';
}
QPushButton, QComboBox, QComboBox QListView {
	background: ''' + FREEPAD_RGRADIENT + ''';
}
QPushButton:hover {
background: ''' + FREEPAD_RGRADIENT_OVER + '''; color: #8fffdf;
}
QPushButton {
	border: 2px outset #171719; padding: 5px; padding-left: 15px; padding-right: 15px;
}
QPushButton::pressed {
	border: 2px inset #171719; background: ''' + FREEPAD_LGRADIENT + ''';
}
QPushButton::disabled {
color: #666666;
}
QToolTip { 
	background: ''' + FREEPAD_LGRADIENT + '''; 
	color: white; 
	border: 1px solid ''' + FREEPAD_BORD_COLOR + ''';
	border-radius: 3px;
	border-top-left-radius: 0;
	padding: 3px;
	}
''')
		self.in_symbol = '<span style="color:#882200">-\u25B6</span>'
		self.out_symbol = '<span style="color:#882200">\u25C0-</span>'

		self.settingProgram = False
		self.padNotes = []
		self.padProgramChanges = []
		self.padControlChanges = []
		self.programs = []
		self._controls = {} # controls from varnames
		self.padKeymap = {}
		self.nbPrograms = 0
		self.pmc = 16 # default pad midi channel
		self.kmc = 16 # default knob midi channel
		self.setupUi()
		if self.io.isConnected:
			self.getProgram('1')
		else:
			self.load1stPreset()

	def setupUi(self):
		self.showMidiMessages = True if str(Fsettings.get('showMidiMessages', 'True')) == 'True'  else False

		if 'pad' in self.device:
			if 'mc' in self.device['pad']:
				self.pmc = 0
		if 'knob' in self.device and 'mc' in self.device['knob']:
				self.kmc = 0
		if 'nb_programs' in self.device:
			self.nbPrograms = int(self.device['nb_programs'])

		# Main layout: hLayout + statusbar
		self.createObj(u'vLayout', QVBoxLayout(self))
		self.vLayout.setContentsMargins(0, 0, 0, 0)
		self.vLayout.setSpacing(0)

		self.createObj(u'hLayout', QHBoxLayout())
		self.hLayout.setContentsMargins(10, 10, 10, 10)
		self.hLayout.setSpacing(10)

		if self.nbPrograms > 0:
			self.createObj(u'vLayoutg', QVBoxLayout())
			self.vLayoutg.setContentsMargins(0, 0, 0, 0)
			self.vLayoutg.setSpacing(10)
			for pg in range(1, int(self.device['nb_programs'] + 1)):
				pgt = str(pg)
				pglayout = Creator.createObj(self.vLayoutg, 'pgl' + pgt, QHBoxLayout())
				self.programs.append(Creator.createObj(self.vLayoutg, 'pid' + pgt, Program(pgt)))
				pgui = self.programs[pg - 1]
				pgui.setupUi()
				pgui.setEnabled(self.io.isConnected)
				pglayout.addWidget(pgui, alignment = Qt.AlignmentFlag.AlignCenter)
				self.vLayoutg.addLayout(pglayout)
				self._controls['pid' + str(pg)] = pgui

			self.createObj(u'hlToRam', QHBoxLayout())
			self.createObj(u'btnToRam', QPushButton())
			self.btnToRam.setStyleSheet('QPushButton{padding: 5px 20px 5px 20px;}')
			self.btnToRam.setEnabled(self.io.isConnected)
			hlspacerg = QSpacerItem(5, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
			hlspacerd = QSpacerItem(5, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
			self.hlToRam.addItem(hlspacerg)
			self.hlToRam.addWidget(self.btnToRam)
			self.hlToRam.addItem(hlspacerd)
			self.vLayoutg.addLayout(self.hlToRam)
			self.btnToRam.clicked.connect(self.sendToRam)

			self.addAppButtons(self.vLayoutg)
			self.hLayout.addLayout(self.vLayoutg)

		self.createObj(u'vLayoutd', QVBoxLayout())
		self.vLayoutd.setContentsMargins(0, 0, 0, 0)
		self.createObj(u'gLayout', QGridLayout())
		self.vLayoutd.addLayout(self.gLayout)
		self.gLayout.setContentsMargins(0, 0, 0, 0)
		self.gLayout.setSpacing(10)
		l = 0
		for line in self.device['layout']:
			c = 0
			for ctl in line:
				if ctl != '':
					ctlType = ctl.rstrip('0123456789')
					ctlNum = ctl[len(ctlType):]
					if ctlType == 'p':
						ctlClass = Pad(ctlNum)
						params = {'kit': self.defaultKit, \
							'bv': 'bv' in self.device['pad'], \
							'rgb': 'on_red1' in self.device['pad'],
							'mc': self.pmc
						}
						ctlClass.sendNoteOn.connect(self._sendNoteOn)
						ctlClass.sendNoteOff.connect(self._sendNoteOff)
						ctlClass.keyChanged.connect(self._padKeyChanged)
					elif ctlType == 'k':
						ctlClass = Knob(ctlNum)
						ctlClass.sendControlChanged.connect(self._sendControlChanged)
						params = {'midi_controls': self.defaultControls, \
							'mc': self.kmc
						}
					control = self.createObj(ctl, ctlClass)
					subcontrols = control.setupUi(params)
					self.gLayout.addWidget(control, l, c, 1, 1, alignment = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
					self._controls[ctl] = control
					self._controls.update(subcontrols)
				c = c + 1
			l = l + 1

		self.createObj(u'hLayoutBottom', QHBoxLayout())
		self.hLayoutBottom.setContentsMargins(0, 0, 0, 0)
		self.hLayoutBottom.setSpacing(10)
		self.createObj(u'labelMC', QLabel())
		self.hLayoutBottom.addWidget(self.labelMC)
		self.createObj(u'mc', QComboBox())
		self.mc.setMinimumWidth(60)
		self.mc.setEditable(True)
		self.mc.lineEdit().setReadOnly(True)
		self.mc.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
		for ch in range(1,17):
			sp = '  ' if ch < 10 else ''
			self.mc.addItem(sp + str(ch))
		self.hLayoutBottom.addWidget(self.mc)
		self._controls['mc'] = self.mc

		self.lblAlert = QLabel()
		self.lblAlert.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.lblAlert.setStyleSheet('color: #ff2800;')
		self.hLayoutBottom.addWidget(self.lblAlert)
		self.hLayoutBottom.setStretch(2,1)
		if self.nbPrograms == 0:
			self.addAppButtons(self.hLayoutBottom)

		self.vLayoutd.addLayout(self.hLayoutBottom)
		self.hLayout.addLayout(self.vLayoutd)
		self.vLayout.addLayout(self.hLayout)
		# status bar
		if self.showMidiMessages:
			self.addStatusBar()

		self.retranslateUi()
		self.setFixedSize(self.sizeHint())

		self.mc.currentIndexChanged.connect(self.valueChanged)

		QMetaObject.connectSlotsByName(self)

		# Start a MidiConnectionListener in the background
		self.mlcThread = QThread(self)
		self.mlc = MidiConnectionListener(self.io)
		self.mlc.moveToThread(self.mlcThread)
		self.mlcThread.started.connect(self.mlc.run)
		self.mlcThread.finished.connect(self.mlc.cancel)
		self.mlc.devicePlugged.connect(self.plugged)
		self.mlc.deviceUnplugged.connect(self.unplugged)
		self.mlcThread.start()

	def addStatusBar(self):
		self.createObj(u'statusbar', QLabel())
		self.vLayout.addWidget(self.statusbar)
		self.showMidiMessages = True

	def removeStatusBar(self):
		self.showMidiMessages = False
		self.vLayout.removeWidget(self.statusbar)

	def addAppButtons(self, layout):
		self.createObj(u'tbLayout', QHBoxLayout())
		self.createObj(u'btnLoad', QPushButton())
		self.btnLoad.setEnabled(False)
		self.btnLoad.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_DialogOpenButton')))
		self.createObj(u'btnSave', QPushButton())
		self.btnSave.setEnabled(False)
		self.btnSave.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_DialogSaveButton')))
		self.createObj(u'btnOptions', QPushButton())
		self.btnOptions.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MessageBoxInformation')))
		tblspacerg = QSpacerItem(5, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		tblspacerd = QSpacerItem(5, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.tbLayout.addItem(tblspacerg)
		self.tbLayout.addWidget(self.btnLoad)
		self.tbLayout.addWidget(self.btnSave)
		self.tbLayout.addWidget(self.btnOptions)
		self.tbLayout.addItem(tblspacerd)
		if 'program' in self.device:
			self.btnLoad.clicked.connect(self.loadProgram)
			self.btnSave.clicked.connect(self.saveProgram)
			self.btnLoad.setEnabled(True)
			self.btnSave.setEnabled(True)
		self.btnOptions.clicked.connect(self.showOptionsDialog)
		layout.addLayout(self.tbLayout)

	def _fileDialog(self, fileMode, acceptMode):
		filename = ''
		dialog = QFileDialog(self)
		dialog.setFileMode(fileMode)
		dialog.setAcceptMode(acceptMode)
		dialog.setNameFilter(self.midiname + ' program(*.' + self.midiname.lower() + ')')
		wDir = Fsettings.get('lastDir', os.getenv('HOME'))
		dialog.setDirectory(QDir(wDir))
		if dialog.exec():
			filenames = dialog.selectedFiles()
			if len(filenames) > 0:
				filename = dialog.selectedFiles()[0]
				lastdir = dialog.directory().absolutePath()
				Fsettings.set('lastDir', lastdir)
		return filename

	def load1stPreset(self):
		presets_path = FREEPAD_PATH.joinpath('pads').joinpath('presets').joinpath(self.midiname.lower())
		if presets_path.is_dir():
			presets_files = os.listdir(presets_path)
			if len(presets_files) > 0:
				pp = presets_path.joinpath(presets_files[0])
				self._loadProgram(pp)

	def loadProgram(self, event):
		filename = ''
		try:
			filename = self._fileDialog(QFileDialog.ExistingFile, QFileDialog.AcceptOpen)
			if filename != '':
				QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
				self._loadProgram(filename)
				QApplication.restoreOverrideCursor()

		except Exception as e:
			Debug.dbg('Unable to read ' + self.midiname + ' program from "' + filename + '": ' + str(e))

	def _loadProgram(self, filename):
		with open(filename, 'r') as fp:
			lst = json.load(fp)
			fp.close()
			pgm = [0] + lst[0]
			for pk in lst[1]:
				ctlname = pk[0]
				pkName = pk[1]
				ctl = self._controls[ctlname]
				ctl.cbName.lineEdit().setText(pkName)
				if isinstance(ctl, Pad) and len(pk) > 2:
					key = pk[2]
					ctl.leKey.setText(key)
					self.padKeymap[ctl.pad_id] = key
					if len(pk) > 3:
						ctl.level.setDefaultVelocity(pk[3])
				elif isinstance(ctl, Knob) and len(pk) > 2:
					ctl.pot.setValue(pk[2])
			self.setProgram(pgm)
			self.unselPrograms()
			# switch all lights off
			for line in  self.device['layout']:
				for ctlid in line:
					if ctlid[0:1] == 'p':
						self._controls[ctlid].lightOff()
			self.setFocus() # to activate keyboard keys
			if self.io.isConnected:
				self.sendToRam()

	def saveProgram(self, event):
		try:
			filename = self._fileDialog(QFileDialog.AnyFile, QFileDialog.AcceptSave)
			if filename != '':
				with open(filename, 'w') as fp:
					pgm = self.program()
					json.dump([pgm[1:], self._ctlVars()], fp)
					fp.close()
		except Exception as e:
			Debug.dbg('Unable to save ' + self.midiname + ' program in "' + filename + '": ' + str(e))

	# return control names and keyboard keys
	def _ctlVars(self):
		pkn = []
		for line in self.device['layout']:
			for control in line:
				ctl = self._controls[control]
				if isinstance(ctl, Pad):
					pkn.append([control, ctl.cbName.lineEdit().text(), ctl.leKey.text(), ctl.level.defaultVelocity])
				else:
					pkn.append([control, ctl.cbName.lineEdit().text(), ctl.pot.value()])
		return pkn

	# slot called when receiving a midi message
	def receivedMidi(self, msg):
		m = msg.split(' ')
		mtype = m[0]
		if mtype == 'note_on':
			self._midiNoteOn(m[1][8:], m[2][5:], m[3])
		elif mtype == 'note_off':
			self._midiNoteOff(m[1][8:], m[2][5:], m[3])
		elif mtype == 'control_change':
			self._midiControlChange(m[1][8:], m[2][8:], m[3][6:])
		elif mtype == 'program_change':
			self._midiProgramChange(m[1][8:], m[2][8:])
		elif mtype == 'sysex':
			self._midiSysex(m[1])
		else:
			self.warning('Received midi message of unknown type ' + mtype)
		if self.showMidiMessages:
			self.statusbar.setText(self.in_symbol + ' ' + msg[0:-7]) # without "time=0"

	def warning(self, msg, detail =''):
		self.lblAlert.setText(msg + '.')
		Debug.dbg(msg + detail)
		QTimer.singleShot(4000, lambda: self.lblAlert.setText(''))

	def _padFromNote(self, note):
		if not 'program' in self.io.pad:
			return 0
		if len(self.padNotes) == 0:
			for i in range(0, len(self._program)):
				ctlname = self._program[i]
				if (ctlname[0:1] == 'p') and (ctlname[-5:] == '_note'):
					val = self.getValue(ctlname)
					self.padNotes.append(str(val))
		if note in self.padNotes:
			index = self.padNotes.index(note) + 1
			if note in self.padNotes[index:]:
				self.warning('Cannot retrieve pad when a note is set twice or more', ': ' + str(self.padNotes))
			return index
		else:
			return 0

	def _padFromProgramChange(self, pc):
		if len(self.padProgramChanges) == 0:
			for i in range(0, len(self._program)):
				try:
					ctlname = self._program[i]
				except:
					raise PadException(ctlname + ' not found in program.')
				if (ctlname[0:1] == 'p') and (ctlname[-3:] == '_pc'):
					val = self.getValue(ctlname)
					self.padProgramChanges.append(str(val))
		if pc in self.padProgramChanges:
			index = self.padProgramChanges.index(pc) + 1
			if pc in self.padProgramChanges[index:]:
				self.warning('Cannot retrieve pad when a program change is set twice or more', ': ' + str(self.padNotes))
			return index
		else:
			return 0

	def _kFromControlChange(self, cc):
		if len(self.padControlChanges) == 0:
			for i in range(0, len(self._program)):
				try:
					ctlname = self._program[i]
				except:
					raise PadException(ctlname + ' not found in program.')
				if (ctlname[0:1] == 'k') and (ctlname[-3:] == '_cc'):
					val = self.getValue(ctlname)
					self.padControlChanges.append(str(val))
		if cc in self.padControlChanges:
			index = self.padControlChanges.index(cc) + 1
			if cc in self.padControlChanges[index:]:
				self.warning('Cannot retrieve knob when a control change is set twice or more', ': ' + str(self.padControlChanges))
			return index
		return 0

	def _midiNoteOn(self, channel, note, velocity):
		padnum = self._padFromNote(note)
		if padnum > 0:
			pad = self.findChildren(QWidget, 'p' + str(padnum))
			if len(pad) > 0:
				pad[0].lightOn(velocity[9:])
		else:
			self.warning('Cannot retrieve pad from note ' + str(note), ' in ' + str(self.padNotes))

	def _midiNoteOff(self, channel, note, velocity):
		padnum = self._padFromNote(note)
		if padnum > 0:
			pad = self.findChildren(QWidget, 'p' + str(padnum))
			if len(pad) > 0:
				pad[0].lightOff()

	def _midiControlChange(self, channel, control, value):
		knum = self._kFromControlChange(control)
		if knum > 0:
			k = self.findChildren(QWidget, 'k' + str(knum))
			if len(k) > 0:
				k[0].setValue(value)
		else:
			self.warning('Cannot retrieve knob with control changes ' + str(self.padControlChanges), ' for CC ' + str(control))

	def _midiProgramChange(self, channel, program):
		padnum = self._padFromProgramChange(program)
		if padnum > 0:
			pad = self.findChildren(QWidget, 'p' + str(padnum))
			if len(pad) > 0:
				pad[0].lightOn(0)
				QTimer.singleShot(200, lambda: pad[0].lightOff())
		else:
			self.warning('Cannot retrieve pad from program change with program' + str(self.padProgramChanges))

	def _midiSysex(self, data):
		data = data[6: -1].split(',')
		Debug.dbg('Received ' + str(data))
		self.setProgram(data[len(self.io.pad['get_program'].split(',')) - 1:])

	# Set an UI value.
	def setValueOld(self, varname, value):
		try: 
			if varname == 'pid':
				if value != 0: # value is zero when loading a program file
					self._controls[varname + str(value)].select()
			elif '_' in varname and varname[varname.rindex('_') - len(varname) + 1:] in ['red1', 'red2', 'green1', 'green2', 'blue1', 'blue2']:
				color = varname[varname.rindex('_') - len(varname) + 1:]
				padid = varname[0:varname.index('_')]
				onoff = varname[varname.index('_') + 1:varname.rindex('_')]
				pad = self._controls[padid]
				setattr(pad, onoff + '_' + color, value)
				pad.lightOff()
			else:
				ctl = self.findChildren(QWidget, varname)
				if len(ctl) > 0:
					ctl = ctl[0]
					if isinstance(ctl, QSpinBox):
						ctl.setValue(int(value))
					elif isinstance(ctl, QComboBox):
						ctl.setCurrentIndex(int(value))
				else:
					Debug.dbg('setValue: ' + varname + ' not found in ' + str(self))
		except Exception as e:
			Debug.dbg('Unable to set ' + varname + ' = ' + str(value) + ' ' + str(e))

	# Set an UI value.
	def setValue(self, varname, value):
		try: 
			if varname == 'pid':
				if value != 0: # value is zero when loading a program file
					self._controls[varname + str(value)].select()
			else:
				ctl = self._controls[varname]
				if isinstance(ctl, QSpinBox):
					ctl.setValue(int(value))
				elif isinstance(ctl, QComboBox):
					ctl.setCurrentIndex(int(value))
				elif isinstance(ctl, Pad):
					v = varname[len(ctl.pad_id) + 2:]
					setattr(ctl, v, value)
				else:
					Debug.dbg('setValue: ' + varname + ' not found in ' + str(self))
		except Exception as e:
			Debug.dbg('Unable to set ' + varname + ' = ' + str(value) + ': ' + str(e))

	def getValue(self, varname):
		if varname not in  self._controls:
			return None
		ctl = self._controls[varname]
		if isinstance(ctl, QSpinBox):
			val = ctl.value()
		elif isinstance(ctl, QComboBox):
			val = ctl.currentIndex()
		elif isinstance(ctl, Pad):
			val = getattr(ctl, varname[len(ctl.pad_id) + 2:])
		return val

	def closeEvent(self, event):
		self.io.close()
		self.io.deleteLater()
		self.mlcThread.quit()
		event.accept()

	def program(self):
		pgm = []
		for i in range(0, len(self._program)):
			varname = self._program[i]
			val = self.getValue(varname)
			pgm.append(val)
		return(pgm)

	def sendToRam(self):
		if self.io.isConnected:
			self.io.sendProgram(0, self.program())
			self.unselPrograms()

	def sendProgram(self, pid):
		if self.io.isConnected:
			msg = self.io.sendProgram(pid, self.program())
			self.statusbar.setText(self.out_symbol + ' ' + msg)

	def setProgram(self, pgm):
		if 'program' not in self.io.pad:
			raise PadException('"program" not found in JSON file.')
		if len(pgm) != len(self._program):
			raise PadException('received a program with a different size than expected according to JSON file.')

		self.settingProgram = True
		self.unselPrograms()
		for i in range(0, len(self._program)):
			try:
				varname = self._program[i]
				self.setValue(varname, int(pgm[i]))
			except Exception as e:
				raise PadException(varname + ' not found in program: ' + str(e))
		self.settingProgram = False


	def getProgram(self, pid):
		if self.io.isConnected:
			self.unselPrograms()
			self.io.getProgram(pid)

	def unselPrograms(self):
		if not self.settingProgram:
			for p in range(1, self.nbPrograms + 1):
				pgm = self.findChildren(QWidget, 'pid' + str(p))
				if len(pgm) > 0:
					pgm[0].unsel()
			self.padNotes = [] # reinit
			self.padProgramChanges = []
			self.padControlChanges = []

	def plugged(self):
		self.setEnabled(True)
		self.retranslateUi()
		self.getProgram('1') # LPD8 switch to program 4 when disconnected/connected again

		_DSARW = 'dontShowAgainReconnectionWarning'
		if not Fsettings.get(_DSARW, False):
			devname = self.device['midiname']
			msg = u'Do not forget to connect again your ' + devname + '\nto the Midi Through port or to something else.'
			mb = QMessageBox(QMessageBox.Warning, 'Freepad', msg)
			cb = QCheckBox("Don't show this again")
			mb.setCheckBox(cb)
			mb.exec()
			if cb.checkState() == 2:
				Fsettings.set(_DSARW, True)

	def unplugged(self):
		self.retranslateUi()
		self.setEnabled(False)

	def setEnabled(self, enabled : bool):
		for pg in self.programs:
			pg.setEnabled(enabled)
		self.btnToRam.setEnabled(enabled)

	def showOptionsDialog(self, event):
		dialog = FreepadOptionsWindow(self)
		dialog.setupUi(self.midiname)
		dialog.exec()

	def _sendNoteOn(self, mc, note, velocity):
		if mc == 16:
			mc = self.mc.currentIndex()
		msg = self.io.sendNoteOn(mc, note, velocity)
		if self.showMidiMessages and msg is not None:
			self.statusbar.setText(self.out_symbol + ' ' + msg)

	def _sendNoteOff(self, mc, note, velocity):
		if mc == 16:
			mc = self.mc.currentIndex()
		msg = self.io.sendNoteOff(mc, note, velocity)
		if self.showMidiMessages and msg is not None:
			self.statusbar.setText(self.out_symbol + ' ' + msg)

	def _sendControlChanged(self, mc, cc, val):
		if mc == 16:
			mc = self.mc.currentIndex()
		msg = self.io.sendControlChanged(mc, cc, val)
		if self.showMidiMessages and msg is not None:
			self.statusbar.setText(self.out_symbol + ' ' + msg)

	def valueChanged(self, value):
		self.unselPrograms()

	def _padKeyChanged(self, pad_id, key):
		self.padKeymap[pad_id] = key.lower()

	def retranslateUi(self):
		virtual = '' if self.io.isConnected else 'virtual '
		self.setWindowTitle(tr(u'Freepad ' + virtual + self.midiname, None))
		if self.nbPrograms > 0:
			self.btnToRam.setText(tr(u'Send to RAM', None))
		self.labelMC.setText(tr(u'Midi channel', None))

	def keyPressEvent(self, event):
		self._keyEvent(event, '_sendNoteOn')

	def keyReleaseEvent(self, event):
		self._keyEvent(event, '_sendNoteOff')

	def _keyEvent(self, event, callback):
		if isinstance(event, QKeyEvent) and not event.isAutoRepeat() and self.hasFocus():
			key = event.text().lower()
			if key in self.padKeymap.values():
				for pad_id in [pad_id for pad_id, k in self.padKeymap.items() if k == key]:
					pads = self.findChildren(QWidget, 'p' + pad_id)
					if len(pads) > 0:
							getattr(pads[0], callback)()
