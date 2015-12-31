"""
PyBluRead is a wrapper around libbluray.
By Colin ML Burnett

Not everything in libbluray is wrapped by this library.
"""

import _bluread

__all__ = ["Bluray", "Title", "Version", "BRToXML"]

Version = _bluread.Version

from .objects import Bluray, Title

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

			title = titles.AddChild( node('title', idx=tnum) )
			title.AddChild( tnode('length', t.Length, fancy=t.LengthFancy) )

			angles = title.AddChild( node('angles', num=t.NumberOfAngles) )


			chapters = title.AddChild( node('chapters', num=t.NumberOfChapters) )
			for cnum in range(1,t.NumberOfChapters+1):
				c = t.GetChapter(cnum)

				chapter = chapters.AddChild( node('chapter', num=c.Num) )
				chapter.AddChild( tnode('start', c.Start, fancy=c.StartFancy) )
				chapter.AddChild( tnode('end', c.End, fancy=c.EndFancy) )
				chapter.AddChild( tnode('length', c.Length, fancy=c.LengthFancy) )
				chapter.AddChild( tnode('clipnum', c.ClipNum) )


			clips = title.AddChild( node('clips', num=t.NumberOfClips) )
			for cnum in range(t.NumberOfClips):
				c = t.GetClip(cnum)

				clip = clips.AddChild( node('clip', num=c.Num) )

				subs = clip.AddChild( node('subtitles', num=c.NumberOfSubtitles) )
				for snum in range(c.NumberOfSubtitles):
					s = c.GetSubtitle(snum)

					sub = sub.AddChild( node('subtitle', num=s.Num) )
					sub.AddChild( tnode('Language', s.Language) )



	if pretty:
		return root.OuterXMLPretty
	else:
		return root.outerXML

