import sys

from pad.freepadapp import FreepadApp

if __name__ == '__main__':
	app = FreepadApp(sys.argv)
	sys.exit(app.exec())
else:
	print('Type "python -m pad" to start')



