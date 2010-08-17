import shutil

from bbfreeze import Freezer

f = Freezer("emptyorch_rel")
f.addScript("emptyorch.py")
f()
shutil.copy("emptyorch.xrc", "emptyorch_rel")
shutil.copy("fake.mp3", "emptyorch_rel")
