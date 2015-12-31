
import _bluread

import os

def TicksToFancy(l):
	# I can't find any good documentation on why duration is in 90,000th's of a second
	total = l / 45000 / 2

	# After dividing by 90000, the non-integer fraction is the sub-second portion
	# So multiply by 1000 and truncate to get milliseconds
	ms = int((total - int(total)) * 1000)

	# total now in integer seconds, hour & minute math is straight-forward
	total = int(total)

	s = total % 60
	total = int(total / 60)

	m = total % 60
	total = int(total / 60)

	h = total

	return "%02d:%02d:%02d.%03d" % (h,m,s,ms)


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
		_bluread.Title.__init__(self, BR, Num, Chapter)

	@property
	def LengthFancy(self):
		return TicksToFancy(self.Length)

class Chapter(_bluread.Chapter):
	def __init__(self, TITLE, Num):
		_bluread.Chapter.__init__(self, TITLE, Num)

	@property
	def StartFancy(self):
		return TicksToFancy(self.Start)

	@property
	def LengthFancy(self):
		return TicksToFancy(self.Length)

	@property
	def End(self):
		return self.Start + self.Length

	@property
	def EndFancy(self):
		return TicksToFancy(self.End)

