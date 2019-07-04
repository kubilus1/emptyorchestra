import os
import sys
from optparse import OptionParser

class TitleMaker():
    def __init__(self, delim, tpos, apos):
        self.delim = delim
        self.tpos = tpos
        self.apos = apos

    def titleize(self, instring):
        outstring = ''
        vals = instring.split()
        for val in vals:
            outstring = "%s %s" % (outstring, val.capitalize())
        return outstring.lstrip()


    def maketitle(self, filename):
        file, ext = os.path.splitext(filename)
        chunks = file.split(self.delim)
        if len(chunks) >= 2:
            outstring = "%s|%s|%s" % (
                filename.strip(),
                self.titleize(chunks[self.tpos].strip()),
                self.titleize(chunks[self.apos].strip())
            )
        return outstring
        #if len(chunks) >= 2:
        #    print "%s|%s|%s" % (
        #        filename.strip(),
        #        titleize(chunks[-2].split('.')[-1].strip()),
        #        titleize(chunks[-1].split('.')[0].strip()),
        #    )
        #else:
        #    print "%s|%s|" % (
        #        filename.strip(),
        #        titleize(chunks[-1].split('.')[0].strip()),
        #    )

    def maketitles(self, files):
        titles = []
        for file in files:
            if file.endswith('.cdg'):
                titles.append(self.maketitle(file))

            if file.endswith('.zip'):
                titles.append(
                    self.maketitle(os.path.join(
                        file,
                        file.replace('.zip', '.cdg')
                    ))
                )
        return titles


def main():
    parser = OptionParser()
    parser.add_option(
        "-d",
        "--delimiter",
        action = "store",
        help = "Character(s) seperating each item",
        default = "-"
    )
    parser.add_option(
        "-t",
        "--title_pos",
        action = "store",
        help = "Position of song title in file path",
        default = "1"
    )
    parser.add_option(
        "-a",
        "--artist_pos",
        action = "store",
        help = "Position of artist name in file path",
        default = "0"
    )
    
    opts, args = parser.parse_args()

    if args > 1:
        path = "."
    else:
        path = args[0]

    files = os.listdir(path)
    tm = TitleMaker(
        opts.delimiter,
        int(opts.title_pos),
        int(opts.artist_pos)
    )
    titles = tm.maketitles(files)
    for title in titles:
        print title

if __name__ == "__main__":
    main()
