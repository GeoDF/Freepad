from qtpy.QtCore import QMetaObject, QSize, Qt, QTimer, Signal
from qtpy.QtWidgets import QColorDialog, QComboBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, \
		QLineEdit, QPushButton, QSlider, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget
from qtpy.QtGui import QColor

from pad.ui.common import Creator, Spinput, tr, \
	FREEPAD_BORD_COLOR,FREEPAD_LGRADIENT, FREEPAD_RGRADIENT

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
		# Midi require values < 128, so colors are split into two bytes
		self.off_red1 = 1
		self.off_red2 = 9
		self.off_green1 = 0
		self.off_green2 = 33
		self.off_blue1 = 0
		self.off_blue2 = 0
		self.on_red1 = 1
		self.on_red2 = 127
		self.on_green1 = 0
		self.on_green2 = 40
		self.on_blue1 = 0
		self.on_blue2 = 0
		self.bv = False
		self.rgb = False
		self.mc = 16
		self.noteString = [
			["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
			[u"Do", u"Do#", u"Ré", u"Ré#", u"Mi", u"Fa", u"Fa#", u"Sol", u"Sol#", u"La", u"La#", u"Si",]
		]

	def setupUi(self, params):
		subcontrols = {}
		for p in params:
			setattr(self, p, params[p])

		on_red = 128 * self.on_red1 + self.on_red2
		on_green = 128 * self.on_green1 + self.on_green2
		on_blue = 128 * self.on_blue1 + self.on_blue2
		off_red = 128 * self.off_red1 + self.off_red2
		off_green = 128 * self.off_green1 + self.off_green2
		off_blue = 128 * self.off_blue1 + self.off_blue2
		vn = 'p' + self.pad_id
		subcontrols[vn + '_off_red1'] = self
		subcontrols[vn + '_off_red2'] = self
		subcontrols[vn + '_off_green1'] = self
		subcontrols[vn + '_off_green2'] = self
		subcontrols[vn + '_off_blue1'] = self
		subcontrols[vn + '_off_blue2'] = self
		subcontrols[vn + '_on_red1'] = self
		subcontrols[vn + '_on_red2'] = self
		subcontrols[vn + '_on_green1'] = self
		subcontrols[vn + '_on_green2'] = self
		subcontrols[vn + '_on_blue1'] = self
		subcontrols[vn + '_on_blue2'] = self

		self.setStyleSheet('''
#padLW {
	border: 1px solid rgb(''' + str(off_red) + ''',''' + str(off_green) + ''',''' + str(off_blue) + ''');
	border-radius: 5px;
}
#cbName {
	max-width: 120px;
	background: transparent;
}
#cbName QListView {
	min-width: 150px;
	border: 1px inset ''' + FREEPAD_BORD_COLOR + '''; border-radius: 3px; border-top-left-radius: 0;
}
'''
)

		# Pad main layout
		self.createObj('padMainLayout', QVBoxLayout(self))
		self.padMainLayout.setContentsMargins(0, 0, 0, 0)
		self.padMainLayout.setSpacing(0)
		# Pad frame
		self.createObj(u"padLW", QFrame())
		self.padLW.setFrameStyle(QFrame.StyledPanel)
		self.padMainLayout.addWidget(self.padLW)

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
			ctlname = 'p' + self.pad_id + '_off'
			btnOff = self.createObj(ctlname, QPushButton())
			btnOff.setMaximumSize(12, 12)
			btnOff.setStyleSheet('background-color: rgb(' + str(off_red) +',' + str(off_green) + ',' + str(off_blue) + ');')
			btnOff.clicked.connect(lambda e: self.chooseColor('off'))
			subcontrols[ctlname] = btnOff
			ctlname = 'p' + self.pad_id + '_on'
			btnOn = self.createObj(ctlname, QPushButton())
			self.btnNoteHL.addWidget(btnOff, Qt.AlignmentFlag.AlignLeft)
			btnOn.setMaximumSize(12, 12)
			btnOn.setStyleSheet('background-color: rgb(' + str(on_red) +',' + str(on_green) + ',' + str(on_blue) + ');')
			btnOn.clicked.connect(lambda e: self.chooseColor('on'))
			subcontrols[ctlname] = btnOn
		self.createObj(u"btnNote", QPushButton())
		self.btnNote.setStyleSheet("margin: 0; padding: 3px; border-radius: 3px;")
		self.btnNote.setMaximumWidth(60)
		self.btnNoteHL.addWidget(self.btnNote, Qt.AlignmentFlag.AlignCenter)
		if self.rgb:
			self.btnNoteHL.addWidget(btnOn, Qt.AlignmentFlag.AlignRight)
		self.verticalLayout.addLayout(self.btnNoteHL)

		self.createObj('hlp', QHBoxLayout())
		self.createObj('vl2', QVBoxLayout())

		ctlname = 'p' + self.pad_id + '_note'
		self.spNote = Spinput()
		self.spNote.setupUi(ctlname, tr(u"Note", None))
		self.vl2.addWidget(self.spNote)
		subcontrols[ctlname] = self.spNote.spin

		ctlname = 'p' + self.pad_id + '_cc'
		self.spCC = Spinput()
		self.spCC.setupUi(ctlname, tr(u"CC", None))
		self.vl2.addWidget(self.spCC)
		subcontrols[ctlname] = self.spCC.spin

		ctlname = 'p' + self.pad_id + '_pc'
		self.spPC = Spinput()
		self.spPC.setupUi(ctlname, tr(u"PC", None))
		self.vl2.addWidget(self.spPC)
		subcontrols[ctlname] = self.spPC.spin

		if self.bv:
			ctlname = 'p' + self.pad_id + '_bv'
			self.cbBehavior = self.createObj(ctlname, QComboBox(self.padLW))
			self.cbBehavior.setEditable(True)
			self.cbBehavior.lineEdit().setReadOnly(True)
			self.cbBehavior.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
			self.cbBehavior.addItem("")
			self.cbBehavior.addItem("")
			self.cbBehavior.currentIndexChanged.connect(self.valueChanged)
			self.vl2.addWidget(self.cbBehavior)
			subcontrols[ctlname] = self.cbBehavior

		if self.mc < 16:
			ctlname = 'p' + self.pad_id + '_mc'
			self.cbMC = self.createObj("p" + self.pad_id + "_mc", QComboBox(self.padLW))
			self.cbMC.setEditable(True)
			self.cbMC.lineEdit().setReadOnly(True)
			self.cbMC.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
			for ch in range(1,17):
				sp = "  " if ch < 10 else ""
				self.cbMC.addItem(sp + str(ch))
			self.cbMC.addItem("Global")
			self.cbMC.setCurrentIndex(16)
			self.mc = 16
			self.cbMC.currentIndexChanged.connect(self.mcChanged)
			self.vl2.addWidget(self.cbMC)
			subcontrols[ctlname] = self.cbMC

		self.hlp.addLayout(self.vl2)

		# Level
		self.createObj('vlLevel', QVBoxLayout())
		self.createObj('level', Level(self))
		self.vlLevel.addWidget(self.level, 0, Qt.AlignmentFlag.AlignHCenter)
		self.vlLevel.addItem(QSpacerItem(0, 4, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
		# Key
		self.createObj('leKey', keyEdit())
		self.leKey.textChanged.connect(lambda: self.keyChanged.emit(self.pad_id, self.leKey.text()))
		self.vlLevel.addWidget(self.leKey)
		self.vlLevel.addItem(QSpacerItem(0, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

		self.hlp.addLayout(self.vlLevel)
		self.verticalLayout.addLayout(self.hlp)

		self.retranslateUi()
		self.setFixedSize(self.padMainLayout.sizeHint())

		self.cbName.currentIndexChanged.connect(self.instrumentChanged)
		self.spNote.valueChanged.connect(self.noteChanged)
		self.spCC.valueChanged.connect(self.valueChanged)
		self.spPC.valueChanged.connect(self.valueChanged)

		self.btnNote.pressed.connect(self._sendNoteOn)
		self.btnNote.released.connect(self._sendNoteOff)

		QMetaObject.connectSlotsByName(self)
		self.noteChanged(0)
		return subcontrols
		# setupUi

	def retranslateUi(self):
		if self.bv:
			self.cbBehavior.setItemText(0, tr(u"Tap", None))
			self.cbBehavior.setItemText(1, tr(u"Toggle", None))

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
			red = 128 * self.on_red1 + self.on_red2
			green = 128 * self.on_green1 + self.on_green2
			blue = 128 * self.on_blue1 + self.on_blue2
			self.padLW.setStyleSheet(
'#padLW {border-color: rgb(' + str(red) + ',' + str(green) + ',' + str(blue) + ');}'
)
			shadow = QGraphicsDropShadowEffect()
			shadow.setColor(QColor(red, green, blue))
			shadow.setOffset(1, 1)
			shadow.setBlurRadius(12)
			self.setGraphicsEffect(shadow)
			self.level.setVelocity(int(velocity))
		except Exception as e:
			self.parent().cprint('Error in Pad.lightOn: ' + str(e))

	def lightOff(self):
		try:
			self.padLW.setStyleSheet(
'#padLW {border-color: rgb(' + \
str(128 * self.off_red1 + self.off_red2) + ',' + \
str(128 * self.off_green1 + self.off_green2) + ',' + \
str(128 * self.off_blue1 + self.off_blue2) + ');}'
)
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
		red = 128 * getattr(self, col + '_red1') + getattr(self, col + '_red1')
		green = 128 * getattr(self, col + '_green1') + getattr(self, col + '_green2')
		blue = 128 * getattr(self, col + '_blue1') + getattr(self, col + '_blue2')
		color = QColorDialog.getColor(QColor(red, green, blue), self)
		if color.isValid():
			btn = getattr(self, "p" + self.pad_id + "_" + col)
			btn.setStyleSheet('background-color: ' + color.name() + ';')
			red = color.red()
			green = color.green()
			blue = color.blue()
			setattr(self, col + '_red1', int(red / 128))
			setattr(self, col + '_red2', red % 128)
			setattr(self, col + '_green1', int(green / 128))
			setattr(self, col + '_green2', green % 128)
			setattr(self, col + '_blue1', int(blue / 128))
			setattr(self, col + '_blue2', blue % 128)
			if col == 'off':
				self.lightOff()


class Level(QSlider):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setMinimum(0)
		self.setMaximum(127)
		self.setOrientation(Qt.Orientation.Vertical)
		self.setStyleSheet(
'''QSlider::vertical {
	width: 22px;
}
QSlider::groove:vertical {
	width: 5px; border: 1px solid #111111;
	background: qlineargradient(spread:pad, x1:1, y1:1, x2:1, y2:0.011, stop:0 rgba(0, 85, 0, 255), stop:0.511211 rgba(128, 85, 0, 255), stop:1 rgba(170, 0, 0, 255));
}
QSlider::sub-page:vertical {
	width: 5px; border: 1px solid #000000; background: ''' + FREEPAD_LGRADIENT + ''';
}
QSlider::handle:vertical:focus {
	width: 22px; margin-left: -4px; margin-right: -6px; height: 5px;
	border: 1px outset #882200; border-radius: 3px; background: #441100;
}
QSlider::handle:vertical:hover {
	background: #882200;
}'''
)
		self.defaultVelocity = 80 # velocity when sending midi notes
		self._settingVelocity = False
		self.valueChanged.connect(self.setDefaultVelocity)
		self.sliderPressed.connect(self._sliderPressed)
		self.sliderReleased.connect(self._sliderReleased)

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

	def _sliderPressed(self):
		self.setCursor(Qt.CursorShape.ClosedHandCursor)

	def _sliderReleased(self):
		self.setCursor(Qt.CursorShape.ArrowCursor)

class keyEdit(QLineEdit):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setFixedSize(QSize(20,20))
		self.setMaxLength(1)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
		self.setStyleSheet('''
QLineEdit {
	border: 1px outset #111111;
	border-radius: 3px; background: ''' + FREEPAD_RGRADIENT + ''';
	selection-color: #ff3800;
	selection-background-color: #001828;
}
QLineEdit:focus, QLineEdit:hover {
	border: 1px inset ''' + FREEPAD_BORD_COLOR + ''';
}''')

	def focusInEvent(self, *args, **kwargs):
		QTimer.singleShot(0, self.selectAll)
		return QLineEdit.focusInEvent(self, *args, **kwargs)

