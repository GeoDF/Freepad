# Freepad
Free editor for Akai LPD8 midi pads controller

![freepad_01](https://github.com/user-attachments/assets/eb0b693f-c8a3-45e3-877e-59fe53157667)

Features:
- Virtual pad : send MIDI notes and control change messages.
- Get and send programs from and to your LPD8.
- Load and save programs from and to your computer (with instruments names).
- Show MIDI messages sent by LPD8.
- Display a visual feedback.
- Display instrument names corresponding to notes in drum kits.
- switch automatically betwwen the virtual pad mode and the editor mode when you plug/unplug your LPD8.

IMPORTANT NOTES: the LPD8 pad device have 4 programs, and the computer is not advised when you change the program used on your LPD8 with its "Program" button. Then, Freepad cannot guess anymore which pad or knob send which note or control change message. In the same way, when you change the note associated to a pad in Freepad, you loose the synchornisation with the LPD8 until you press "Send" or "Send to RAM".
And if you set the same note for two or more pads or the same control change to two or more knobs, Freepad cannot guess which pad or knob is used. 
In such cases, a warning message is briefly displayed.
Sending a program to the LPD8 or getting one restore the synchronisation.

The LPD8 MK2 is NOT SUPPORTED yet. 

