import mido
import mido.backends.rtmidi

from qtpy.QtCore import QObject, QTimer, Signal

from pad.freepad_settings import Fsettings
from pad.ui.common import Debug, tr

class Mid(object):
	@staticmethod
	def get_input_names():
		try:
			return mido.get_input_names()
		except:
			return []

	@staticmethod
	def get_output_names():
		try:
			return mido.get_output_names()
		except:
			return []

	# the midiname format depends on OS
	@staticmethod
	def shortMidiName(longname):
		if ':' in longname: # Linux
			longname = longname[0:longname.index(':')]
		elif ' ' in longname: # evil OS
			longname = longname[0:longname.rindex(' ')]
		return longname

	@staticmethod
	def open_input(midiname):
		try:
			return mido.open_input(midiname, False)
		except Exception as e:
			Debug.dbg('Unable to open ' + midiname + ': ' + str(e))
			return None
	
	@staticmethod
	def open_output(midiname):
		try:
			return mido.open_output(midiname, False)
		except Exception as e:
			Debug.dbg('Unable to open ' + midiname + ': ' + str(e))
			return None

class PadIO(QObject):
	receivedMidi = Signal(str)
	devicePlugged = Signal()
	deviceUnplugged  = Signal()

	def __init__(self, pad, parent = None):
		super().__init__(parent)
		self.pad = pad
		self.program = []
		if 'program' in pad:
			program = pad["program"]
			for i in range(0, len(program)):
				ctlname = program[i]
				if ctlname[0] == 'p' and ctlname != 'pid':
					pad_vars = pad['pad']
					for v in range(0, len(pad_vars)):
						self.program.append(ctlname + '_' + pad_vars[v])
				elif ctlname[0] == 'k':
					knob_vars = pad['knob']
					for v in range(0, len(knob_vars)):
						self.program.append(ctlname + '_' + knob_vars[v])
				else:
					self.program.append(ctlname)
		self.isConnected = False
		self.in_port = None
		self.out_port = None
		self.mtout_port = None
		self.in_names = [Mid.get_input_names()] # BEFORE starting mcTimer

		# midi event
		self.meTimer = QTimer(self)
		self.meTimer.setInterval(8)
		self.meTimer.timeout.connect(self.listenMessages)

		# midi connection
		self.mcTimer = QTimer(self)
		self.mcTimer.setInterval(250)
		self.mcTimer.timeout.connect(self.listenMidiConnections)
		self.listenMidiConnections()
		self.mcTimer.start()

		if not self.isConnected:
			self.openDevicePorts() # Required for virtual pads ONLY (cannot open ports twice)

	def listenMessages(self):
		if not self.in_port is None:
			for msg in self.in_port.iter_pending():
				if msg is not None:
					self.receivedMidi.emit(str(msg))

	def listenMidiConnections(self):
		m_in = Mid.get_input_names()
		if not m_in == self.in_names:
			for device in m_in:
				if Mid.shortMidiName(device) == self.pad['midiname'].upper():
					self.openDevicePorts()
					self.in_names = Mid.get_input_names()
					self.meTimer.start()
					self.isConnected = True
					self.devicePlugged.emit()
					return
			for device in self.in_names:
				if Mid.shortMidiName(device) == self.pad['midiname'].upper():
					self.closeDevicePorts()
					self.meTimer.stop()
					self.isConnected = False
					self.deviceUnplugged.emit()
		self.in_names = Mid.get_input_names()

	def openDevicePorts(self):
		in_midiname = self._find_pad_port("in")
		out_midiname = self._find_pad_port("out")
		if in_midiname in Mid.get_input_names():
			self.in_port = Mid.open_input(in_midiname)
		if out_midiname in Mid.get_output_names():
			self.out_port = Mid.open_output(out_midiname)
		MIDI_OUTPUT_PORT = Fsettings.get('midiOutputPort', tr('No MIDI output'))
		try:
			for name in Mid.get_output_names():
				if MIDI_OUTPUT_PORT in name:
					self.setMidiOutPort(name)
		except Exception as e:
			Debug.dbg('Unable to connect Freepad to "' + MIDI_OUTPUT_PORT + '. ' + str(e))

	def setMidiOutPort(self, port_name):
		try:
			self.mtout_port.close()
		except:
			pass
		self.mtout_port = Mid.open_output(port_name)

	def closeDevicePorts(self):
		self.meTimer.stop()
		try:
			self.in_port.close()
			self.out_port.close()
			self.in_port = None
			self.out_port = None
		except Exception as e:
			#Debug.dbg('Error in closeDevicePorts: ' + str(e))
			pass
		self.isConnected = False

	def _find_pad_port(self, op):
		midiname = self.pad['midiname']
		if midiname == '':
			return None
		try:
			if op == "in":
				dev_names: list[str] = [dev for dev in Mid.get_input_names()]
			elif op == "out":
				dev_names: list[str] = [dev for dev in Mid.get_output_names()]
			else:
				return None
			for name in dev_names:
					if midiname.upper() in name.upper():
							return name
			return None
		except Exception as e:
			Debug.dbg("Error in _find_pad: " + str(e))

	def close(self):
		self.closeDevicePorts()

	# Request for the program n° nb
	def getProgram(self, nb):
		try:
			data = self.pad['get_program'].replace('pid', str(nb)).split(",")
			data = [int(h, 16) for h in data]
		except Exception as e:
			Debug.dbg('Bad "get_program" value in the JSON file: ' + str(e))
		if not self.out_port is None:
			try:
				self.out_port.send(mido.Message('sysex', data = data))
			except Exception as e:
				Debug.dbg('Unable to request program ' + str(nb) + ': ' + str(e))

	def sendProgram(self, pid, program):
		if not self.out_port is None:
			data = self.pad["send_program"].replace('pid', str(pid)).split(",")
			program = data + program[1:]
			for i in range(0, len(data)):
				program[i] = int(data[i], 16)
			m = mido.Message("sysex", data = program)
			self.out_port.send(m)
			return str(m)

	def sendNoteOn(self, channel, note, velocity):
		if channel in range(0,16) and note in range(0,128):
			return self.sendNoteMessage(channel, note, velocity, "on")

	def sendNoteOff(self, channel, note, velocity):
		if channel in range(0,16) and note in range(0,128):
			return self.sendNoteMessage(channel, note, velocity, "off")

	def sendNoteMessage(self, channel, note, velocity, msg):
		if self.mtout_port is not None:
			m = mido.Message("note_" + msg, channel = channel, note = note, velocity = velocity)
			self.mtout_port.send(m)
			return str(m)[0:-7]

	def sendControlChange(self, channel, cc, val):
		if self.mtout_port is not None:
			m = mido.Message("control_change", channel = channel, control = cc, value = val)
			self.mtout_port.send(m)
			return str(m)[0:-7]

	def sendProgramChange(self, channel, pc):
		if self.mtout_port is not None:
			m = mido.Message("program_change", channel = channel, program = pc)
			self.mtout_port.send(m)
			return str(m)[0:-7]


