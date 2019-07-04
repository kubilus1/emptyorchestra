import os
import shutil

from bbfreeze import Freezer

freezedir = os.path.join("bfreeze","emptyorch_%s" % os.name)
f = Freezer(freezedir)
f.addScript("emptyorch.py")
f()
shutil.copy("emptyorch.xrc", freezedir)
shutil.copy("fake.mp3", freezedir)
