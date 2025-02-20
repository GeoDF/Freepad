import mido
import mido.backends.rtmidi

from qtpy.QtCore import QObject, QThread, QTimer, Signal

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
		except:
			return None
	
	@staticmethod
	def open_output(midiname):
		try:
			return mido.open_output(midiname, False)
		except:
			return None

class PadIO(QObject):
	receivedMidi = Signal(str)

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
		self.midiListenerThread = QThread(self)
		self.openDevicePorts()

	def openDevicePorts(self):
		in_midiname = self._find_pad_port("in")
		out_midiname = self._find_pad_port("out")
		if in_midiname in Mid.get_input_names():
			self.in_port = Mid.open_input(in_midiname)
		if out_midiname in Mid.get_output_names():
			self.out_port = Mid.open_output(out_midiname)
		if (self.in_port is not None) and (self.out_port is not None):
			try:
				#self.midiListenerThread = QThread(self)
				self.midiListener = MidiListener(self.in_port)
				self.midiListener.moveToThread(self.midiListenerThread)
				self.midiListener.gotMessage.connect(lambda msg: self.receivedMidi.emit(msg))
				self.midiListenerThread.started.connect(self.midiListener.run)
				self.midiListenerThread.start()
				self.isConnected = self.midiListenerThread.isRunning()
			except Exception as e:
				Debug.dbg('Error in openDevicePorts: ' + str(e))
		else:
			Debug.dbg('Unable to open "' + str(in_midiname) + '"')
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
		if getattr(self, 'midiListenerThread'):
			self.midiListenerThread.quit()
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

	# Reuest for the program n° nb. Response read by MidiListener and received by ui
	def getProgram(self, nb):
		try:
			data = self.pad['get_program'].replace('pid', str(nb)).split(",")
			data = [int(h, 16) for h in data]
		except Exception as e:
			Debug.dbg('Bad "get_program" value in the JSON file: ' + str(e))
		try:
			self.out_port.send(mido.Message('sysex', data = data))
		except Exception as e:
			Debug.dbg('Unable to request program ' + str(nb) + ': ' + str(e))

	def sendProgram(self, pid, program):
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

	def sendControlChanged(self, channel, cc, val):
		if self.mtout_port is not None:
			m = mido.Message("control_change", channel = channel, control = cc, value = val)
			self.mtout_port.send(m)
			return str(m)[0:-7]

class MidiListener(QObject):
	gotMessage = Signal(str)

	def __init__(self, in_port, parent = None):
		super().__init__(parent)
		self.in_port = in_port
		self.timer = QTimer(self) # Using a timer preserve from freezing GUI
		self.timer.setInterval(8)
		self.timer.timeout.connect(self.listenMessages)

	def run(self):
		self.timer.start()
		Debug.dbg('Started midi events listener on port "' + str(self.in_port.name) + '"')

	def listenMessages(self):
		for msg in self.in_port.iter_pending():
			if msg is not None:
				self.gotMessage.emit(str(msg))

	def stop(self):
		print('MidiListener.stop called')
		self.timer.stop()
		del self.timer
		self.thread().quit()


class MidiConnectionListener(QObject):
	devicePlugged = Signal()
	deviceUnplugged  = Signal()

	def __init__(self, io, parent = None):
		super().__init__(parent)
		self.io = io
		self.deviceName = io.pad['midiname']
		self.timer = QTimer(self)
		self.timer.setInterval(250)
		self.timer.timeout.connect(self.listenMidiConnections)
		self.in_names = Mid.get_input_names()

	def run(self):
		self.timer.start()
		Debug.dbg('Started connection listener for "' + str(self.deviceName) + '"')

	def cancel(self):
		self.timer.stop()
		del self.timer
		self.deleteLater()
		self.thread().quit()

	def listenMidiConnections(self):
		m_in = Mid.get_input_names()
		if not m_in == self.in_names:
			for device in m_in:
				if Mid.shortMidiName(device) == self.deviceName.upper():
					self.io.openDevicePorts()
					self.in_names = Mid.get_input_names()
					self.devicePlugged.emit()
					return
			for device in self.in_names:
				if Mid.shortMidiName(device) == self.deviceName.upper():
					self.io.closeDevicePorts()
					self.deviceUnplugged.emit()
		self.in_names = Mid.get_input_names()

