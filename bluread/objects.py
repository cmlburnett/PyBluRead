"""
Python objects that wrap C API objects.
"""

import _bluread

import glob
import os
import subprocess


def TicksToTuple(l):
	"""
	Convert 64-bit bluray ticks into clock time as a 4-tuple of (hours, minutes, seconds, milliseconds)
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

	return (h,m,s,ms)

def TicksToFancy(l):
	"""
	Convert 64-bit bluray ticks into clock time.
	There is a conversion constant of 90000 that I am unable to find good documentation for.
	That said, the resulting times match what other programs tell me so it must be legit.
	"""

	t = TicksToTuple(l)

	return "%02d:%02d:%02d.%03d" % t

class Disc:
	"""
	Utility functions.
	"""

	@staticmethod
	def Check(globpath):
		"""
		Checks drives based on a glob path @globpath.
		Returned is a 3-tuple of (path, disc_type, and discid) where disc_type is 'br', 'dvd', or 'cd'.

		I have not tried multi-mode discs, so I have no idea what udevadm returns.
		My suspicion is that there are multiple media keys that would match.

		Sample output of udevadm that is expected is shown below (only serial number is removed).
		This drive is a BR/DVD/CD combo drive that currently has a CD inserted.
		The three keys of interest are ID_CDROM_MEDIA_CD=1, ID_CDROM_MEDIA_DVD=1, and ID-CDROM_MEDIA_BD=1.
		These indicate the type of media inserted.
		Depending on which is set, the appropriate function is called to return an ID for the media.

		$ udevadm info -q all /dev/sr0
		P: /devices/pci0000:00/0000:00:1f.2/ata1/host0/target0:0:1/0:0:1:0/block/sr0
		N: sr0
		L: -100
		S: cdrom
		S: cdrw
		S: disk/by-id/ata-HL-DT-ST_BD-RE_BH12LS38_K91B6A95648
		S: dvd
		S: dvdrw
		E: DEVLINKS=/dev/cdrom /dev/disk/by-id/ata-HL-DT-ST_BD-RE_XXXXXXXXXX /dev/cdrw /dev/dvd /dev/dvdrw
		E: DEVNAME=/dev/sr0
		E: DEVPATH=/devices/pci0000:00/0000:00:1f.2/ata1/host0/target0:0:1/0:0:1:0/block/sr0
		E: DEVTYPE=disk
		E: ID_ATA=1
		E: ID_ATA_FEATURE_SET_PM=1
		E: ID_ATA_FEATURE_SET_PM_ENABLED=0
		E: ID_ATA_SATA=1
		E: ID_ATA_SATA_SIGNAL_RATE_GEN1=1
		E: ID_BUS=ata
		E: ID_CDROM=1
		E: ID_CDROM_BD=1
		E: ID_CDROM_BD_R=1
		E: ID_CDROM_BD_RE=1
		E: ID_CDROM_CD=1
		E: ID_CDROM_CD_R=1
		E: ID_CDROM_CD_RW=1
		E: ID_CDROM_DVD=1
		E: ID_CDROM_DVD_PLUS_R=1
		E: ID_CDROM_DVD_PLUS_RW=1
		E: ID_CDROM_DVD_PLUS_R_DL=1
		E: ID_CDROM_DVD_R=1
		E: ID_CDROM_DVD_RAM=1
		E: ID_CDROM_DVD_RW=1
		E: ID_CDROM_MEDIA=1
		E: ID_CDROM_MEDIA_CD=1
		E: ID_CDROM_MEDIA_SESSION_COUNT=1
		E: ID_CDROM_MEDIA_TRACK_COUNT=10
		E: ID_CDROM_MEDIA_TRACK_COUNT_AUDIO=10
		E: ID_CDROM_MRW=1
		E: ID_CDROM_MRW_W=1
		E: ID_MODEL=HL-DT-ST_BD-RE_BH12LS38
		E: ID_MODEL_ENC=HL-DT-ST\x20BD-RE\x20\x20BH12LS38\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
		E: ID_REVISION=1.00
		E: ID_SERIAL=XXXXXXXXXXXXXXXXXXXX
		E: ID_SERIAL_SHORT=XXXXXXXX
		E: ID_TYPE=cd
		E: MAJOR=11
		E: MINOR=0
		E: SUBSYSTEM=block
		E: TAGS=:uaccess:seat:systemd:
		E: USEC_INITIALIZED=2498180
		"""

		ret = []

		paths = glob.glob(globpath)
		for path in paths:
			# Call udevadm to get drive status
			lines = subprocess.check_output(['udevadm', 'info', '-q', 'all', path], universal_newlines=True).split('\n')

			for line in lines:
				parts = line.split(' ', 1)
				if len(parts) != 2: continue

				discid = None
				typ = None
				if parts[1] == 'ID_CDROM_MEDIA_CD=1':
					ret.append( (path, 'cd', Disc.cd_discid(path)) )
				elif parts[1] == 'ID_CDROM_MEDIA_DVD=1':
					ret.append( (path, 'dvd', Disc.dvd_discid(path)) )
				elif parts[1] == 'ID_CDROM_MEDIA_BD=1':
					ret.append( (path, 'br', Disc.br_discid(path)) )

		return ret

	@staticmethod
	def cd_discid(path):
		"""
		Gets the ID of the CD disc.
		This is from the cd-discid program that aggregates information about the tracks since CDs have no unique identifier otherwise.
		This is the same ID used for CDDB.
		"""

		return subprocess.check_output(['cd-discid', path]).decode('latin-1').split('\n')[0]

	@staticmethod
	def dvd_discid(path):
		"""
		Gets the ID of the DVD disc.
		This is the Volume id and volume size from the output of isoinfo.
		Volume id is not always sufficient to be unique enough to be usable.
		"""

		vid = None
		vsid = None
		sz = None

		lines = subprocess.check_output(['isoinfo', '-d', '-i', path]).decode('latin-1').split('\n')
		for line in lines:
			parts = line.split(':')
			if parts[0].lower().startswith('volume id'): vid = parts[1].strip()
			if parts[0].lower().startswith('volume set id'): vsid = parts[1].strip()
			if parts[0].lower().startswith('volume size'): sz = parts[1].strip()

		if vid == None:		raise ValueError("Did not find volume id in isoinfo output")
		if vsid == None:	raise ValueError("Did not find volume set id in isoinfo output")
		if sz == None:		raise ValueError("Did not find volume size in isoinfo output")

		return "%s - %s - %s" % (vid,vsid,sz)

	@staticmethod
	def br_discid(path):
		lines = subprocess.check_output(['blkid', '-s', 'LABEL', '-o', 'value', path]).decode('latin-1').split('\n')
		label = lines[0].strip()
		if not len(label):
			raise ValueError("Failed to get LABEL for '%s'" % path)

		lines = subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', path]).decode('latin-1').split('\n')
		uuid = lines[0].strip()
		if not len(uuid):
			raise ValueError("Failed to get UUID for '%s'" % path)

		return "%s - %s" % (label, uuid)

	@staticmethod
	def br_getSize(path):
		label,uuid = __class__.br_discid(path).split(' - ')

		lines = subprocess.check_output(['blockdev', '--getbsz', path]).decode('latin-1').split('\n')
		blocksize = int(lines[0])

		lines = subprocess.check_output(['blockdev', '--getsize64', path]).decode('latin-1').split('\n')
		size = int(lines[0])

		blocks = int(size / blocksize)

		return (label,blocksize,blocks)

	@staticmethod
	def dd(inf, outf, blocksize, blocks, label):
		"""
		Perform a 'resumable' dd copy from @inf to @ouf using the given blocksize and number of blocks.
		The @label is used in exceptions to be descriptive.

		The resumable aspect:
		1) If @outf exists, then the sizes are compared
		2) If the @outf size is the same as what is expected then nothing is done
		3) If the @outf size is not a multiple of @blocksize, the remainder of the block is copied with blocksize=1
		4) If the @outf size is a multiple of @blocksize, the remainder of the blocks are copied by seek and skip appropriately.
		5) If @outf does not exist, then the entire @inf is copied.

		Commands used:
			Partial block copy:   ['dd', 'if=%s'%inf, 'of=%s'%outf, 'bs=1', 'count=%d' % (blocksize - (cursize % blocksize)), 'skip=%d'%cursize, 'seek=%d'%cursize]
			Remaining block copy: ['dd', 'if=%s'%inf, 'of=%s'%outf, 'bs=1', 'count=%d' % (blocksize - (cursize % blocksize)), 'skip=%d'%cursize, 'seek=%d'%cursize]
			Remaining block copy: ['dd', 'if=%s'%inf, 'of=%s'%outf, 'bs=%d' % blocksize, 'count=%d' % (blocksize - (cursize % blocksize)), 'skip=%d'%cursize, 'seek=%d'%cursize]
			Full block copy:      ['dd', 'if=%s'%inf, 'of=%s'%outf, 'bs=%d'%blocksize, 'count=%d'%blocks]

		Where cursize is given by os.path.getsize().
		"""

		# Get expected total size
		expectedsize = blocksize * blocks

		if os.path.exists(outf):
			cursize = os.path.getsize(outf)

			# If sizes are the same, then no need to copy
			if expectedsize == cursize:
				print("Disc already copied")
				return

			elif expectedsize < cursize:
				print("Disc already copied")
				# Um, ok, I guess it's done copying
				return

			else:
				# Partial copy
				print("Partial copy: blocksize=%d, blocks=%d, mod=%d" % (blocksize, blocks, blocksize - (cursize % blocksize)))

				# First, need to copy remaining block
				if cursize % blocksize != 0:
					print("Partial block copy")
					# Finish remainder of block
					args = ['dd', 'if=%s'%inf, 'of=%s'%outf, 'bs=1', 'count=%d' % (blocksize - (cursize % blocksize)), 'skip=%d'%cursize, 'seek=%d'%cursize]
					print(" ".join(args))
					ret = subprocess.call(args)
					if ret != 0:
						raise Exception("Failed to partial copy remaining block %d of disc '%s' to drive" % (int(cursize/blocksize)+1, label))

				# Get [possibly] updated size
				cursize = os.path.getsize(outf)

				print("Partial copy")
				# Finish remainder of disc
				#   * Blocks written: int(cursize / blocksize)
				#   * Remaining blocks: blocks - int(cursize / blocksize)
				#   * Starting block: int(cursize / blocksize)
				args = ['dd', 'if=%s'%inf, 'of=%s'%outf, 'bs=%d' % blocksize, 'count=%d' % (blocks - int(cursize / blocksize)), 'skip=%d'%int(cursize/blocksize), 'seek=%d'%int(cursize/blocksize)]
				print(" ".join(args))
				ret = subprocess.call(args)
				if ret != 0:
					raise Exception("Failed to copy remaining %d blocks (total %d) of disc '%s' to drive" % (blocks - int(cursize/blocksize)+1, blocks, label))

		else:
			# Dup entire disc to drive
			args = ['dd', 'if=%s'%inf, 'of=%s'%outf, 'bs=%d'%blocksize, 'count=%d'%blocks]
			print(" ".join(args))
			ret = subprocess.call(args)
			if ret != 0:
				raise Exception("Failed to copy disc '%s' to drive" % label)

	@staticmethod
	def dvd_GetSize(path):
		"""
		Get label, block size, and # of blocks from the disc (returned as a tuple in that order).
		Using block size and blocks, instead of not specifying them, per this page
		  https://www.thomas-krenn.com/en/wiki/Create_an_ISO_Image_from_a_source_CD_or_DVD_under_Linux
		Seems the more prudent choice.
		"""

		# Get information from isoinfo
		ret = subprocess.check_output(["isoinfo", "-d", "-i",path], universal_newlines=True)
		lines = ret.split("\n")

		label = None
		blocksize = None
		blocks = None

		# Have to iterate through the output to find the desired lines
		for line in lines:
			parts = line.split(':')
			parts = [p.strip() for p in parts]

			if parts[0] == 'Volume id':						label = parts[1]
			elif parts[0] == 'Logical block size is':		blocksize = int(parts[1])
			elif parts[0] == 'Volume size is':				blocks = int(parts[1])
			else:
				# Don't care
				pass

		# Make sure all three are present
		if label is None:		raise Exception("Could not find volume label")
		if blocksize is None:	raise Exception("Could not find block size")
		if blocks is None:		raise Exception("Could not find number of blocks")

		return (label,blocksize,blocks)

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

