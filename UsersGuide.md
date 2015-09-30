# Emptyorchestra Users Guide #

EmptyOrchestra turns your **Nix or Windows PC into a karaoke jukebox!**



# Usage #

## Finding Karaoke Files ##

When starting EmptyOrchestra for the first time you will be presented with a dialog asking where to find the karaoke files.  Select the directory containing all karaoke files.

EmptyOrchestra will enact a background scan of this data and load the songs into the system.  On every start of EmptyOrchestra it will check for new songs.  This happens in the background and you can sing while it scans!

## Starting Over ##

Emptyorchestra saves information under your user home directory in a directory called .emptyorch.  You can start the karaoke database over by removing the .musicdata file under this directory.


## Searching Songs ##

Underneath the media pane in the right side of the screen, a user may type in a search term.  Pressing enter will filter the media pane.  Pressing the 'x' on the search will un-filter the media pane.

## Playing Songs ##

You can play a highlighted song by clicking the button labeled 'Play Selected' or by pressing enter.

## Using the Playlist ##

Emptyorchestra allows you to select a series of songs into a playlist.  You can then play the entire playlist, re-arrange the playlist or remove items from the playlist.

After highlighting songs in the media pane, pressing 'Add to Playlist' will copy the chosen songs into the playlist in the lower right section of the screen.

The user may adjust the order of the playlist by clicking on the up or down arrow buttons above the playlist.  Clicking the 'x' button on the playlist will remove the highlighted song from the playlist.

## Syncing The Music ##

No one wants to have the lyrics come up at the wrong time during their song!

Emptyorchestra allows you to sync the lyrics to the music while the song is playing.

Tap the right arrow to have the lyrics come up sooner, tap the left arrow to have the lyrics come up later.

## Saving The Settings ##

Emptyorchestra will automatically preserve settings from the interface.  This would include:

  * Karaoke window size and position
  * Fullscreen display
  * Lyric offset

## Updating Song Artist and Title ##

Sometimes the artist and title of the song files are hard to determine accurately.  You can double click on these fields and correct them.

This information is stored in the tag of the music file and will be preserved on re-scans of the music database.

# Troubleshooting #

## After Upgrading EmptyOrchestra Fails to Start ##
EmptyOrchestra should automatically both the configuration and the musicdata.  If for some reason this does not work, try reinitializing the user data.

  * On any unix system, simply remove the '~/.emptyorchestra' directory.
  * On Windows you will remove a directory 'C:\Documents and Settings\

&lt;username&gt;

\.emptyorchestra'