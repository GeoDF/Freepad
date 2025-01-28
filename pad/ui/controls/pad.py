from qtpy.QtCore import QCoreApplication, QMetaObject, Qt, Signal
from qtpy.QtWidgets import QColorDialog, QComboBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, \
		QPushButton, QVBoxLayout, QWidget
from qtpy.QtGui import QColor

from pad.ui.common import Creator, Spinput

class Pad(QWidget, Creator):
	sendNoteOn = Signal(int, int)
	sendNoteOff = Signal(int, int)

	def __init__(self, title, settings, parent = None):
		super().__init__(parent)
		self.padTitle = title
		self.note = 0
		self.noteStyle = int(settings.value('noteStyle', 1))
		self.kit = {}
		self.bordColorOff = "#882100"
		self.bordColorOn = "#ff2800"
		self.bv = False
		self.rgb = False
		self.mc = 16
		self.noteString = [
			["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
			[u"Do", u"Do#", u"Ré", u"Ré#", u"Mi", u"Fa", u"Fa#", u"Sol", u"Sol#", u"La", u"La#", u"Si",]
		]

	def setupUi(self, params):
		for p in ['bordColorOff', 'bordColorOn', 'kit', 'rgb', 'bv', 'mc']:
			if p in params:
				setattr(self, p, params[p])

		self.setStyleSheet("Pad #padLW {"
"border: 1px solid " + self.bordColorOff + "; border-radius: 5px;"
"}"
"Pad #cbName {"
"background: transparent;"
"}"
"Pad #cbName QListView {"
"min-width: 150px;"
"border: 1px inset #441200; border-radius: 3px; border-top-left-radius: 0;"
"}"
)

		self.createObj(u"padLW", QFrame(self))
		self.padLW.setFrameStyle(QFrame.StyledPanel)

		self.createObj(u"verticalLayout", QVBoxLayout())
		self.padLW.setLayout(self.verticalLayout)
		self.verticalLayout.setContentsMargins(5, 5, 5, 5)
		self.verticalLayout.setSpacing(3)

		self.createObj(u"cbName", QComboBox())
		self.cbName.setEditable(True)
		self.cbName.setMaximumWidth(100)
		self.cbName.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.cbName.addItem(u"Pad " + self.padTitle)
		if self.kit is not None:
			for note in self.kit:
				self.cbName.addItem(self.kit[note])
		self.verticalLayout.addWidget(self.cbName)

		self.btnNoteHL = QHBoxLayout()
		if self.rgb:
			btnOff = self.createObj("pc" + self.padTitle + "_coff", QPushButton())
			btnOff.setMaximumSize(12, 12)
			btnOff.setStyleSheet('background-color: ' + self.bordColorOff + ';')
			btnOff.clicked.connect(lambda e: self.chooseColor('Off'))
			btnOn = self.createObj("pc" + self.padTitle + "_con", QPushButton())
			self.btnNoteHL.addWidget(btnOff, Qt.AlignmentFlag.AlignLeft)
			btnOn.setMaximumSize(12, 12)
			btnOn.setStyleSheet('background-color: ' + self.bordColorOn + ';')
			btnOn.clicked.connect(lambda e: self.chooseColor('On'))
		self.createObj(u"btnNote", QPushButton())
		self.btnNote.setStyleSheet("margin: 0; padding: 3px; border-radius: 3px;")
		self.btnNote.setMaximumWidth(60)
		self.btnNoteHL.addWidget(self.btnNote, Qt.AlignmentFlag.AlignCenter)
		if self.rgb:
			self.btnNoteHL.addWidget(btnOn, Qt.AlignmentFlag.AlignRight)
		self.verticalLayout.addLayout(self.btnNoteHL)

		self.spNote = Spinput()
		self.spNote.setupUi("p" + self.padTitle + "_note", QCoreApplication.translate("Pad", u"Note", None))
		self.verticalLayout.addWidget(self.spNote)

		self.spCC = Spinput()
		self.spCC.setupUi("p" + self.padTitle + "_cc", QCoreApplication.translate("Pad", u"CC", None))
		self.verticalLayout.addWidget(self.spCC)

		self.spPC = Spinput()
		self.spPC.setupUi("p" + self.padTitle + "_pc", QCoreApplication.translate("Pad", u"PC", None))
		self.verticalLayout.addWidget(self.spPC)

		if self.bv:
			self.cbBehavior = self.createObj("p" + self.padTitle + "_b", QComboBox(self.padLW))
			self.cbBehavior.addItem("")
			self.cbBehavior.addItem("")
			self.cbBehavior.currentIndexChanged.connect(self.valueChanged)
			self.verticalLayout.addWidget(self.cbBehavior)

		if self.mc < 16:
			self.cbMC = self.createObj("p" + self.padTitle + "_mc", QComboBox(self.padLW))
			for ch in range(1,17):
				sp = "  " if ch < 10 else ""
				self.cbMC.addItem(sp + str(ch))
			self.cbMC.addItem("Global")
			self.cbMC.setCurrentIndex(16)
			self.mc = 16
			self.cbMC.currentIndexChanged.connect(self.mcChanged)
			self.verticalLayout.addWidget(self.cbMC)

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

	def lightOn(self):
		try:
			self.padLW.setStyleSheet("#padLW {border-color: " + self.bordColorOn + ";}")
			shadow = QGraphicsDropShadowEffect()
			shadow.setColor(QColor(self.bordColorOn))
			shadow.setOffset(1, 1)
			shadow.setBlurRadius(12)
			self.setGraphicsEffect(shadow)
		except:
			pass

	def lightOff(self):
		try:
			self.padLW.setStyleSheet("#padLW {border-color: " + self.bordColorOff + ";}")
			self.setGraphicsEffect(None)
		except:
			pass

	def _sendNoteOn(self):
		self.sendNoteOn.emit(self.mc, self.note)
		self.lightOn()

	def _sendNoteOff(self):
		self.sendNoteOff.emit(self.mc, self.note)
		self.lightOff()

	def chooseColor(self, col):
		color = QColorDialog.getColor()
		btn = getattr(self, "pc" + self.padTitle + "_c" + col.lower())
		btn.setStyleSheet('background-color: ' + color.name() + ';')
		setattr(self, 'bordColor' + col, color.name())
		if col == 'Off':
			self.lightOff()


