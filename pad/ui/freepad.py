import os, json

from qtpy.QtCore import QCoreApplication, QDir, QMetaObject, Qt, QTimer
from qtpy.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QGridLayout, \
	QHBoxLayout, QLabel, QLayout, QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QStatusBar, QSpinBox, \
	QStyle, QVBoxLayout, QWidget
from qtpy.QtGui import QIcon, QKeyEvent

from pad.path import FREEPAD_PATH, FREEPAD_ICON_PATH
from pad.ui.common import Creator, PadException
from pad.ui.controls import Knob, Pad, Program
from pad.ui.options import FreepadOptionsWindow
from pad.padio import PadIO

class FreepadWindow(QWidget, Creator):
	def __init__(self, params):
		super().__init__()
		self.setWindowIcon(QIcon(FREEPAD_ICON_PATH))
		self.setAttribute(Qt.WA_DeleteOnClose) #noqa
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		for p in ['device', 'in_name', 'defaultKit', 'defaultControls', 'settings', 'debug']:
			if p in params:
				setattr(self, p, params[p])
		self.io = PadIO(self.device, self.in_name)
		try: 
			self.io.receivedMidi.disconnect(self.receivedMidi)
		except:
			pass
		self.io.receivedMidi.connect(self.receivedMidi)
		self.midiname = self.device["midiname"]
		if 'nb_programs' in self.device:
			self.nbPrograms = int(self.device["nb_programs"])
		else:
			self.nbPrograms = 0

		self._program = self.io.program

		self.titleColor = "#dfdddd"
		self.noteColor = "#cfffff"
		self.lgradient = "qlineargradient(spread:reflect, x1:1, y1:0.5, x2:1, y2:1, stop:0 #171719, stop:1 #080808);"
		self.rgradient = "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 #080808, stop:1 #171719)"
		self.rgradient_over = "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 #280808, stop:1 #171719)"

		self.setStyleSheet("FreepadWindow * {"
"color: white;"
"}"
"FreepadWindow, QStatusBar, Pad #padLW {"
"background: " + self.lgradient + ";"
"}"
"#cbName, Program #bTitle, QStatusBar {"
"font-size: 12px; color: " + self.titleColor + ";"
"}"
"QComboBox:focus, QComboBox:hover {"
"border: 1px inset #441200; selection-color: #000022; selection-background-color: #8f2200"
"}"
"QComboBox {"
"border: 1px outset #111111; border-radius: 3px; background: transparent;"
"}"
"QComboBox QListView {"
"border: 1px solid #8f2200; border-radius: 3px; border-top-left-radius: 0;"
"}"
"QComboBox::drop-down {"
"width: 12px; height: 12px;"
"subcontrol-origin: border;"
"subcontrol-position: center right;"
"}"
"QComboBox::down-arrow {"
"background: none; border: none;"
"image: url(pad/ui/img/spindown.png);"
"}"
"QComboBox::down-arrow:hover {"
"image: url(pad/ui/img/spindown_hover.png);"
"}"
"Pad #btnNote, QStatusBar {"
"font-size: 12px; color: " + self.noteColor + ";"
"}"
"QComboBox QAbstractItemView {"
"selection-background-color: #8f2200; selection-color: #000022;"
"}"
"QPushButton, QComboBox, QComboBox QListView {"
"background: " + self.rgradient + ";"
"}"
"QPushButton:hover {"
"background: " + self.rgradient_over + "; color: #8fffdf;"
"}"
"QPushButton {"
"border: 2px outset #171719; padding: 5px; padding-left: 15px; padding-right: 15px;"
"}"
"QPushButton::pressed {"
"border: 2px inset #171719; background: " + self.lgradient + ";"
"}"
"QPushButton::disabled {"
"color: #666666;"
"}"
)
		self.in_symbol = '\u25B6'
		self.out_symbol = '\u25C0'

		self.showMidiMessages = True if str(self.settings.value('showMidiMessages', "True")) == "True"  else False
		self.settingProgram = False
		self.padNotes = []
		self.padProgramChanges = []
		self.padControlChanges = []
		self.programs = []
		self.padKeymap = {}
		self.nbPrograms = 0
		self.pmc = 16
		self.kmc = 16
		self.setupUi()
		self.setFixedSize(self.sizeHint())
		if self.io.isConnected:
			self.getProgram("1")
		else:
			self.load1stPreset()

	def setupUi(self):
		if 'pad' in self.device:
			if 'mc' in self.device['pad']:
				self.pmc = 0
		if 'knob' in self.device and 'mc' in self.device['knob']:
				self.kmc = 0
		if 'nb_programs' in self.device:
			self.nbPrograms = int(self.device['nb_programs'])

		# Main layout
		self.createObj(u"vLayout", QVBoxLayout(self))
		self.vLayout.setContentsMargins(0, 0, 0, 0)

		self.createObj(u"hLayout", QHBoxLayout())
		self.hLayout.setContentsMargins(10, 10, 0, 0) # this 10 is top-margin
		self.hLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)

		if self.nbPrograms > 0:
			self.createObj(u"vLayoutg", QVBoxLayout())
			self.vLayoutg.setContentsMargins(0, 0, 0, 0)
			for pg in range(1, int(self.device["nb_programs"] + 1)):
				pgt = str(pg)
				pglayout = Creator.createObj(self.vLayoutg, "pgl" + pgt, QHBoxLayout())
				self.programs.append(Creator.createObj(self.vLayoutg, "pid" + pgt, Program(pgt)))
				pgui = self.programs[pg - 1]
				pgui.setupUi()
				pgui.setEnabled(self.io.isConnected)
				pglayout.addWidget(pgui, alignment = Qt.AlignmentFlag.AlignCenter)
				self.vLayoutg.addLayout(pglayout)
				self.vSpacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
				self.vLayoutg.addItem(self.vSpacer)

			self.createObj(u"hlToRam", QHBoxLayout())
			self.createObj(u"btnToRam", QPushButton())
			self.btnToRam.setStyleSheet("QPushButton{padding: 5px 20px 5px 20px;}")
			self.btnToRam.setEnabled(self.io.isConnected)
			hlspacerg = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
			hlspacerd = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
			self.hlToRam.addItem(hlspacerg)
			self.hlToRam.addWidget(self.btnToRam)
			self.hlToRam.addItem(hlspacerd)
			self.vLayoutg.addLayout(self.hlToRam)
			self.btnToRam.clicked.connect(self.sendToRam)

			self.verticalSpacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
			self.vLayoutg.addItem(self.verticalSpacer)
			self.addAppButtons(self.vLayoutg)
			self.verticalSpacer2 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
			self.vLayoutg.addItem(self.verticalSpacer2)
			self.hLayout.addLayout(self.vLayoutg)

		self.createObj(u"gLayoutd", QGridLayout())
		self.gLayoutd.setHorizontalSpacing(10)
		self.gLayoutd.setVerticalSpacing(0)
		l = 0
		for line in self.device['layout']:
			l = l + 1
			c = 0
			for ctl in line:
				ctlType = ctl.rstrip("0123456789")
				ctlNum = ctl[len(ctlType):]
				if ctlType == 'p':
					ctlClass = Pad(ctlNum, self.settings)
					params = {'kit': self.defaultKit, \
									'bv': 'bv' in self.device['pad'], \
									'rgb': 'on_red' in self.device['pad'],
									'mc': self.pmc,
									'lgradient': self.rgradient,
									'rgradient': self.rgradient
									}
					ctlClass.sendNoteOn.connect(self._sendNoteOn)
					ctlClass.sendNoteOff.connect(self._sendNoteOff)
					ctlClass.keyChanged.connect(self._padKeyChanged)
				elif ctlType == 'k':
					ctlClass = Knob(ctlNum)
					ctlClass.sendControlChanged.connect(self._sendControlChanged)
					params = {'controls': self.defaultControls, \
									'mc': self.kmc}
				control = self.createObj(ctl, ctlClass)
				control.setupUi(params)
				self.gLayoutd.addWidget(control, l, c, alignment = Qt.AlignmentFlag.AlignCenter)
				c = c + 1
			l = l + 1

		self.createObj(u"hLayoutMC", QHBoxLayout())
		self.hLayoutMC.setContentsMargins(0, 0, 0, 0)
		self.hLayoutMC.setSpacing(10)

		self.createObj(u"labelMC", QLabel())
		self.hLayoutMC.addWidget(self.labelMC)

		self.createObj(u"mc", QComboBox())
		self.mc.setMinimumWidth(60)
		for ch in range(1,17):
			sp = "  " if ch < 10 else ""
			self.mc.addItem(sp + str(ch))
		self.hLayoutMC.addWidget(self.mc)
		self.lblAlert = QLabel()
		self.lblAlert.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.lblAlert.setStyleSheet("color: #ff2800;")
		self.hLayoutMC.addWidget(self.lblAlert)
		self.hLayoutMC.setStretch(2,1)
		if self.nbPrograms == 0:
			self.addAppButtons(self.hLayoutMC)

		self.gLayoutd.addLayout(self.hLayoutMC, l + 1, 0, 1, c)
		self.hLayout.addLayout(self.gLayoutd)
		self.vLayout.addLayout(self.hLayout)
		# Margin bottom before status bar
		self.vLayout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

		if self.showMidiMessages:
			self.createObj(u"statusbar", QStatusBar())
			self.vLayout.addWidget(self.statusbar)

		self.retranslateUi()

		self.mc.currentIndexChanged.connect(self.valueChanged)

		QMetaObject.connectSlotsByName(self)

	def addAppButtons(self, layout):
		self.createObj(u"tbLayout", QHBoxLayout())
		self.createObj(u"btnLoad", QPushButton())
		self.btnLoad.setEnabled(False)
		self.btnLoad.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DialogOpenButton")))
		self.createObj(u"btnSave", QPushButton())
		self.btnSave.setEnabled(False)
		self.btnSave.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DialogSaveButton")))
		self.createObj(u"btnOptions", QPushButton())
		self.btnOptions.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_MessageBoxInformation")))
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

	def _ctlFromId(self, ctl):
		ctlType = ctl.rstrip('0123456789')
		if ctlType == 'p':
			c = Pad
		elif ctlType == 'k':
			c = Knob
		c = self.findChildren(c, ctl)
		if len(c) >0:
			return c[0]
		return False

	def _fileDialog(self, fileMode, acceptMode):
		filename = ''
		dialog = QFileDialog(self)
		dialog.setFileMode(fileMode)
		dialog.setAcceptMode(acceptMode)
		dialog.setNameFilter(self.midiname + ' program(*.' + self.midiname.lower() + ')')
		wDir = self.settings.value('Freepad/lastDir', os.getenv('HOME'))
		dialog.setDirectory(QDir(wDir))
		if dialog.exec():
			filenames = dialog.selectedFiles()
			if len(filenames) > 0:
				filename = dialog.selectedFiles()[0]
				lastdir = dialog.directory().absolutePath()
				self.settings.setValue('Freepad/lastDir', lastdir)
		return filename

	def load1stPreset(self):
		presets_path = FREEPAD_PATH.joinpath('pads').joinpath('presets').joinpath(self.midiname.lower())
		if presets_path.is_dir():
			presets_files = os.listdir(presets_path)
			if len(presets_files) > 0:
				pp = presets_path.joinpath(presets_files[0])
				self._loadProgram(pp)

	def loadProgram(self, event):
		filename = ""
		try:
			filename = self._fileDialog(QFileDialog.ExistingFile, QFileDialog.AcceptOpen)
			if filename != "":
				QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
				self._loadProgram(filename)
				QApplication.restoreOverrideCursor()

		except Exception as e:
			self.cprint('Unable to read ' + self.midiname + ' program from "' + filename + '": ' + str(e))

	def _loadProgram(self, filename):
		try:
			with open(filename, "r") as fp:
				lst = json.load(fp)
				fp.close()
				pgm = [0] + lst[0]
				for pk in lst[1]:
					ctlname = pk[0]
					pkName = pk[1]
					ctl = self._ctlFromId(ctlname)
					if ctl is not False:
						ctl.cbName.lineEdit().setText(pkName)
						if isinstance(ctl, Pad) and len(pk) > 2:
							key = pk[2]
							ctl.leKey.setText(key)
							self.padKeymap[ctl.pad_id] = key
							if len(pk) > 3:
								ctl.level.setDefaultVelocity(pk[3])
				self.setProgram(pgm)
				if self.io.isConnected:
					self.sendToRam()
				self.unselPrograms()
				self.setFocus() # to activate keyboard keys

		except Exception as e:
			self.cprint('Unable to read ' + self.midiname + ' program from "' + filename + '": ' + str(e))

	def saveProgram(self, event):
		try:
			filename = self._fileDialog(QFileDialog.AnyFile, QFileDialog.AcceptSave)
			if filename != "":
					with open(filename, "w") as fp:
						pgm = self.program()
						json.dump([pgm[1:], self._ctlVars()], fp)
						fp.close()
		except Exception as e:
			self.cprint('Unable to save ' + self.midiname + ' program in "' + filename + '": ' + str(e))

	# return control names and keyboard keys
	def _ctlVars(self):
		pkn = []
		for line in self.device['layout']:
			for control in line:
				ctl = self._ctlFromId(control)
				if ctl is not False:
					if isinstance(ctl, Pad):
						pkn.append([control, ctl.cbName.lineEdit().text(), ctl.leKey.text(), ctl.level.defaultVelocity])
					else:
						pkn.append([control, ctl.cbName.lineEdit().text()])
		return pkn



	def receivedMidi(self, msg):
		m = msg.split(" ")
		mtype = m[0]
		if mtype == "note_on":
			self._midiNoteOn(m[1][8:], m[2][5:], m[3])
		elif mtype == "note_off":
			self._midiNoteOff(m[1][8:], m[2][5:], m[3])
		elif mtype == "control_change":
			self._midiControlChange(m[1][8:], m[2][8:], m[3][6:])
		elif mtype == "program_change":
			self._midiProgramChange(m[1][8:], m[2][8:])
		elif mtype == "sysex":
			self._midiSysex(m[1])
		else:
			self.warning("Received midi message of unknown type " + mtype)
		if self.showMidiMessages:
			self.statusbar.showMessage(self.in_symbol + ' ' + msg[0:-7]) # without "time=0"

	def warning(self, msg, detail =''):
		self.lblAlert.setText(msg + '.')
		self.cprint(msg + detail)
		QTimer.singleShot(4000, lambda: self.lblAlert.setText(''))

	def cprint(self, msg):
		if self.debug:
			print(msg)

	def _padFromNote(self, note):
		if not 'program' in self.io.pad:
			return 0
		if len(self.padNotes) == 0:
			for i in range(0, len(self._program)):
				ctlname = self._program[i]
				if (ctlname[0:1] == "p") and (ctlname[-5:] == "_note"):
					val = self.getValue(ctlname)
					self.padNotes.append(str(val))
		if note in self.padNotes:
			index = self.padNotes.index(note) + 1
			if note in self.padNotes[index:]:
				self.warning("Cannot retrieve pad when a note is set twice or more", ': ' + str(self.padNotes))
			return index
		else:
			return 0

	def _padFromProgramChange(self, pc):
		if len(self.padProgramChanges) == 0:
			for i in range(0, len(self._program)):
				try:
					ctlname = self._program[i]
				except:
					raise PadException(ctlname + " not found in program.")
				if (ctlname[0:1] == "p") and (ctlname[-3:] == "_pc"):
					val = self.getValue(ctlname)
					self.padProgramChanges.append(str(val))
		if pc in self.padProgramChanges:
			index = self.padProgramChanges.index(pc) + 1
			if pc in self.padProgramChanges[index:]:
				self.warning("Cannot retrieve pad when a program change is set twice or more", ': ' + str(self.padNotes))
			return index
		else:
			return 0

	def _kFromControlChange(self, cc):
		if len(self.padControlChanges) == 0:
			for i in range(0, len(self._program)):
				try:
					ctlname = self._program[i]
				except:
					raise PadException(ctlname + " not found in program.")
				if (ctlname[0:1] == "k") and (ctlname[-3:] == "_cc"):
					val = self.getValue(ctlname)
					self.padControlChanges.append(str(val))
		if cc in self.padControlChanges:
			index = self.padControlChanges.index(cc) + 1
			if cc in self.padControlChanges[index:]:
				self.warning("Cannot retrieve knob when a control change is set twice or more", ': ' + str(self.padControlChanges))
			return index
		return 0

	def _midiNoteOn(self, channel, note, velocity):
		padnum = self._padFromNote(note)
		if padnum > 0:
			pad = self.findChildren(QWidget, "p" + str(padnum))
			if len(pad) > 0:
				pad[0].lightOn(velocity[9:])
		else:
			self.warning("Cannot retrieve pad from note " + str(note), " in " + str(self.padNotes))

	def _midiNoteOff(self, channel, note, velocity):
		padnum = self._padFromNote(note)
		if padnum > 0:
			pad = self.findChildren(QWidget, "p" + str(padnum))
			if len(pad) > 0:
				pad[0].lightOff()

	def _midiControlChange(self, channel, control, value):
		knum = self._kFromControlChange(control)
		if knum > 0:
			k = self.findChildren(QWidget, "k" + str(knum))
			if len(k) > 0:
				k[0].setValue(value)
		else:
			self.warning("Cannot retrieve knob with control changes " + str(self.padControlChanges), " for CC " + str(control))

	def _midiProgramChange(self, channel, program):
		padnum = self._padFromProgramChange(program)
		if padnum > 0:
			pad = self.findChildren(QWidget, "p" + str(padnum))
			if len(pad) > 0:
				pad[0].lightOn()
				QTimer.singleShot(200, lambda: pad[0].lightOff())
		else:
			self.warning("Cannot retrieve pad from program change with program" + str(self.padProgramChanges))

	def _midiSysex(self, data):
		data = data[6: -1].split(",")
		self.cprint('Received ' + str(data))
		self.setProgram(data[len(self.io.pad["get_program"].split(",")) - 1:])

	# Set an UI value.
	def setValue(self, ctlname, value):
		try: 
			if ctlname == "pid":
				if value != 0: # value is zero when loading a program file
					pgm = self.findChildren(QWidget, ctlname + str(value))
					pgm[0].select()
			elif '_' in ctlname and ctlname[ctlname.rindex('_') - len(ctlname) + 1:] in ['red', 'green', 'blue']:
				color = ctlname[ctlname.rindex('_') - len(ctlname) + 1:]
				padid = ctlname[0:ctlname.index('_')]
				onoff = ctlname[ctlname.index('_') + 1:ctlname.rindex('_')]
				pad = self.findChildren(QWidget, padid)
				if len(pad) > 0:
					setattr(pad[0], onoff + '_' + color, value)
					pad[0].lightOff()
			else:
				ctl = self.findChildren(QWidget, ctlname)
				if len(ctl) > 0:
					ctl = ctl[0]
					if isinstance(ctl, QSpinBox):
						ctl.setValue(int(value))
					elif isinstance(ctl, QComboBox):
						ctl.setCurrentIndex(int(value))
				else:
					print('setValue: ' + ctlname + ' not found in ' + str(self))
		except Exception as e:
			self.cprint("Unable to set " + ctlname +" = " + str(value) + ' ' + str(e))

	def getValue(self, ctlname):
		val = None
		if '_' in ctlname and ctlname[ctlname.rindex('_') - len(ctlname) + 1:] in ['red', 'green', 'blue']:
			color = ctlname[ctlname.rindex('_') - len(ctlname) + 1:]
			padid = ctlname[0:ctlname.index('_')]
			onoff = ctlname[ctlname.index('_') + 1:ctlname.rindex('_')]
			pad = self.findChildren(QWidget, padid)
			if len(pad) > 0:
				val = getattr(pad[0], onoff + '_' + color)
		else:
			ctl = self.findChildren(QWidget, ctlname)
			if len(ctl) > 0:
				ctl = ctl[0]
				if isinstance(ctl, QSpinBox):
					val = ctl.value()
				elif isinstance(ctl, QComboBox):
					val = ctl.currentIndex()
		return val

	def closeEvent(self, event):
		self.io.close()

	def program(self):
		pgm = []
		for i in range(0, len(self._program)):
			ctlname = self._program[i]
			val = self.getValue(ctlname)
			pgm.append(val)
		return(pgm)

	def sendToRam(self):
		if self.io.isConnected:
			self.io.sendProgram(0, self.program())
			self.unselPrograms()

	def sendProgram(self, pid):
		if self.io.isConnected:
			msg = self.io.sendProgram(pid, self.program())
			self.statusbar.showMessage(self.out_symbol + ' ' + msg)

	def setProgram(self, pgm):
		if "program" not in self.io.pad:
			raise PadException('"program" not found in JSON file')
		if len(pgm) != len(self._program):
			raise PadException("received a program with a different size than expected according to JSON file.")

		self.settingProgram = True
		self.unselPrograms()
		for i in range(0, len(self._program)):
			try:
				ctlname = self._program[i]
				self.setValue(ctlname, int(pgm[i]))
			except Exception as e:
				raise PadException(ctlname + " not found in program: " + str(e))
		self.settingProgram = False


	def getProgram(self, pid):
		if self.io.isConnected:
			self.unselPrograms()
			self.io.getProgram(pid)

	def unselPrograms(self):
		if not self.settingProgram:
			for p in range(1, self.nbPrograms + 1):
				pgm = self.findChildren(QWidget, "pid" + str(p))
				if len(pgm) > 0:
					pgm[0].unsel()
			self.padNotes = [] # reinit
			self.padProgramChanges = []
			self.padControlChanges = []

	def plugged(self, in_midiname, out_midiname):
		self.io.openDevicePorts(in_midiname, out_midiname)
		if self.io.isConnected:
			self.setEnabled(True)
			self.retranslateUi()
			self.getProgram('1') # LPD8 switch to program 4 when disconnected/connected again

		# self.settings.setValue('dontShowAgainReconnectionWarning', False) # used only for debug
		if not self.settings.value('dontShowAgainReconnectionWarning', False):
			devname = self.device['midiname']
			msg = u'Do not forget to connect again your ' + devname + '\nto the Midi Through port or to something else.'
			mb = QMessageBox(QMessageBox.Warning, 'Freepad', msg)
			cb = QCheckBox("Don't show this again")
			mb.setCheckBox(cb)
			mb.exec()
			if cb.checkState() == 2:
				self.settings.setValue('dontShowAgainReconnectionWarning', True)

	def unplugged(self):
		self.io.closeDevicePorts()
		self.retranslateUi()
		self.setEnabled(False)

	def setEnabled(self, enabled : bool):
		for pg in self.programs:
			pg.setEnabled(enabled)
		self.btnToRam.setEnabled(enabled)

	def showOptionsDialog(self, event):
		dialog = FreepadOptionsWindow(self.settings)
		dialog.setupUi(self.midiname)
		dialog.exec()

	def _sendNoteOn(self, mc, note, velocity):
		if mc == 16:
			mc = self.mc.currentIndex()
		msg = self.io.sendNoteOn(mc, note, velocity)
		if self.showMidiMessages and msg is not None:
			self.statusbar.showMessage(self.out_symbol + ' ' + msg)

	def _sendNoteOff(self, mc, note, velocity):
		if mc == 16:
			mc = self.mc.currentIndex()
		msg = self.io.sendNoteOff(mc, note, velocity)
		if self.showMidiMessages and msg is not None:
			self.statusbar.showMessage(self.out_symbol + ' ' + msg)

	def _sendControlChanged(self, mc, cc, val):
		if mc == 16:
			mc = self.mc.currentIndex()
		msg = self.io.sendControlChanged(mc, cc, val)
		if self.showMidiMessages and msg is not None:
			self.statusbar.showMessage(self.out_symbol + ' ' + msg)

	def valueChanged(self, value):
		self.unselPrograms()

	def _padKeyChanged(self, pad_id, key):
		self.padKeymap[pad_id] = key.lower()

	def retranslateUi(self):
		virtual = "" if self.io.isConnected else "virtual "
		self.setWindowTitle(QCoreApplication.translate("Pads", u"Freepad " + virtual + self.midiname, None))
		if self.nbPrograms > 0:
			self.btnToRam.setText(QCoreApplication.translate("Pads", u"Send to RAM", None))
		self.labelMC.setText(QCoreApplication.translate("Pads", u"Midi channel", None))

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
