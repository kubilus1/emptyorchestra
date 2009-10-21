import shutil

from bbfreeze import Freezer

f = Freezer("emptyorch")
f.addScript("emptyorch.py")
f()
shutil.copy("emptyorch.xrc", "emptyorch")
shutil.copy("emptyorch.cfg", "emptyorch")
