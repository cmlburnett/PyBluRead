
import _bluread

import os

class Bluray(_bluread.Bluray):
	def __init__(self, Path, KEYDB):
		if type(KEYDB) ==  str and not os.path.exists(KEYDB):
			raise ValueError("KEYDB.cfg path '%s' does not exist" % KEYDB)

		_bluread.Bluray.__init__(self, Path, KEYDB, Title)

	def __enter__(self):
		return self

	def __exit__(self, type, value, tb):
		# Close, always
		try:
			self.Close()
		except Exception:
			pass

		# Don't suppress any exceptions
		return False

class Title(_bluread.Title):
	def __init__(self, BR, Num):
		_bluread.Title.__init__(self, BR, Num)

