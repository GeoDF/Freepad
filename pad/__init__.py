import sys

if sys.version_info < (3, 11):
	print('Freepad require Python version 3.11 or greater, while Python version here is ' + str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '.')
	sys.exit()

from .freepadapp import FreepadApp