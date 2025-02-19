from qtpy.QtCore import QSettings


#
# A class with static methods for Freepad settings
#
class Fsettings(object):
	_settings = QSettings('geomaticien.com', 'Freepad')
	_group = 'Freepad'
	
	@staticmethod
	def set(key, value):
		Fsettings._settings.setValue(Fsettings._group + '/' + key, value)

	@staticmethod
	def get(key, defaultValue, _type=None):
		if _type == None:
			return Fsettings._settings.value(Fsettings._group + '/' + key, defaultValue)
		else:
			return Fsettings._settings.value(Fsettings._group + '/' + key, defaultValue, _type)