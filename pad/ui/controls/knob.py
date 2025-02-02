from qtpy.QtCore import QCoreApplication, QLineF, QMetaObject, QRectF, QPointF, QSize, Qt, Signal
from qtpy.QtWidgets import QComboBox, QDial, QStyleOptionSlider, QVBoxLayout, QWidget
from qtpy.QtGui import QBrush, QColor, QRadialGradient, QPainter, QPen

from pad.ui.common import Creator, Spinput

class Knob(QWidget, Creator):
	sendControlChanged = Signal(int, int, int)
	
	def __init__(self, title, parent = None):
		super().__init__(parent)
		self.kTitle = title
		self.midi_controls = {}
		self.mc = 16

	def setupUi(self, params):
		subcontrols = {}
		for p in params:
			setattr(self, p, params[p])

		self.setStyleSheet("Knob #cbName {"
"background: transparent;"
"}"
"Knob #cbName QListView {"
"min-width: 150px;"
"border: 1px inset #441200; border-radius: 3px; border-top-left-radius: 0;"
"}"
)

		self.createObj(u"knobLW", QWidget(self))
		self.createObj(u"verticalLayout", QVBoxLayout())
		self.knobLW.setLayout(self.verticalLayout)
		self.verticalLayout.setContentsMargins(5, 5, 5, 5)
		self.verticalLayout.setSpacing(3)

		self.createObj(u"pot", Potard())
		self.pot.setFixedSize(60, 60)
		self.verticalLayout.addWidget(self.pot, alignment = Qt.AlignmentFlag.AlignCenter)

		self.createObj(u"cbName", QComboBox())
		self.cbName.setEditable(True)
		self.cbName.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.cbName.addItem(u"K " + self.kTitle)
		if self.midi_controls is not None:
			for cc in self.midi_controls:
				self.cbName.addItem(self.midi_controls[cc])
		self.cbName.setMaximumWidth(120)
		self.verticalLayout.addWidget(self.cbName)

		ctlname = 'k' + self.kTitle + '_cc'
		self.spCC = Spinput()
		self.spCC.setupUi(ctlname, QCoreApplication.translate("Knob", u"CC", None))
		self.verticalLayout.addWidget(self.spCC)
		subcontrols[ctlname] = self.spCC.spin

		ctlname = 'k' + self.kTitle + '_lo'
		self.spLO = Spinput()
		self.spLO.setupUi(ctlname, QCoreApplication.translate("Knob", u"LO", None))
		self.verticalLayout.addWidget(self.spLO)
		subcontrols[ctlname] = self.spLO.spin

		ctlname = 'k' + self.kTitle + '_hi'
		self.spHI = Spinput()
		self.spHI.setupUi(ctlname, QCoreApplication.translate("Knob", u"HI", None))
		self.verticalLayout.addWidget(self.spHI)
		subcontrols[ctlname] = self.spHI.spin

		if self.mc < 16:
			ctlname = 'k' + self.kTitle + '_mc'
			self.cbMC = self.createObj(ctlname, QComboBox(self.knobLW))
			for ch in range(1,17):
				sp = "  " if ch < 10 else ""
				self.cbMC.addItem(sp + str(ch))
			self.cbMC.addItem("Global")
			self.cbMC.setCurrentIndex(16)
			self.mc = 16
			self.cbMC.currentIndexChanged.connect(lambda i: print(str(i)))
			self.verticalLayout.addWidget(self.cbMC)
			subcontrols[ctlname] = self.cbMC

		self.setFixedSize(self.knobLW.sizeHint())

		self.retranslateUi(Knob)
		
		self.cbName.currentIndexChanged.connect(self.ccChanged)
		self.pot.valueChanged.connect(lambda v: self.sendControlChanged.emit(self.mc, self.spCC.value(), v))
		QMetaObject.connectSlotsByName(self)
		
		return subcontrols

	def retranslateUi(self, Knob):
		self.cbName.lineEdit().setText(QCoreApplication.translate("Knob", u"K " + self.kTitle, None))

	def setValue(self, val):
		val = (int(val) - self.spLO.value()) * 127 / (self.spHI.value() - self.spLO.value() + 0.000000000001)
		self.pot.setValue(int(val))

	def ccChanged(self, index):
		if index > 0:
			ccn = self.cbName.itemText(index)
			cc = [cc for cc, i in self.midi_controls.items() if i == ccn][0]
			self.spCC.spin.setValue(cc)

# Custon QDial subclass by geomaticien
class Potard(QDial):
	buttonBgColor1 = QColor("#080808")
	buttonBgColor2 = QColor("#202022")
	needleColor = QColor("#bfbfbf")

	def __init__(self, parent = None):
		super().__init__(parent)

		self.setMinimum(0)
		self.setMaximum(127)
		self.setNotchTarget(36)
		self.setNotchesVisible(True)
		self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

	def paintEvent(self, event):
		# create a QStyleOption for the dial, and initialize it with the basic properties
		# that will be used for the configuration of the painter
		opt = QStyleOptionSlider()
		self.initStyleOption(opt)
		# construct a QRectF that uses the minimum between width and height, 
		# and adds some margins for better visual separation
		# this is partially taken from the fusion style helper source
		width = opt.rect.width()
		height = opt.rect.height()
		r = min(width, height) / 2
		r -= r / 50
		d_ = r / 6
		dx = opt.rect.x() + d_ + (width - 2 * r) / 2 + 1
		dy = opt.rect.y() + d_ + (height - 2 * r) / 2 + 1
		br = QRectF(dx + .5, dy + .5, 
				int(r * 2 - 2 * d_ - 2), 
				int(r * 2 - 2 * d_ - 2))

		qp = QPainter(self)
		qp.setRenderHints(qp.Antialiasing)

		for angle in range(240, -90, -30):
			l1 = QLineF.fromPolar(r * 0.9, angle)
			l1.translate(br.center())
			l2 = QLineF.fromPolar(r * 1, angle)
			l2.translate(br.center())
			l = QLineF(l1.p2(), l2.p2())
			qp.setPen(QPen(self.needleColor, 2))
			qp.drawLine(l)

		# find the "real" value ratio between minimum and maximum
		realValue = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
		# compute the angle at which the dial handle should be placed, assuming
		# a range between 240° and 300° (moving clockwise)
		angle = 240 - 300 * realValue

		line = QLineF.fromPolar(r * .6, angle)
		line.translate(br.center())

		fp = line.p2()
		bgradient = QRadialGradient(QPointF(r, r), r * .6, fp)
		bgradient.setColorAt(0, self.buttonBgColor1)
		bgradient.setColorAt(1, self.buttonBgColor2)
		pgradient = QRadialGradient(QPointF(r, r), r, fp)
		pgradient.setColorAt(0, self.buttonBgColor2)
		pgradient.setColorAt(1, self.buttonBgColor1)
		qp.setBrush(QBrush(bgradient))
		qp.setPen(QPen(pgradient, 8))
		qp.drawEllipse(br)

		line = QLineF.fromPolar(r * .6, angle)
		line.translate(br.center())
		qp.setPen(QPen(self.needleColor, 5))
		qp.drawLine(line)



	