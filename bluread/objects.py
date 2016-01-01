"""
Python objects that wrap C API objects.
"""

import _bluread

import os

def TicksToFancy(l):
	"""
	Convert 64-bit bluray ticks into clock time.
	There is a conversion constant of 90000 that I am unable to find good documentation for.
	That said, the resulting times match what other programs tell me so it must be legit.
	"""
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
	"""
	Entry object into parsing Bluray structure.
	Pass the device path to the init function, and then call Open() to initiate reading.
	Also, provide a path to KEYDB.cfg file if you feel so inclined (which is passed through libbluray as libbluray does not decrypt).
	
	A Bluray has titles.
	A Title has chapters.
	"""

	def __init__(self, Path, KEYDB=None):
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
		_bluread.Title.__init__(self, BR, Num, Chapter,Clip)

	@property
	def LengthFancy(self):
		return TicksToFancy(self.Length)

	@property
	def Playlist(self):
		"""
		Gets the playlist as an MPLS file name.
		"""
		return "%05d.mpls" % self.PlaylistNumber

class Chapter(_bluread.Chapter):
	"""
	Represents a chaper which belongs to a title.
	Chapters reference a clip, which contains all of the media data.
	"""

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

class Clip(_bluread.Clip):
	"""
	A title consists of 1+ clips and 1+ chapters.
	Each chapter references a clip.
	Each clip contains video, audio, interactive graphics (aka menus), and presentation graphics (aka subtitles).
	"""

	def __init__(self, Title, Num):
		_bluread.Clip.__init__(self, Title, Num, Video, Audio, Subtitle)

class Video(_bluread.Video):
	"""
	Video stream.
	"""

	def __init__(self, Clip, Num):
		_bluread.Video.__init__(self, Clip, Num)

	@property
	def CodingType(self):
		x = self._CodingType
		if x == 1:			return "MPEG1"
		elif x == 2:		return "MPEG2"
		elif x == 0xEA:		return "VC-1"
		elif x == 0x1B:		return "H.264"
		else:				return "%d"%x

	@property
	def Format(self):
		x = self._Format
		if x == 1:			return "480i"
		elif x == 2:		return "576i"
		elif x == 3:		return "480p"
		elif x == 5:		return "720p"
		elif x == 6:		return "1080p"
		elif x == 7:		return "576p"
		else:				return "%d"%x

	@property
	def Rate(self):
		x = self._Rate
		if x == 1:			return "23.976"
		elif x == 2:		return "24.000"
		elif x == 3:		return "25.000"
		elif x == 4:		return "29.970"
		elif x == 6:		return "50.000"
		elif x == 7:		return "59.940"
		else:				return "%d"%x

	@property
	def Aspect(self):
		x = self._Aspect
		if x == 2:			return "4:3"
		elif x == 3:		return "16:9"
		else:				return "%d"%x

class Audio(_bluread.Audio):
	"""
	Audio stream.
	"""

	def __init__(self, Clip, Num):
		_bluread.Audio.__init__(self, Clip, Num)

	@property
	def CodingType(self):
		x = self._CodingType
		if x == 3:			return "MPEG1"
		elif x == 4:		return "MPEG2"
		elif x == 0x80:		return "LPCM"
		elif x == 0x81:		return "AC-3"
		elif x == 0x82:		return "DTS"
		elif x == 0x83:		return "TruHD"
		elif x == 0x84:		return "AC-3+"
		elif x == 0x85:		return "DTS-HD"
		elif x == 0x86:		return "DTS-HD Master"
		elif x == 0xA2:		return "DTS-HD Secondary"
		else:				return "%d"%x

	@property
	def Format(self):
		x = self._Format
		if x == 1:			return "Mono"
		elif x == 3:		return "Stereo"
		elif x == 6:		return "Multiple"
		elif x == 12:		return "Combo"
		else:				return "%d"%x

	@property
	def Rate(self):
		x = self._Rate
		if x == 1:			return "48000"
		elif x == 4:		return "96000"
		elif x == 5:		return "192000"
		elif x == 12:		return "192000 Combo"
		elif x == 14:		return "96000 Combo"
		else:				return "%d"%x

class Subtitle(_bluread.Subtitle):
	"""
	Presentation graphic streams are suggested to be used for subtitles (i.e., non-interactive overlay graphics).
	PG streams are just assumed to be subtitles in this module.
	"""

	def __init__(self, Clip, Num):
		_bluread.Subtitle.__init__(self, Clip, Num)

