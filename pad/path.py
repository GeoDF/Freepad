import sys
from pathlib import Path


if getattr(sys, '_MEIPASS', False):
	FREEPAD_PATH = Path(sys._MEIPASS)
else:
	FREEPAD_PATH = Path(__file__).parent

FREEPAD_ICON_PATH = str(FREEPAD_PATH.joinpath('ui').joinpath('img').joinpath('djembe.png'))