from qtpy.QtCore import QCoreApplication, QMetaObject, QSize, Qt, QTimer, Signal
from qtpy.QtWidgets import QColorDialog, QComboBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, \
		QLineEdit, QPushButton, QSlider, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget
from qtpy.QtGui import QColor

from pad.ui.common import Creator, Spinput

class Pad(QWidget, Creator):
	sendNoteOn = Signal(int, int, int)
	sendNoteOff = Signal(int, int, int)
	keyChanged = Signal(str, str)

	def __init__(self, pad_id, settings, parent = None):
		super().__init__(parent)
		self.pad_id = pad_id
		self.note = 0
		self.noteStyle = int(settings.value('noteStyle', 1))
		self.kit = {}
		self.off_red = 136
		self.off_green = 33
		self.off_blue = 0
		self.on_red = 255
		self.on_green = 40
		self.on_blue = 0
		self.bv = False
		self.rgb = False
		self.mc = 16
		self.noteString = [
			["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
			[u"Do", u"Do#", u"Ré", u"Ré#", u"Mi", u"Fa", u"Fa#", u"Sol", u"Sol#", u"La", u"La#", u"Si",]
		]

	def setupUi(self, params):
		for p in params:
			setattr(self, p, params[p])

		self.setStyleSheet("Pad #padLW {"
"border: 1px solid rgb(" + str(self.off_red) +',' + str(self.off_green) + ',' + str(self.off_blue) + "); border-radius: 5px;"
"}"
"Pad #cbName {"
	"max-width: 120px;"
	"background: transparent;"
"}"
"Pad #cbName QListView {"
	"min-width: 150px;"
	"border: 1px inset #441200; border-radius: 3px; border-top-left-radius: 0;"
"}"
'QSlider::vertical {'
	'width: 22px;'
'}'
'QSlider::groove:vertical {'
	'width: 5px; border: 1px solid #111111;'
	'background: qlineargradient(spread:pad, x1:1, y1:1, x2:1, y2:0.011, stop:0 rgba(0, 85, 0, 255), stop:0.511211 rgba(255, 170, 0, 255), stop:1 rgba(170, 0, 0, 255));'
'}'
'QSlider::sub-page:vertical {'
	'width: 5px; border: 1px solid #000000; background: ' + self.lgradient + ';}'
'QSlider::handle:vertical:focus {width: 20px; margin-left: -5px; margin-right: -5px; height: 5px; border: 1px solid #882200; border-radius: 3px; background: #442200;}'
'QLineEdit {border: 1px outset #111111; border-radius: 3px; background: ' + self.rgradient + '; selection-color: #ff3800; selection-background-color: #001828;}'
'QLineEdit:focus, QLineEdit:hover {border: 1px inset #441200;}'
)

		self.createObj(u"padLW", QFrame(self))
		self.padLW.setFrameStyle(QFrame.StyledPanel)

		self.createObj(u"verticalLayout", QVBoxLayout())
		self.padLW.setLayout(self.verticalLayout)
		self.verticalLayout.setContentsMargins(5, 5, 5, 5)
		self.verticalLayout.setSpacing(3)

		self.createObj(u"cbName", QComboBox())
		self.cbName.setEditable(True)
		self.cbName.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.cbName.addItem(u"Pad " + self.pad_id)
		if self.kit is not None:
			for note in self.kit:
				self.cbName.addItem(self.kit[note])
		self.verticalLayout.addWidget(self.cbName)

		self.btnNoteHL = QHBoxLayout()
		if self.rgb:
			btnOff = self.createObj("p" + self.pad_id + "_off", QPushButton())
			btnOff.setMaximumSize(12, 12)
			btnOff.setStyleSheet('background-color: rgb(' + str(self.off_red) +',' + str(self.off_green) + ',' + str(self.off_blue) + ');')
			btnOff.clicked.connect(lambda e: self.chooseColor('off'))
			btnOn = self.createObj("p" + self.pad_id + "_on", QPushButton())
			self.btnNoteHL.addWidget(btnOff, Qt.AlignmentFlag.AlignLeft)
			btnOn.setMaximumSize(12, 12)
			btnOn.setStyleSheet('background-color: rgb(' + str(self.on_red) +',' + str(self.on_green) + ',' + str(self.on_blue) + ');')
			btnOn.clicked.connect(lambda e: self.chooseColor('on'))
		self.createObj(u"btnNote", QPushButton())
		self.btnNote.setStyleSheet("margin: 0; padding: 3px; border-radius: 3px;")
		self.btnNote.setMaximumWidth(60)
		self.btnNoteHL.addWidget(self.btnNote, Qt.AlignmentFlag.AlignCenter)
		if self.rgb:
			self.btnNoteHL.addWidget(btnOn, Qt.AlignmentFlag.AlignRight)
		self.verticalLayout.addLayout(self.btnNoteHL)

		self.createObj('hl', QHBoxLayout())
		self.createObj('vl2', QVBoxLayout())

		self.spNote = Spinput()
		self.spNote.setupUi("p" + self.pad_id + "_note", QCoreApplication.translate("Pad", u"Note", None))
		self.vl2.addWidget(self.spNote)

		self.spCC = Spinput()
		self.spCC.setupUi("p" + self.pad_id + "_cc", QCoreApplication.translate("Pad", u"CC", None))
		self.vl2.addWidget(self.spCC)

		self.spPC = Spinput()
		self.spPC.setupUi("p" + self.pad_id + "_pc", QCoreApplication.translate("Pad", u"PC", None))
		self.vl2.addWidget(self.spPC)

		if self.bv:
			self.cbBehavior = self.createObj("p" + self.pad_id + "_bv", QComboBox(self.padLW))
			self.cbBehavior.addItem("")
			self.cbBehavior.addItem("")
			self.cbBehavior.currentIndexChanged.connect(self.valueChanged)
			self.vl2.addWidget(self.cbBehavior)

		if self.mc < 16:
			self.cbMC = self.createObj("p" + self.pad_id + "_mc", QComboBox(self.padLW))
			for ch in range(1,17):
				sp = "  " if ch < 10 else ""
				self.cbMC.addItem(sp + str(ch))
			self.cbMC.addItem("Global")
			self.cbMC.setCurrentIndex(16)
			self.mc = 16
			self.cbMC.currentIndexChanged.connect(self.mcChanged)
			self.vl2.addWidget(self.cbMC)

		self.hl.addLayout(self.vl2)

		# Level
		self.createObj('vlLevel', QVBoxLayout())
		self.createObj('level', Level(self))
		self.vlLevel.addWidget(self.level, 0, Qt.AlignmentFlag.AlignHCenter)
		self.vlLevel.addItem(QSpacerItem(15, 4, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
		# Key
		self.createObj('leKey', keyEdit())
		self.leKey.textChanged.connect(lambda: self.keyChanged.emit(self.pad_id, self.leKey.text()))
		self.vlLevel.addWidget(self.leKey)
		self.vlLevel.addItem(QSpacerItem(15, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

		self.hl.addLayout(self.vlLevel)
		self.verticalLayout.addLayout(self.hl)

		self.verticalLayout.addLayout(self.hl)

		self.setFixedSize(self.padLW.sizeHint())

		self.retranslateUi()

		self.cbName.currentIndexChanged.connect(self.instrumentChanged)
		self.spNote.valueChanged.connect(self.noteChanged)
		self.spCC.valueChanged.connect(self.valueChanged)
		self.spPC.valueChanged.connect(self.valueChanged)

		self.btnNote.pressed.connect(self._sendNoteOn)
		self.btnNote.released.connect(self._sendNoteOff)

		QMetaObject.connectSlotsByName(self)
		self.noteChanged(0)
		# setupUi

	def retranslateUi(self):
		if self.bv:
			self.cbBehavior.setItemText(0, QCoreApplication.translate("Pad", u"Tap", None))
			self.cbBehavior.setItemText(1, QCoreApplication.translate("Pad", u"Toggle", None))

	def instrumentChanged(self, index):
		if index > 0:
			instrument = self.cbName.itemText(index)
			note = [note for note, i in self.kit.items() if i == instrument][0]
			self.spNote.spin.setValue(note)

	def noteChanged(self, value):
		octave = int(value / 12) - 1
		self.btnNote.setText(str(self.noteString[self.noteStyle][value % 12]) + " " + str(octave))
		self.note = value
		self.valueChanged()

	def mcChanged(self, index):
		self.mc = index

	def valueChanged(self):
		if self.parent() is not None:
			self.parent().unselPrograms()

	def lightOn(self, velocity):
		try:
			self.padLW.setStyleSheet('#padLW {border-color: rgb(' + str(self.on_red) +',' + str(self.on_green) + ',' + str(self.on_blue) + ');}')
			shadow = QGraphicsDropShadowEffect()
			shadow.setColor(QColor(self.on_red, self.on_green, self.on_blue))
			shadow.setOffset(1, 1)
			shadow.setBlurRadius(12)
			self.setGraphicsEffect(shadow)
			self.level.setVelocity(int(velocity))
		except Exception as e:
			self.parent().cprint('Error in Pad.lightOn: ' + str(e))

	def lightOff(self):
		try:
			self.padLW.setStyleSheet('#padLW {border-color: rgb(' + str(self.off_red) +',' + str(self.off_green) + ',' + str(self.off_blue) + ');}')
			self.setGraphicsEffect(None)
			self.level.setVelocity(0)
		except:
			pass

	def _sendNoteOn(self):
		self.sendNoteOn.emit(self.mc, self.note, self.level.defaultVelocity)
		self.lightOn(self.level.defaultVelocity)

	def _sendNoteOff(self):
		self.sendNoteOff.emit(self.mc, self.note, self.level.defaultVelocity)
		self.lightOff()

	def chooseColor(self, col):
		color = QColorDialog.getColor()
		btn = getattr(self, "p" + self.pad_id + "_" + col)
		btn.setStyleSheet('background-color: ' + color.name() + ';')
		setattr(self, col + '_red', color.red())
		setattr(self, col + '_green', color.green())
		setattr(self, col + '_blue', color.blue())
		if col == 'off':
			self.lightOff()


class Level(QSlider):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setMinimum(0)
		self.setMaximum(127)
		self.setOrientation(Qt.Orientation.Vertical)
		self.defaultVelocity = 64 # velocity when sending midi notes
		self._settingVelocity = False
		self.valueChanged.connect(self.setDefaultVelocity)

	def focusInEvent(self, *args, **kwargs):
		self.setVelocity(self.defaultVelocity)
		return QSlider.focusInEvent(self, *args, **kwargs)

	def focusOutEvent(self, *args, **kwargs):
		self.setVelocity(0)
		return QSlider.focusInEvent(self, *args, **kwargs)

	def setDefaultVelocity(self, v):
		if not self._settingVelocity:
			self.defaultVelocity = v

	def setVelocity(self, v):
		self._settingVelocity = True
		self.setValue(v)
		self._settingVelocity = False

class keyEdit(QLineEdit):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setFixedSize(QSize(20,20))
		self.setMaxLength(1)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

	def focusInEvent(self, *args, **kwargs):
		QTimer.singleShot(0, self.selectAll)
		return QLineEdit.focusInEvent(self, *args, **kwargs)

