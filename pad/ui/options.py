# -*- coding: utf-8 -*-
from pathlib import Path

from qtpy.QtCore import QDir, QMetaObject
from qtpy.QtWidgets import QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox, \
	QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QSpacerItem, QTabWidget, QTextBrowser, \
	QRadioButton, QPushButton, QVBoxLayout, QStyle, QWidget
from qtpy.QtGui import QDesktopServices, QIcon

from pad.path import FREEPAD_PATH, FREEPAD_ICON_PATH
from pad.freepad_settings import Fsettings
from pad.ui.common import Creator, Debug, tr
from pad.padio import Mid

class FreepadOptionsWindow(QDialog, Creator):
	def __init__(self, fpw, parent = None):
		super().__init__(parent)
		self.setWindowIcon(QIcon(FREEPAD_ICON_PATH))
		self.fpw = fpw

	def setupUi(self, title):
		if not self.objectName():
			self.setObjectName(u"FreepadOptionsWindow")
		self.resize(600, 400)
		self.setMinimumSize(600, 400)
		self._openIcon = 	self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DialogOpenButton"))
		self.title = title
		self.showMidiMessages = True if Fsettings.get('showMidiMessages', True) == "True" else False
		self.noteStyle = int(Fsettings.get('noteStyle', '1'))
		self.defaultDrumsKit = Fsettings.get('lastkits', self._get1stDefault('kits'))
		self.defaultControlsKit = Fsettings.get('lastcontrols', self._get1stDefault('controls'))
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

		self.createObj(u'formLayout', QFormLayout())
		self.createObj(u'lblDrums', QLabel())
		self.formLayout.setWidget(0, QFormLayout.LabelRole, self.lblDrums)
		self.createObj(u'hlDrums', QHBoxLayout())
		self.createObj(u'leDrums', QLineEdit())
		self.leDrums.setText(self.defaultDrumsKit)
		self.createObj(u'btnDrums', QPushButton())
		self.btnDrums.setIcon(self._openIcon)
		self.hlDrums.addWidget(self.leDrums)
		self.hlDrums.addWidget(self.btnDrums)
		self.hlDrums.setStretch(0, 1)
		self.formLayout.setLayout(0, QFormLayout.FieldRole, self.hlDrums)

		self.createObj(u'lblControls', QLabel())
		self.formLayout.setWidget(1, QFormLayout.LabelRole, self.lblControls)
		self.createObj(u'hlControls', QHBoxLayout())
		self.createObj(u'leControls', QLineEdit())
		self.leControls.setText(self.defaultControlsKit)
		self.createObj(u'btnControls', QPushButton())
		self.btnControls.setIcon(self._openIcon)
		self.hlControls.addWidget(self.leControls)
		self.hlControls.addWidget(self.btnControls)
		self.hlControls.setStretch(0, 1)
		self.formLayout.setLayout(1, QFormLayout.FieldRole, self.hlControls)

		MIDI_OUTPUT_PORT = tr('No MIDI output')
		self.createObj(u'lblMidiOutputPort', QLabel())
		self.createObj('cbMidiOutputPort', QComboBox())
		self.cbMidiOutputPort.addItem(MIDI_OUTPUT_PORT)
		for port in Mid.get_output_names():
			self.cbMidiOutputPort.addItem(port)
		self.cbMidiOutputPort.setCurrentText(Fsettings.get('midiOutputPort', MIDI_OUTPUT_PORT))
		self.cbMidiOutputPort.currentTextChanged.connect(self.setMidiOutputPort)
		
		self.formLayout.setWidget(2, QFormLayout.LabelRole, self.lblMidiOutputPort)
		self.formLayout.setWidget(2, QFormLayout.FieldRole, self.cbMidiOutputPort)

		self.vLayoutOptions.addLayout(self.formLayout)

		self.cbToolbar = QCheckBox(self.tabOptions)
		self.cbToolbar.setObjectName(u"cbToolbar")
		self.cbToolbar.setChecked(self.showMidiMessages)
		self.cbToolbar.stateChanged.connect(self.setShowMidiMessages)
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

		self.leDrums.textChanged.connect(lambda t: Fsettings.set('lastkits', t))
		self.leControls.textChanged.connect(lambda t: Fsettings.set('lastcontrols', t))
		self.btnDrums.clicked.connect(lambda e: self.loadKit(u'kits'))
		self.btnControls.clicked.connect(lambda e: self.loadKit(u'controls'))
		self.rbDoremi.toggled.connect(self.setNoteStyle)
		self.tHelp.anchorClicked.connect(self.openLinkInBrowser)
		QMetaObject.connectSlotsByName(self)
	# setupUi

	def retranslateUi(self):
		self.setWindowTitle(tr("Freepad " + self.title + " options", None))
		self.lblDrums.setText(tr(u"Drums kit", None))
		self.lblControls.setText(tr(u"Controls kit", None))
		self.rbDoremi.setText(tr(u"Do Ré Mi", None))
		self.rbCDE.setText(tr(u"C D E ", None))
		self.cbToolbar.setText(tr(u"&Show midi messages", None))
		self.lblMidiOutputPort.setText(tr('Midi output'))
		self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabOptions), tr(u"Options", None))
		self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabHelp), tr(u"Help", None))
		# retranslateUi

	def setNoteStyle(self, note_style):
		Fsettings.set('noteStyle', int(note_style))
		for line in self.fpw.device['layout']:
			for ctl in line:
				if ctl[0:1] != 'p' or ctl == 'pid':
					continue
				pad = self.fpw._controls[ctl]
				pad.noteStyle = note_style
				pad.noteChanged(pad.spNote.value())

	def setMidiOutputPort(self, port_name):
		Fsettings.set('midiOutputPort', port_name)
		self.fpw.io.setMidiOutPort(port_name)

	def setShowMidiMessages(self, val):
		value = (val == 2)
		Fsettings.set('showMidiMessages', str(value))
		if value:
			self.fpw.addStatusBar()
			self.fpw.setFixedSize(self.fpw.sizeHint().width(), self.fpw.vLayout.sizeHint().height() + self.fpw.statusbar.sizeHint().height())
		else:
			self.fpw.removeStatusBar()
			self.fpw.statusbar.deleteLater()
			self.fpw.setFixedSize(self.fpw.sizeHint().width(), self.fpw.vLayout.sizeHint().height())

	def loadKit(self, kit):
		filename = ''
		try:
			filename = self._fileDialog(kit)
			if filename != "":
				lename = 'leDrums' if kit == 'kits' else 'leControls'
				le = getattr(self, lename)
				le.setText(filename)
		except Exception as e:
			Debug.dbg('FreepadOptionsWindow.loadKit unable to read "' + filename + '": ' + str(e))

	def _fileDialog(self, kit):
		filename = ""
		dialog = QFileDialog(self)
		dialog.setFileMode(QFileDialog.ExistingFile)
		dialog.setAcceptMode(QFileDialog.AcceptOpen)
		dialog.setNameFilter("Kit file(*.kit)")
		lastkit = Fsettings.get('last' + kit, self._get1stDefault(kit))
		dialog.setDirectory(QDir(str(Path(lastkit).parent)))
		if dialog.exec():
			filenames = dialog.selectedFiles()
			if len(filenames) > 0:
				filename = dialog.selectedFiles()[0]
		return filename

	def loadHelp(self):
		with open(str(FREEPAD_PATH.joinpath('help').joinpath('freepad.html')), 'r') as fp:
			html = fp.read()
			fp.close()
			self.tHelp.setHtml(html)

	def openLinkInBrowser(self, url):
		if not QDesktopServices.openUrl(url):
			Debug.dbg('Unable to open ' + str(url))

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

