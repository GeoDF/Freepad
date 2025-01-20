from qtpy.QtCore import QMetaObject, Signal
from qtpy.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QWidget

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
		if not self.objectName():
			self.setObjectName(u"Spinput")

		self.name = name
		self.label = label

		self.createObj(u"hl", QHBoxLayout(self))
		self.hl.setContentsMargins(0, 0, 0, 0)

		self.createObj(u"lbl", QLabel(self))
		self.lbl.setText(self.label)
		#if QT_CONFIG(tooltip)
		self.lbl.setToolTip(self.name)
		#endif // QT_CONFIG(tooltip)
		self.hl.addWidget(self.lbl)
		self.spin = QSpinBox()
		self.spin.setObjectName(name)
		arrow_size = "width: 7px; height: 7px";
		self.spin.setStyleSheet("QSpinBox {padding-left:5px; padding-right:5px; background: transparent; border: 1px inset #171719; border-radius: 3px}"
"QSpinBox:hover {border: 1px inset #441200}"
"QSpinBox:focus {border-color: #441200; selection-color: #ff3800; selection-background-color: #001828; color: #ff2800}"
"QSpinBox::up-button:focus {subcontrol-origin: border; subcontrol-position: top right; border-image: url(pad/ui/img/spinup.png); " + arrow_size + "; margin-top: 4px; margin-right: 4px;}"
"QSpinBox::up-button:focus:hover {border-image: url(pad/ui/img/spinup_hover.png);}"
"QSpinBox::up-button:focus:pressed {border-image: url(pad/ui/img/spinup_pressed.png);}"
"QSpinBox::down-button:focus {subcontrol-origin: border; subcontrol-position: bottom right; border-image: url(pad/ui/img/spindown.png); " + arrow_size + "; margin-bottom: 4px; margin-right: 4px;}"
"QSpinBox::down-button:focus:hover {border-image: url(pad/ui/img/spindown_hover.png);}"
"QSpinBox::down-button:focus:pressed {border-image: url(pad/ui/img/spindown_pressed.png);}"
"QSpinBox::up-arrow:focus:disabled, QSpinBox::up-arrow:focus:off {" + arrow_size + ";image: url(pad/ui/img/spinup_disabled.png);}"
"QSpinBox::down-arrow:focus:disabled, QSpinBox::down-arrow:focus:off {" + arrow_size + "; image: url(pad/ui/img/spindown_disabled.png);}"
)

		self.spin.setMinimum(0)
		self.spin.setMaximum(127)
		self.spin.setAccelerated(True)
		self.hl.addWidget(self.spin)

		self.spin.valueChanged.connect(lambda v: self.valueChanged.emit(v))
		QMetaObject.connectSlotsByName(self)

	def value(self):
		return self.spin.value()