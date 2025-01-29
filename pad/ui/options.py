# -*- coding: utf-8 -*-
from pathlib import Path

from qtpy.QtCore import QCoreApplication, QDir, QMetaObject
from qtpy.QtWidgets import QCheckBox, QDialog, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, \
	QSizePolicy, QSpacerItem, QTabWidget, QTextBrowser, QRadioButton, QPushButton, QVBoxLayout, QStyle, QWidget
from qtpy.QtGui import QDesktopServices, QIcon

from pad.path import FREEPAD_PATH, FREEPAD_ICON_PATH
from pad.ui.common import Creator

class FreepadOptionsWindow(QDialog, Creator):
	def __init__(self, settings, parent = None):
		super().__init__(parent)
		self.settings = settings
		self.setWindowIcon(QIcon(FREEPAD_ICON_PATH))

	def setupUi(self, title):
		if not self.objectName():
			self.setObjectName(u"FreepadOptionsWindow")
		self.resize(600, 400)
		self.setMinimumSize(600, 400)
		self._openIcon = 	self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DialogOpenButton"))
		self.title = title
		self.showMidiMessages = True if self.settings.value('showMidiMessages', True) == "True" else False
		self.noteStyle = int(self.settings.value('noteStyle', '1'))
		self.defaultDrumsKit = self.settings.value('lastkits', self._get1stDefault('kits'))
		self.defaultControlsKit = self.settings.value('lastcontrols', self._get1stDefault('controls'))
		self.setContentsMargins(0, 0, 0, 0)

		self.createObj(u"vLayout", QVBoxLayout(self))
		self.vLayout.setContentsMargins(0, 0, 0, 0)

		self.tabWidget = QTabWidget(self)
		self.tabWidget.setObjectName(u"tabWidget")
		self.tabOptions = QWidget()
		self.tabOptions.setObjectName(u"tabOptions")
		self.vLayoutOptions = QVBoxLayout(self.tabOptions)
		self.vLayoutOptions.setObjectName(u"vLayoutOptions")
		self.hLayout = QHBoxLayout()
		self.hLayout.setObjectName(u"hLayout")
		
		self.horizontalSpacer = QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		self.hLayout.addItem(self.horizontalSpacer)

		self.vLayoutOptions.addLayout(self.hLayout)

		self.createObj(u'flPaths', QFormLayout())
		self.createObj(u'lblDrums', QLabel())
		self.flPaths.setWidget(0, QFormLayout.LabelRole, self.lblDrums)
		self.createObj(u'hlDrums', QHBoxLayout())
		self.createObj(u'leDrums', QLineEdit())
		self.leDrums.setText(self.defaultDrumsKit)
		self.createObj(u'btnDrums', QPushButton())
		self.btnDrums.setIcon(self._openIcon)
		self.hlDrums.addWidget(self.leDrums)
		self.hlDrums.addWidget(self.btnDrums)
		self.hlDrums.setStretch(0, 1)
		self.flPaths.setLayout(0, QFormLayout.FieldRole, self.hlDrums)

		self.createObj(u'lblControls', QLabel())
		self.flPaths.setWidget(1, QFormLayout.LabelRole, self.lblControls)
		self.createObj(u'hlControls', QHBoxLayout())
		self.createObj(u'leControls', QLineEdit())
		self.leControls.setText(self.defaultControlsKit)
		self.createObj(u'btnControls', QPushButton())
		self.btnControls.setIcon(self._openIcon)
		self.hlControls.addWidget(self.leControls)
		self.hlControls.addWidget(self.btnControls)
		self.hlControls.setStretch(0, 1)
		self.flPaths.setLayout(1, QFormLayout.FieldRole, self.hlControls)

		self.vLayoutOptions.addLayout(self.flPaths)

		self.gbNoteStyle = QGroupBox("&Note style")
		self.gbNoteStyle.setStyleSheet("QGroupBox:title {margin-left:15px; margin-top:12px; background-color:transparent}")
		self.vLayoutNoteStyle = QVBoxLayout()
		self.vLayoutNoteStyle.setObjectName(u"vLayoutNoteStyle")
		self.rbDoremi = QRadioButton(self.tabOptions)
		self.rbDoremi.setObjectName(u"rbDoremi")
		self.rbDoremi.setChecked(bool(self.noteStyle == 1))
		self.vLayoutNoteStyle.addWidget(self.rbDoremi)
		self.rbCDE = QRadioButton(self.tabOptions)
		self.rbCDE.setObjectName(u"rbCDE")
		self.rbCDE.setChecked(not bool(self.noteStyle == 1))
		self.vLayoutNoteStyle.addWidget(self.rbCDE)
		self.gbNoteStyle.setLayout(self.vLayoutNoteStyle)
		self.vLayoutOptions.addWidget(self.gbNoteStyle)

		self.cbToolbar = QCheckBox(self.tabOptions)
		self.cbToolbar.setObjectName(u"cbToolbar")
		self.cbToolbar.setChecked(self.showMidiMessages)
		self.vLayoutOptions.addWidget(self.cbToolbar)

		self.verticalSpacer = QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
		
		self.vLayoutOptions.addItem(self.verticalSpacer)
		
		self.tabWidget.addTab(self.tabOptions, "")
		self.tabHelp = QWidget()
		self.tabHelp.setObjectName(u"tabHelp")
		self.vLayoutHelp = QVBoxLayout(self.tabHelp)
		self.vLayoutHelp.setObjectName(u"vLayoutHelp")
		self.vLayoutHelp.setContentsMargins(0, 0, 0, 0)
		self.tHelp = QTextBrowser(self.tabHelp)
		self.tHelp.setObjectName(u"tHelp")
		self.tHelp.setStyleSheet("background-color: transparent; border: none;")
		self.tHelp.setOpenLinks(False)
		self.tHelp.setSearchPaths([str(FREEPAD_PATH.joinpath('help'))])
		self.vLayoutHelp.addWidget(self.tHelp)
		self.tabWidget.addTab(self.tabHelp, "")
		self.loadHelp()
		
		self.vLayout.addWidget(self.tabWidget)

		self.retranslateUi()
		
		self.tabWidget.setCurrentIndex(0)

		self.leDrums.textChanged.connect(lambda t: self.settings.setValue('lastkits', t))
		self.leControls.textChanged.connect(lambda t: self.settings.setValue('lastcontrols', t))
		self.btnDrums.clicked.connect(lambda e: self.loadKit(u'kits'))
		self.btnControls.clicked.connect(lambda e: self.loadKit(u'controls'))
		self.rbDoremi.toggled.connect(lambda b : self.settings.setValue('noteStyle', int(b)))
		self.cbToolbar.stateChanged.connect(lambda v : self.settings.setValue('showMidiMessages', str(v == 2)))
		self.tHelp.anchorClicked.connect(self.openLinkInBrowser)
		QMetaObject.connectSlotsByName(self)
	# setupUi

	def retranslateUi(self):
		self.setWindowTitle(QCoreApplication.translate("FrrepadOptions", "Freepad " + self.title + " options", None))
		self.lblDrums.setText(QCoreApplication.translate("FrrepadOptions", u"Drums kit", None))
		self.lblControls.setText(QCoreApplication.translate("FrrepadOptions", u"Controls kit", None))
		self.rbDoremi.setText(QCoreApplication.translate("FrrepadOptions", u"Do Ré Mi", None))
		self.rbCDE.setText(QCoreApplication.translate("FrrepadOptions", u"C D E ", None))
		self.cbToolbar.setText(QCoreApplication.translate("FrrepadOptions", u"&Show midi messages", None))
		self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabOptions), QCoreApplication.translate("Dialog", u"Options", None))
		self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabHelp), QCoreApplication.translate("Dialog", u"Help", None))
		# retranslateUi

	def loadKit(self, kit):
		filename = ''
		try:
			filename = self._fileDialog(kit)
			if filename != "":
				lename = 'leDrums' if kit == 'kits' else 'leControls'
				le = getattr(self, lename)
				le.setText(filename)
		except Exception as e:
			print('FreepadOptionsWindow.loadKit unable to read "' + filename + '": ' + str(e))

	def _fileDialog(self, kit):
		filename = ""
		dialog = QFileDialog(self)
		dialog.setFileMode(QFileDialog.ExistingFile)
		dialog.setAcceptMode(QFileDialog.AcceptOpen)
		dialog.setNameFilter("Kit file(*.kit)")
		lastkit = self.settings.value('last' + kit, self._get1stDefault(kit))
		dialog.setDirectory(QDir(str(Path(lastkit).parent)))
		if dialog.exec():
			filenames = dialog.selectedFiles()
			if len(filenames) > 0:
				filename = dialog.selectedFiles()[0]
		return filename

	def loadHelp(self):
		with open("pad/help/freepad.html", "r") as fp:
			html = fp.read()
			fp.close()
			self.tHelp.setHtml(html)

	def openLinkInBrowser(self, url):
		#url = QUrl(url)
		#print(str(url))
		if not QDesktopServices.openUrl(url):
			print('Unable to open ' + str(url))

	def _get1stDefault(self, d):
		path = FREEPAD_PATH.joinpath('midi').joinpath(d)
		if not path.is_dir():
			return False
		for k in path.iterdir():
			fp = path.joinpath(k)
			if not fp.is_file():
					continue
			break
		return str(fp)

