"""
PyBluRead is a wrapper around libbluray.
By Colin ML Burnett

Not everything in libbluray is wrapped by this library.
"""

import _bluread

__all__ = ["Bluray", "Title", "Chapter", "Clip", "Video", "Audio", "Subtitle", "Version", "BRToXML"]

Version = _bluread.Version

from .objects import Bluray, Title, Chapter, Clip, Video, Audio, Subtitle

from crudexml import node,tnode

def BRToXML(device, KEYDB, pretty=True):
	with Bluray(device, KEYDB) as b:
		b.Open()

		root = node('br', numtitles=b.NumberOfTitles, parser="pybluread %s"%Version)
		root.AddChild( tnode('device', b.Path) )
		root.AddChild( tnode('KEYDB', b.KeyDB) )

		titles = root.AddChild( node('titles', main=b.MainTitleNumber) )

		for tnum in range(b.NumberOfTitles):
			t = b.GetTitle(tnum)

			title = titles.AddChild( node('title', idx=tnum, playlist=t.Playlist) )
			title.AddChild( tnode('length', t.Length, fancy=t.LengthFancy) )

			angles = title.AddChild( node('angles', num=t.NumberOfAngles) )


			#print([tnum, 'num chaps', t.NumberOfChapters])
			chapters = title.AddChild( node('chapters', num=t.NumberOfChapters) )
			for cnum in range(1,t.NumberOfChapters+1):
				c = t.GetChapter(cnum)

				#print([tnum, 'chap', cnum, c.ClipNum])
				chapter = chapters.AddChild( node('chapter', num=c.Num) )
				chapter.AddChild( tnode('start', c.Start, fancy=c.StartFancy) )
				chapter.AddChild( tnode('end', c.End, fancy=c.EndFancy) )
				chapter.AddChild( tnode('length', c.Length, fancy=c.LengthFancy) )
				chapter.AddChild( tnode('clipnum', c.ClipNum) )


			#print([tnum, 'num clips', t.NumberOfClips])
			clips = title.AddChild( node('clips', num=t.NumberOfClips) )
			for cnum in range(t.NumberOfClips):
				c = t.GetClip(cnum)
				#print([tnum, cnum, ((c.NumberOfVideosPrimary, c.NumberOfVideosSecondary), (c.NumberOfAudiosPrimary, c.NumberOfAudiosSecondary), c.NumberOfSubtitles)])

				clip = clips.AddChild( node('clip', num=c.Num) )

				videos = clip.AddChild( node('videos', num=c.NumberOfVideosPrimary) )
				for snum in range(c.NumberOfVideosPrimary):
					s = c.GetVideo(snum)

					video = videos.AddChild( node('video', num=s.Num) )
					video.AddChild( tnode('Language', s.Language) )
					video.AddChild( tnode('CodingType', s.CodingType) )
					video.AddChild( tnode('Format', s.Format) )
					video.AddChild( tnode('Rate', s.Rate) )
					video.AddChild( tnode('Aspect', s.Aspect) )

				audios = clip.AddChild( node('audios', num=c.NumberOfAudiosPrimary) )
				for snum in range(c.NumberOfAudiosPrimary):
					s = c.GetAudio(snum)

					audio = audios.AddChild( node('audio', num=s.Num) )
					audio.AddChild( tnode('Language', s.Language) )
					audio.AddChild( tnode('CodingType', s.CodingType) )
					audio.AddChild( tnode('Format', s.Format) )
					audio.AddChild( tnode('Rate', s.Rate) )

				subs = clip.AddChild( node('subtitles', num=c.NumberOfSubtitles) )
				for snum in range(c.NumberOfSubtitles):
					s = c.GetSubtitle(snum)

					sub = subs.AddChild( node('subtitle', num=s.Num) )
					sub.AddChild( tnode('Language', s.Language) )

	if pretty:
		return root.OuterXMLPretty
	else:
		return root.outerXML

