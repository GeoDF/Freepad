import sys

from .freepadapp import FreepadApp

if __name__ == '__main__':
	app = FreepadApp(sys.argv)
	app.setApplicationName("Freepad")
	app.setStyle("fusion") # required
	sys.exit(app.exec())
else:
	print('Type "python -m pad" to start')



