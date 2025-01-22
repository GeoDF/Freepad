import os, json

from qtpy.QtCore import QCoreApplication, QDir, QMetaObject, Qt, QTimer
from qtpy.QtWidgets import QCheckBox, QComboBox, QFileDialog, QGridLayout, \
	QHBoxLayout, QLabel, QLayout, QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QStatusBar, QSpinBox, \
	QStyle, QVBoxLayout, QWidget
from qtpy.QtGui import QKeyEvent

from pad.path import FREEPAD_PATH
from pad.ui.common import Creator, PadException
from pad.ui.controls import Knob, Pad, Program
from pad.ui.options import FreepadOptionsWindow
from pad.padio import PadIO

class FreepadWindow(QWidget):
	def __init__(self, device, in_name, defaultKit, defaultControls, settings, parent = None):
		super().__init__(parent)
		self.settings = settings
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
		self.device = device
		self.io = PadIO(device, in_name)
		try: 
			self.io.receivedMidi.disconnect(self.receivedMidi)
		except:
			pass
		self.io.receivedMidi.connect(self.receivedMidi)
		self.midiname = device["midiname"]

		self.ui = Ui_Pads(settings, self)
		self.ui.setupUi(device, defaultKit, defaultControls)
		self.setFixedSize(self.sizeHint())
		self.titleColor = "#dfdddd"
		self.noteColor = "#cfffff"
		self.lgradient = "qlineargradient(spread:reflect, x1:1, y1:0.5, x2:1, y2:1, stop:0 #171719, stop:1 #080808);"
		rgradient = "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 #080808, stop:1 #171719)"
		rgradient_over = "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 #280808, stop:1 #171719)"

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
"background: " + rgradient + ";"
"}"
"QPushButton:hover {"
"background: " + rgradient_over + "; color: #8fffdf;"
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

		self.noteString = [
			["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
			[u"Do", u"Do#", u"Ré", u"Ré#", u"Mi", u"Fa", u"Fa#", u"Sol", u"Sol#", u"La", u"La#", u"Si",]
		]
		self.settingProgram = False
		self.padNotes = []
		self.padProgramChanges = []
		self.padControlChanges = []
		if self.io.isConnected:
			self.getProgram("1")
		else:
			self.load1stPreset()


	def _ctlFromId(self, ctl):
		sctl = str(ctl)
		ctlType = sctl.rstrip("0123456789")
		if ctlType == "p" or ctlType == "pad":
			c = Pad
		elif ctlType == "k" or ctlType == "knob":
			c = Knob
		c = self.findChildren(c, ctl)
		if len(c) >0:
			return c[0]
		return False


	def _fileDialog(self, fileMode, acceptMode):
		filename = ""
		dialog = QFileDialog(self)
		dialog.setFileMode(fileMode)
		dialog.setAcceptMode(acceptMode)
		dialog.setNameFilter(self.midiname + " program(*." + self.midiname.lower() + ")")
		wDir = self.settings.value('Freepad/lastDir', os.getenv("HOME"))
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
		presets_files = os.listdir(presets_path)
		if len(presets_files) > 0:
			pp = presets_path.joinpath(presets_files[0])
			self._loadProgram(pp)

	def loadProgram(self, event):
		filename = ""
		try:
			filename = self._fileDialog(QFileDialog.ExistingFile, QFileDialog.AcceptOpen)
			if filename != "":
				self._loadProgram(filename)

		except Exception as e:
			self.cprint('Unable to read ' + self.midiname + ' program from "' + filename + '": ' + str(e))

	def _loadProgram(self, filename):
		try:
			with open(filename, "rb") as fp:
				lst = json.load(fp)
				pgm = [0] + lst[0]
				try:
					for pk in lst[1]:
						ctlname = pk[0]
						pkName = pk[1]
						ctl = self._ctlFromId(ctlname)
						if ctl is not False:
							ctl.cbName.lineEdit().setText(pkName)
				except Exception as e:
					self.cprint("Error while reading names from backup: " + str(e))
				fp.close()
				self.setProgram(pgm)
				if self.io.isConnected:
					self.sendToRam()
				self.unselPrograms()

		except Exception as e:
			self.cprint('Unable to read ' + self.midiname + ' program from "' + filename + '": ' + str(e))

	def saveProgram(self, event):
		try:
			filename = self._fileDialog(QFileDialog.AnyFile, QFileDialog.AcceptSave)
			if filename != "":
					with open(filename, "w") as fp:
						json.dump([self.program()[1:], self.pkNames()], fp)
						fp.close()
		except Exception as e:
			self.cprint('Unable to save ' + self.midiname + ' program in "' + filename + '": ' + str(e))

	def pkNames(self):
		pkn = []
		l = 0
		for line in self.ui.pads_layout:
			l = l + 1
			c = 0
			for control in line:
				ctl = self._ctlFromId(control)
				if ctl is not False:
					pkn.append([control, ctl.cbName.lineEdit().text()])
				c = c + 1
			l = l + 1
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
		if self.ui.showMidiMessages:
			self.ui.statusbar.showMessage(msg[0:-7]) # without "time=0"

	def warning(self, msg, detail =''):
		self.ui.lblAlert.setText(msg + '.')
		self.cprint(msg + detail)
		QTimer.singleShot(4000, lambda: self.ui.lblAlert.setText(''))

	def cprint(self, msg):
		if True: # future conditionnal debug mode
			print(msg)

	def _padFromNote(self, note):
		if not 'program' in self.io.pad:
			return 0
		if len(self.padNotes) == 0:
			for i in range(0, len(self.io.pad["program"])):
				try:
					ctlname = self.io.pad["program"][i]
				except:
					raise PadException(ctlname + " not found in program.")
				if (ctlname[0:1] == "p") and (ctlname[-5:] == "_note"):
					val = self._getValue(ctlname)
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
			for i in range(0, len(self.io.pad["program"])):
				try:
					ctlname = self.io.pad["program"][i]
				except:
					raise PadException(ctlname + " not found in program.")
				if (ctlname[0:1] == "p") and (ctlname[-3:] == "_pc"):
					val = self._getValue(ctlname)
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
			for i in range(0, len(self.io.pad["program"])):
				try:
					ctlname = self.io.pad["program"][i]
				except:
					raise PadException(ctlname + " not found in program.")
				if (ctlname[0:1] == "k") and (ctlname[-3:] == "_cc"):
					val = self._getValue(ctlname)
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
				pad[0].lightOn()
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


	# Set an UI value. Should be called ONLY f slot self.receiveMidi()
	def _setValue(self, ctlname, value):
		try: 
			if ctlname == "pid" and value != 0:
				pgm = self.findChildren(QWidget, ctlname + str(value))
				pgm[0].select()
			else:
				ctl = self.findChildren(QWidget, ctlname)
				if len(ctl) > 0:
					ctl = ctl[0]
					if isinstance(ctl, QSpinBox):
						ctl.setValue(int(value))
					elif isinstance(ctl, QComboBox):
						ctl.setCurrentIndex(int(value))
					elif isinstance(ctl, QPushButton):
						print('_setValue: to do for QPushButton ...')
		except Exception as e:
			self.cprint("Unable to set " + ctlname +" = " + str(value))

	def _getValue(self, ctlname):
		val = None
		ctl = self.findChildren(QWidget, ctlname)
		if len(ctl) > 0:
			ctl = ctl[0]
			if isinstance(ctl, QSpinBox):
				val = ctl.value()
			elif isinstance(ctl, QComboBox):
				val = ctl.currentIndex()
		elif ctlname == "manufid" and "manufid" in self.io.pad:
			try:
				val = int(self.io.pad["manufid"], 16)
			except:
				pass
		return val

	def closeEvent(self, event):
		if getattr(self, 'midiListener', None) is not None:
			self.midiListener.cancel()

	def program(self):
		pgm = []
		for i in range(0, len(self.io.pad["program"])):
			try:
				ctlname = self.io.pad["program"][i]
			except:
				raise PadException(ctlname + " not found in program.")
			val = self._getValue(ctlname)
			pgm.append(val)
		return(pgm)

	def sendToRam(self):
		if self.io.isConnected:
			self.io.sendProgram(0, self.program())
			self.unselPrograms()

	def sendProgram(self, pid):
		if self.io.isConnected:
			self.io.sendProgram(pid, self.program())

	def setProgram(self, pgm):
		if "program" not in self.io.pad:
			raise PadException('"program" not found in json file')
		if "get_program" not in self.io.pad:
			raise PadException('"get_program" not found in json file')
		if len(pgm) != len(self.io.pad["program"] ):
			raise PadException("received a program with a different size than expected according to json file.")

		self.settingProgram = True
		self.unselPrograms()
		for i in range(0, len(self.device["program"])):
			try:
				ctlname = self.device["program"][i]
				self._setValue(ctlname, int(pgm[i]))
			except Exception as e:
				raise PadException(ctlname + " not found in program: " + str(e))
		self.settingProgram = False


	def getProgram(self, pid):
		if self.io.isConnected:
			self.unselPrograms()
			self.io.getProgram(pid)

	def unselPrograms(self):
		if not self.settingProgram:
			for p in range(1, 5):
				pgm = self.findChildren(QWidget, "pid" + str(p))
				pgm[0].unsel()
			self.padNotes = [] # reinit
			self.padProgramChanges = []
			self.padControlChanges = []

	def plugged(self, in_midiname, out_midiname):
		self.io.openDevicePorts(in_midiname, out_midiname)
		if self.io.isConnected:
			self.ui.setEnabled(True)
			self.ui.retranslateUi()
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
		self.ui.retranslateUi()
		self.ui.setEnabled(False)

class Ui_Pads(Creator, QWidget):
	def __init__(self, settings, parent = None):
		super().__init__(parent)
		self.settings = settings
		self.showMidiMessages = True if str(settings.value('showMidiMessages', "True")) == "True"  else False
		self.device = None
		self.programs = []

	def setupUi(self, device, kit, controls):
		if not self.objectName():
			self.setObjectName(u"Pads")

		self.device = device
		self.midiname = device["midiname"]
		self.pads_layout = device["layout"]

		# Main layout
		self.createObj(u"vLayout", QVBoxLayout(self.parent()))
		self.vLayout.setContentsMargins(0, 5, 0, 0)

		self.createObj(u"hLayout", QHBoxLayout())
		self.hLayout.setContentsMargins(5, 5, 5, 5)
		self.hLayout.setSizeConstraint(QLayout.SetMinAndMaxSize)

		self.createObj(u"vLayoutg", QVBoxLayout())
		self.vLayoutg.setContentsMargins(0, 0, 0, 0)

		for pg in range(1, int(device["nb_programs"] + 1)):
			pgt = str(pg)
			pglayout = Creator.createObj(self.vLayoutg, "pgl" + pgt, QHBoxLayout())
			self.programs.append(Creator.createObj(self.vLayoutg, "pid" + pgt, Program(pgt)))
			pgui = self.programs[pg - 1]
			pgui.setupUi()
			pgui.setEnabled(self.parent().io.isConnected)
			pglayout.addWidget(pgui, alignment = Qt.AlignmentFlag.AlignCenter)
			self.vLayoutg.addLayout(pglayout)
			self.vSpacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
			self.vLayoutg.addItem(self.vSpacer)

		self.createObj(u"hlToRam", QHBoxLayout())
		self.createObj(u"btnToRam", QPushButton())
		self.btnToRam.setStyleSheet("QPushButton{padding: 5px 20px 5px 20px;}")
		self.btnToRam.setEnabled(self.parent().io.isConnected)
		hlspacerg = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		hlspacerd = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.hlToRam.addItem(hlspacerg)
		self.hlToRam.addWidget(self.btnToRam)
		self.hlToRam.addItem(hlspacerd)
		self.vLayoutg.addLayout(self.hlToRam)

		self.verticalSpacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
		self.vLayoutg.addItem(self.verticalSpacer)

		self.createObj(u"tbLayout", QHBoxLayout())
		self.createObj(u"btnLoad", QPushButton())
		self.btnLoad.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DialogOpenButton")))
		self.createObj(u"btnSave", QPushButton())
		self.btnSave.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DialogSaveButton")))
		self.createObj(u"btnOptions", QPushButton())
		self.btnOptions.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_MessageBoxInformation")))
		tblspacerg = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		tblspacerd = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.tbLayout.addItem(tblspacerg)
		self.tbLayout.addWidget(self.btnLoad)
		self.tbLayout.addWidget(self.btnSave)
		self.tbLayout.addWidget(self.btnOptions)
		self.tbLayout.addItem(tblspacerd)
		self.vLayoutg.addLayout(self.tbLayout)

		self.verticalSpacer2 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
		self.vLayoutg.addItem(self.verticalSpacer2)

		self.hLayout.addLayout(self.vLayoutg)

		self.createObj(u"gLayoutd", QGridLayout())
		self.gLayoutd.setContentsMargins(0, 0, 0, 0)
		l = 0
		for line in self.pads_layout:
			l = l + 1
			c = 0
			for pad in line:
				spad = str(pad)
				ctlType = spad.rstrip("0123456789")
				ctlNum = spad[len(ctlType):]
				if ctlType in ['p', 'pc']:
					ctlClass = Pad(ctlNum, self.settings)
					params = {"bordColorOff" : "#882100", "bordColorOn" : "#ff2800", "kit": kit}
					params['rgb'] = (ctlType == 'pc')
					ctlClass.sendNoteOn.connect(lambda note: self.parent().io.sendNoteOn(self.mc.currentIndex(), note))
					ctlClass.sendNoteOff.connect(lambda note: self.parent().io.sendNoteOff(self.mc.currentIndex(), note))
				elif ctlType == "k":
					ctlClass = Knob(ctlNum)
					ctlClass.sendControlChanged.connect(lambda cc, val: self.parent().io.sendControlChanged(self.mc.currentIndex(), cc, val))
					params = {"controls": controls}
				ctl = Creator.createObj(self.gLayoutd, ctlType + ctlNum, ctlClass)
				ctl.setupUi(params)
				self.gLayoutd.addWidget(ctl, l, c)
				c = c + 1
			l = l + 1

		self.createObj(u"hLayoutMC", QHBoxLayout())
		self.hLayoutMC.setContentsMargins(0, 0, 0, 0)

		self.createObj(u"labelMC", QLabel())
		self.labelMC.setStyleSheet("padding-left: 15px;")
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

		self.gLayoutd.addLayout(self.hLayoutMC, l + 1, 0, 1, c)
		self.hLayout.addLayout(self.gLayoutd)
		self.vLayout.addLayout(self.hLayout)

		if self.showMidiMessages:
			self.createObj(u"statusbar", QStatusBar())
			self.vLayout.addWidget(self.statusbar)

		self.retranslateUi()

		self.btnLoad.clicked.connect(self.parent().loadProgram)
		self.btnSave.clicked.connect(self.parent().saveProgram)
		self.btnOptions.clicked.connect(self.showOptionsDialog)
		self.btnToRam.clicked.connect(self.parent().sendToRam)

		self.mc.currentIndexChanged.connect(self.valueChanged)

		QMetaObject.connectSlotsByName(self)

	def retranslateUi(self):
		virtual = "" if self.parent().io.isConnected else "virtual "
		self.parent().setWindowTitle(QCoreApplication.translate("Pads", u"Freepad " + virtual + self.midiname, None))
		self.btnToRam.setText(QCoreApplication.translate("Pads", u"Send to RAM", None))
		self.labelMC.setText(QCoreApplication.translate("Pads", u"Midi channel", None))

	def setEnabled(self, enabled : bool):
		for pg in self.programs:
			pg.setEnabled(enabled)
		self.btnToRam.setEnabled(enabled)

	def valueChanged(self, value):
		self.parent().unselPrograms()

	def showOptionsDialog(self, event):
		dialog = FreepadOptionsWindow(self.settings)
		dialog.setupUi(self.parent().midiname)
		dialog.exec()


# TODO : map keybord on pad. This will probably won't work. May be we need to capture keyboard events and test
# its to fire pads when no input control have focus
	def keyPressEvent(self, event):
		if isinstance(event, QKeyEvent):
			key_text = event.text()
			print(f"Last Key Pressed: {key_text}")

	def keyReleaseEvent(self, event):
		if isinstance(event, QKeyEvent):
			key_text = event.text()
			print(f"Key Released: {key_text}")

