import sys
from pathlib import Path

if getattr(sys, '_MEIPASS', False):
	FREEPAD_PATH = Path(sys._MEIPASS) # noqa
	FREEPAD_IS_COMPILED = True
else:
	FREEPAD_PATH = Path(__file__).parent
	FREEPAD_IS_COMPILED = False
FREEPAD_ICON_PATH = str(FREEPAD_PATH.joinpath(u'ui').joinpath(u'img').joinpath(u'djembe.png'))

def imgUrl(path):
	return str(FREEPAD_PATH.joinpath(u'ui').joinpath(u'img').joinpath(path)).replace('\\', '/')
