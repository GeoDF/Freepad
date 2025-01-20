from qtpy.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from qtpy.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

class Program(QWidget):
	def __init__(self, n, parent = None):
		super().__init__(parent)
		self.n = n

	def setupUi(self):
		if not self.objectName():
			self.setObjectName("Program")

		self.setMinimumSize(QSize(138, 65))

		self.vLayout = QVBoxLayout(self)
		self.vLayout.setObjectName("verticalLayout")
		self.vLayout.setContentsMargins(0, 0, 0, 0)
		
		self.lblhLayout = QHBoxLayout()
		self.lblhLayout.setContentsMargins(0, 0, 0, 0)

		self.lblhSpacerg = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.lblhLayout.addItem(self.lblhSpacerg)

		self.lblTitleChecked = QLabel()
		self.lblTitleChecked.setObjectName("lblTitleChecked")
		self.lblTitleChecked.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.lblTitleChecked.setFixedWidth(12)
		self.lblTitleChecked.setStyleSheet("background: transparent;")
		self.lblhLayout.addWidget(self.lblTitleChecked)

		self.bTitle = QPushButton()
		self.bTitle.setObjectName("bTitle")
		self.bTitle.setStyleSheet("border: none; background: transparent")
		self.lblhLayout.addWidget(self.bTitle)

		self.lblhSpacerd = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.lblhLayout.addItem(self.lblhSpacerd)

		self.vLayout.addLayout(self.lblhLayout)

		self.hLayout = QHBoxLayout()
		self.hLayout.setObjectName("hLayout")
		self.hLayout.setContentsMargins(0, 0, 0, 0)

		self.hSpacerl = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.hLayout.addItem(self.hSpacerl)

		self.btnGet = QPushButton()
		self.hLayout.addWidget(self.btnGet)

		self.btnSend = QPushButton()
		self.hLayout.addWidget(self.btnSend)

		self.hSpacerd = QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.hLayout.addItem(self.hSpacerd)

		self.vLayout.addLayout(self.hLayout)
		self.vSpacer = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
		self.vLayout.addItem(self.vSpacer)

		self.retranslateUi()

		self.btnSend.clicked.connect(self.sendProgram)
		self.btnGet.clicked.connect(self.getProgram)
		self.bTitle.clicked.connect(self.getProgram)

		QMetaObject.connectSlotsByName(self)

	def retranslateUi(self):
		self.pTitle = QCoreApplication.translate("Program", u"Program" + " " + self.n, None)
		self.bTitle.setText(self.pTitle)
		self.btnGet.setText(QCoreApplication.translate("Program", u"Get", None))
		self.btnSend.setText(QCoreApplication.translate("Program", u"Send", None))

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




