# Bandcamp Ripper

Find every album in your exported Spotify playlists and liked songs and download the lossy mp3s from Bandcamp. Ditch Spotify and take your music with you. 

The goal here is to help ease the transition from Spotify to DRM-free and artist-friendly methods of acquiring music. Just export your Spotify data and run the script, and it will populate a folder of your choice with all the music it can find on Bandcamp.

It even embeds metadata and artwork, but you need ffmpeg installed to do this.

This script is not meant to steal people's creative works. That is why the script only downloads the lossy mp3 previews from Bandcamp, and does not have access to tracks that artists have not enabled previews for. It does not attempt to find lossless versions anywhere on the internet. If you want the full lossless album, you should support the artist by paying for it.

This shouldn't be an issue. You were already paying for music through Spotify, but because of their abysmal payout rates, you were essentially paying Spotify for the privilege of mooching off your favorite artists. A digital album is roughly the price of a month of Spotify, so buy one album a month and replace the old lossy version with your new lossless copy.

Everyone wins. Except Spotify, of course. Cry me a river.

# Setup
* Request a data download from Spotify, specifically the main one (not the extended history or technical data). It comes as a .zip after a few days.
* Install Python 3
* pip3 install the imports
* Install ffmpeg on your system (it has to be accessible from anywhere in a command prompt / terminal, so you'll need to edit your PATH variable if you're on Windows)

# Ripper.py - Usage

Extract the Spotify data export and find the library file and the playlist file. These contain every song you've liked enough to save somewhere. Pass them to the script as command line arguments. Here's an example of how to do it.

```
python3 ripper.py --library_file YourLibrary.json --playlists_file Playlist1.json --output_folder /home/username/Music
```

| Parameter | Example | Description |
| - | - | - |
| --artist / -a | --artist "Artist Name" | Runs against only one artist in your Spotify export, not the whole collection.
| --dryrun / -d | --dryrun 1 | If included, the script will only search. It will not download. |

Optionally, you can also pass `--artist "Exact Artist Name"` to download only a specific artist from your library.

The script organizes your download in folders (Artist / Album) in the main output folder you specify.

# M3UGen.py - Usage

Given a Spotify playlists file, you can generate .m3u (playlist) files. Point it to the playlist file and output folder you used with `ripper.py`. It searches the output folder for the songs mentioned in the playlist. If they aren't found, it writes the track and artist name in a comment. Exports the playlist files in the top level of your chosen output folder.

```
python3 m3ugen.py --playlists_file Playlist1.json --output_folder /home/username/Music
```

# TODO

* More sources other than Spotify (ex. manually list multiple artists/albums)
* GUI
* Save summary to a file
* Include summary of album prices and total library value in summary

# Known Bugs

**ripper.py**

* Sometimes fails to find the album in the search result. Maybe a better solution is to look up the artist then search for the album on their page?
* Adds albums with slashes in the name in a nested folder (ex. songs from album "A/B" are put in folder "Artist/A/B")
* Fails to create files and folders with invalid characters, probably needs to encode them