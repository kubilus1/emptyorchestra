Emptyorchestra is a karaoke jukebox aimed at providing an quick and easy to use interface for playing all your CDG based karaoke files.

Ultimately Emptyorchestra aims to turn your PC into a professional karaoke system.

# Requirements #

  * Python 2.6 or greater
  * Mutagen: http://code.google.com/p/mutagen/
  * wxPython 2.8+: http://www.wxpython.org/download.php
  * pygame 1.9+: http://www.pygame.org/download.shtml
  * numpy: http://www.scipy.org/Download

# Setup #
## Windows ##
Windows users can download the latest Windows .MSI file.  Run it and follow the instructions.

If upgrading from an earlier version:

  1. Run the new .MSI installer and choose to 'REMOVE' the old version.
  1. Run the new .MSI installer and install as usual.

## Ubuntu/Debian ##
Ubuntu users can download the latest .deb file.  Install it with the following command:
```
  $ sudo dpkg -i emptyorch_<version>.deb
```
## All OSs ##

All other users can downloaded the latest source release .ZIP file or checkout the latest code from svn:

```
svn checkout http://emptyorchestra.googlecode.com/svn/trunk/ emptyorchestra-read-only  
```

The user will then enter the emptyorchestra directory and type 'python emptyorch.py' to run.  Or install the application with:

```
python setup.py install
```

EmptyOrchestra can then be run anywhere by executing:

```
emptyorch
```

# Screenshot #
![http://farm3.static.flickr.com/2792/4178714217_46a71a5189.jpg](http://farm3.static.flickr.com/2792/4178714217_46a71a5189.jpg)

# Help #

Take a look at the UsersGuide for instructions on how to use the software!  If there are some issues (I use this, but it's still a Work In Progress!), don't hesitate to tell me about it under the 'Issues' tab on this web site.


# To Do #
  * ~~Allow saving meta data changes~~
  * ~~Save options~~
  * ~~Interactively adjust cdg and audio offset~~
  * ~~Play in fullscreen~~
  * Add concept of Users and a User rotation
  * ~~Allow printouts of songs~~
  * Adjust pitch
  * Better Artist-Title detection
  * ~~Auto scan karaoke files~~
  * ~~Improve search~~
  * ~~Find similar artists~~
# Credits #

Thanks to the awesome work on the pycdg module from the folks at pykaraoke http://kibosh.org/pykaraoke/ and to LeeAnn for giving me lots of feedback :)