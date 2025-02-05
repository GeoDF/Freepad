from qtpy.QtCore import QCoreApplication, QMetaObject, Signal
from qtpy.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QWidget

from pad.path import imgUrl

FREEPAD_TITLE_COLOR = '#dfdddd'
FREEPAD_NOTE_COLOR = '#cfffff'
FREEPAD_BORD_COLOR = '#441200'
FREEPAD_LGRADIENT = 'qlineargradient(spread:reflect, x1:1, y1:0.5, x2:1, y2:1, stop:0 #171719, stop:1 #080808);'
FREEPAD_RGRADIENT = 'qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 #080808, stop:1 #171719)'
FREEPAD_RGRADIENT_OVER = 'qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 #280808, stop:1 #171719)'
FREEPAD_TOOLTIPS = False # tooltips needs improvements !

class PadException(Exception):
	def __init__(self, err):
		super().__init__(err)
		print(err)

class Creator():
	# Create object of class cls called name
	def createObj(self, name, cls):
		setattr(self, name, cls)
		w = getattr(self, name)
		w.setObjectName(name)
		return w

class Spinput(QWidget, Creator):
	valueChanged = Signal(int)

	def setupUi(self, name, label):
		self.name = name
		self.label = label

		self.createObj(u'hl', QHBoxLayout(self))
		self.hl.setContentsMargins(0, 0, 0, 0)

		self.createObj(u'lbl', QLabel(self))
		self.lbl.setText(self.label)
		if FREEPAD_TOOLTIPS:
			self.lbl.setToolTip(self.name)
		self.hl.addWidget(self.lbl)
		self.spin = self.createObj(name, QSpinBox(self.parent()))
		arrow_size = 'width: 7px; height: 7px';
		self.spin.setStyleSheet('''
QSpinBox {
	padding-left:5px; padding-right:5px;
	background: transparent;
	border: 1px inset #171719;
	border-radius: 3px;
}
QSpinBox:hover {
	border: 1px inset ''' + FREEPAD_BORD_COLOR + ''';
}
QSpinBox:focus {
	border-color: ''' + FREEPAD_BORD_COLOR + ''';
	selection-color: #ff3800;
	selection-background-color: #001828;
	color: #ff2800;
}
QSpinBox::up-button:focus {
	subcontrol-origin: border; subcontrol-position: top right;
	border-image: url("''' + imgUrl('spinup.png') + '''"); ''' + arrow_size + ''';
	margin-top: 4px; margin-right: 4px;
}
QSpinBox::up-button:focus:hover {
	border-image: url("''' + imgUrl('spinup_hover.png') + '''");
}
QSpinBox::up-button:focus:pressed {
	border-image: url("''' + imgUrl('spinup_pressed.png') +'''");
}
QSpinBox::down-button:focus {
	subcontrol-origin: border; subcontrol-position: bottom right;
	border-image: url("''' + imgUrl('spindown.png') +'"); ''' + arrow_size + ''';
	margin-bottom: 4px; margin-right: 4px;
}
QSpinBox::down-button:focus:hover {
	border-image: url("''' + imgUrl('spindown_hover.png') + '''");
}
QSpinBox::down-button:focus:pressed {
	border-image: url("''' + imgUrl('spindown_pressed.png') + '''");
}
QSpinBox::up-arrow:focus:disabled, QSpinBox::up-arrow:focus:off {'''	+ arrow_size + ''';
	image: url("''' + imgUrl('spinup_disabled.png') + '''");
}
QSpinBox::down-arrow:focus:disabled, QSpinBox::down-arrow:focus:off {'''	+ arrow_size + ''';
	image: url("''' + imgUrl('spindown_disabled.png') +'''");
}''')

		self.spin.setMinimum(0)
		self.spin.setMaximum(127)
		self.spin.setAccelerated(True)
		self.hl.addWidget(self.spin)

		self.spin.valueChanged.connect(lambda v: self.valueChanged.emit(v))
		QMetaObject.connectSlotsByName(self)

	def value(self):
		return self.spin.value()

def tr(txt, disambiguation = None):
	return QCoreApplication.translate('Freepad', txt, disambiguation)

