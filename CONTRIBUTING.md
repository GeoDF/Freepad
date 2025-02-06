# Contributing to Freepad

Everibody could contribute, even without any programming knowledge :

## Creating presets

You can share your Freepad programs as presets, for musicians who use same devices, synthesizers and styles than you.

To do so, just configure Freepad to send notes with the pads and midi control change messages with the knobs to one synthesizer's drumkit, and save your program with an explicit name like:
```
reggae-wailers_gm_en.<ext>
```
The name must be composed of :
- a name reflecting the set of instruments (*"reggae-wailers"*).
- the target synthesizzer drumkit (*"gm"*, for General Midi drumkit).
- the language used for instruments names (*"en"*, for english).

(\<ext\> is just the extension of the file saved by Freepad. You don't need to care about it)

Then :
- check if some similar presets exists in the **Freepad/pad/pads/*<device_name>*/presets** directory. If not :
- fork Freepad.
- upload your presets in your **Freepad/pad/pads/*<device_name>*/presets** Github directory.
- submit a pull request.


## Creating kits

Kits are the lists of intruments and the lists of MIDI control change messages used by Freepad as titles for pads and knobs. Kits are defined in files stored in **Freepad/pad/midi/kits** for instruments kits and in **Freepad/pad/midi/controls** for control changes kits. Kits files are just text files with one number and one name per line, separated by one space.

Due to the MIDI implementation variations, kits are specifics to one synthesizer and one drumkit. That's why sharing kits is a good idea. To share new kits, fork Freepad and submit a pull request with your contribution.


## Translating kits and presets
Kits and presets are localized. You can contribute to Freepad with kits and presets translations. The process is the same than above.


## Creating new virtual devices
(to come)


## Adding support for new devices
(to come)


## Source code contributions
- fork Freepad.
- submit a pull request.

