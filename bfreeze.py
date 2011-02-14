import os
import shutil

from bbfreeze import Freezer

f = Freezer("emptyorch_%s" % os.name)
f.addScript("emptyorch.py")
f()
shutil.copy("emptyorch.xrc", "emptyorch_rel")
shutil.copy("fake.mp3", "emptyorch_rel")
