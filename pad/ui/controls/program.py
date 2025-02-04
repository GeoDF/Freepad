from qtpy.QtCore import QMetaObject, Qt
from qtpy.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from pad.ui.common import Creator, tr

class Program(QWidget , Creator):
	def __init__(self, n, parent = None):
		super().__init__(parent)
		self.n = n

	def setupUi(self):
		self.createObj("vLayout", QVBoxLayout(self))
		self.vLayout.setContentsMargins(0, 0, 0, 0)
		self.vLayout.setSpacing(0)

		self.lblhLayout = QHBoxLayout()
		self.lblhLayout.setContentsMargins(0, 0, 0, 0)

		self.lblhSpacerg = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.lblhLayout.addItem(self.lblhSpacerg)

		self.createObj("lblTitleChecked", QLabel())
		self.lblTitleChecked.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.lblTitleChecked.setFixedWidth(12)
		self.lblTitleChecked.setStyleSheet("background: transparent;")
		self.lblhLayout.addWidget(self.lblTitleChecked)

		self.createObj("bTitle", QPushButton())
		self.bTitle.setStyleSheet("border: none; background: transparent")
		self.lblhLayout.addWidget(self.bTitle)

		self.lblhSpacerd = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.lblhLayout.addItem(self.lblhSpacerd)

		self.vLayout.addLayout(self.lblhLayout)

		self.createObj("hLayout", QHBoxLayout())
		self.hLayout.setContentsMargins(0, 0, 0, 0)
		self.hLayout.setSpacing(10)

		self.btnGet = QPushButton()
		self.hLayout.addWidget(self.btnGet)
		self.btnSend = QPushButton()
		self.hLayout.addWidget(self.btnSend)

		self.vLayout.addLayout(self.hLayout)
		self.vSpacer = QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
		self.vLayout.addItem(self.vSpacer)

		self.retranslateUi()

		self.btnSend.clicked.connect(self.sendProgram)
		self.btnGet.clicked.connect(self.getProgram)
		self.bTitle.clicked.connect(self.getProgram)

		QMetaObject.connectSlotsByName(self)

	def retranslateUi(self):
		self.pTitle = tr("Program", u"Program" + " " + self.n, None)
		self.bTitle.setText(self.pTitle)
		self.btnGet.setText(tr("Program", u"Get", None))
		self.btnSend.setText(tr("Program", u"Send", None))

	def sendProgram(self):
		self.parent().sendProgram(self.n)

	def getProgram(self):
		self.parent().getProgram(self.n)

	def select(self):
		self.lblTitleChecked.setText('<font color="green">\u2714</font>')

	def unsel(self):
		self.lblTitleChecked.setText("")

	def setEnabled(self, val):
		self.bTitle.setEnabled(val)
		self.btnSend.setEnabled(val)
		self.btnGet.setEnabled(val)




