import mido
import mido.backends.rtmidi

from qtpy.QtCore import QObject, QThread, QTimer, Signal

from pad.ui.common import tr

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

	def __init__(self, pad, midiname : str, settings, parent = None):
		super().__init__(parent)
		self.pad = pad
		self.midiname = midiname
		self.settings = settings
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
		self.openDevicePorts(self._find_pad("in"), self._find_pad("out"))

	def openDevicePorts(self, in_midiname, out_midiname):
		if in_midiname in Mid.get_input_names():
			self.in_port = Mid.open_input(in_midiname)
		if out_midiname in Mid.get_output_names():
			self.out_port = Mid.open_output(out_midiname)
		if (self.in_port is not None) and (self.out_port is not None):
			try:
				self.midiListenerThread = QThread(self)
				self.midiListener = MidiListener(self.in_port)
				self.midiListener.moveToThread(self.midiListenerThread)
				self.midiListener.gotMessage.connect(lambda msg: self.receivedMidi.emit(msg))
				self.midiListenerThread.started.connect(self.midiListener.run)
				self.midiListenerThread.start()
				self.isConnected = self.midiListenerThread.isRunning()
			except Exception as e:
				print('Error in openDevicePorts: ' + str(e))
		MIDI_OUTPUT_PORT = self.settings.value('midiOutputPort', tr('No MIDI output'))
		try:
			for name in Mid.get_output_names():
				if MIDI_OUTPUT_PORT in name:
					self.mtout_port = Mid.open_output(name)
		except Exception as e:
			print('Unable to connect Freepad to "' + MIDI_OUTPUT_PORT + '. ' + str(e))


	def closeDevicePorts(self):
		try: 
			self.midiListener.stop()
			self.in_port.close()
			self.out_port.close()
			self.in_port = None
			self.out_port = None
		except Exception as e:
			pass
			#print('Error in closeDevicePorts:' + str(e))
		self.isConnected = False

	def _find_pad(self, op):
		if self.midiname == '':
			return None
		try:
			if op == "in":
				dev_names: list[str] = [dev for dev in Mid.get_input_names()]
			elif op == "out":
				dev_names: list[str] = [dev for dev in Mid.get_output_names()]
			else:
				return None
			for name in dev_names:
					if self.midiname.lower() in name.lower():
							return name
			return None
		except Exception as e:
			print("Error in _find_pad: " + str(e))

	def close(self):
		self.closeDevicePorts()
		#self.mtout_port.close()

	# Reuest for the program n° nb. Response read by MidiListener and received by ui
	def getProgram(self, nb):
		try:
			data = self.pad['get_program'].replace('pid', str(nb)).split(",")
			data = [int(h, 16) for h in data]
		except Exception as e:
			print('Bad "get_program" value in the JSON file: ' + str(e))
		try:
			self.out_port.send(mido.Message('sysex', data = data))
		except Exception as e:
			print('Unable to request program ' + str(nb) + ': ' + str(e))

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

	def listenMessages(self):
		for msg in self.in_port.iter_pending():
			if msg is not None:
				self.gotMessage.emit(str(msg))

	def stop(self):
		self.timer.stop()
		del self.timer
		self.thread().quit()


class MidiConnectionListener(QObject):
	devicePlugged = Signal(dict)
	deviceUnplugged  = Signal(dict)

	def __init__(self, knownPadsNames, parent = None):
		super().__init__(parent)
		self.timer = QTimer(self)
		self.timer.setInterval(250)
		self.timer.timeout.connect(self.listenMidiConnections)
		self.in_names = Mid.get_input_names()
		self.out_names = Mid.get_output_names()
		self.knownPadsNames = knownPadsNames

	def run(self):
		self.timer.start()

	def cancel(self):
		self.timer.stop()
		del self.timer
		self.deleteLater()
		self.thread().quit()

	def listenMidiConnections(self):
		_changed = False
		m_in = Mid.get_input_names()
		m_out = Mid.get_output_names()
		in_added, in_removed, out_added, out_removed = [], [], [], []
		if m_in != self.in_names:
			in_added, in_removed = self._compareLists(self.in_names, m_in)
			self.in_names = m_in
			_changed = True
		if m_out != self.out_names:
			out_added, out_removed = self._compareLists(self.out_names, m_out)
			self.out_names = m_out
			_changed = True
		if _changed:
			if (len(in_added) > 0) and (len(out_added)) > 0:
				self.devicePlugged.emit({'in': in_added, 'out': out_added})
			if len(in_removed) > 0 and len(out_removed) > 0:
				self.deviceUnplugged.emit({'in': in_removed, 'out': out_removed})

	def _compareLists(self, old, new):
		new_set = sorted(new)
		old_set = sorted(old)
		added, deleted = [], []
		i, j = 0, 0
		j_max = len(old_set)
		i_max = len(new_set)
		while True:
			if i == i_max and j == j_max:
					return added, deleted
					break
			if j == j_max:
					#added.append(new_set[i])
					self._appendIfKnown(added, new_set[i])
					i += 1
					continue
			if i == i_max:
					#deleted.append(old_set[j])
					self._appendIfKnown(deleted, old_set[j])
					j += 1
					continue
			if new_set[i] < old_set[j]:
					#added.append(new_set[i])
					self._appendIfKnown(added, new_set[i])
					i += 1
					continue
			if new_set[i] == old_set[j]:
					i += 1
					j += 1
					continue
			if new_set[i] > old_set[j]:
					#deleted.append(old_set[j])
					self._appendIfKnown(deleted, old_set[j])
					j += 1
					continue

	def _appendIfKnown(self, lst : list, val : str):
		if Mid.shortMidiName(val) in self.knownPadsNames:
			lst.append(val)

