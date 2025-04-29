# Written for Python 3

import time
import os
import subprocess
import sys

import requests
from bs4 import BeautifulSoup

PLAYLIST_FILE = "Playlist1.json"
LIBRARY_FILE = "YourLibrary.json"
MUSIC_FOLDER = "/home/jeremy/Music"

# Parse both json files into a sorted unique list of "Album :::: Artist" entries separated by newline
# Requires jq to be installed on the system
command = "{ cat "+LIBRARY_FILE+" | jq .tracks[] | jq -r '.album + \" :::: \" + .artist' ; cat "+PLAYLIST_FILE+" | jq .playlists[].items[].track | jq -r '.albumName + \" :::: \" + .artistName' ; } | sort | uniq | grep \"Snail Mail\""
output = subprocess.check_output(command, shell=True, text=True).strip()

# Split the output into an array
albums = output.split("\n")
album_count = len(albums)


print("DISCOVERED " + str(album_count) + " ALBUMS TO SEARCH FOR.")

counter = 0
for album in albums:
    counter = counter + 1
    meta = album.split(" :::: ")
    if len(meta) == 2:
        title = meta[0]
        artist = meta[1]
        
        # Search Bandcamp for the album
        print("RESULTS FOR "+title+" BY "+artist+" ("+str(counter)+"/"+str(album_count)+"):")
        search_soup = BeautifulSoup(requests.get("https://bandcamp.com/search?q="+title+"+"+artist).content, "html.parser")
        results = search_soup.find_all("li", class_="searchresult")

        all_matches = []
        album_matches = []
        # Collect the matches and pick the best one to pass into yt-dlp
        for result in results:
            heading = result.find("div", class_="heading")
            entry_name = heading.text.strip()
            url = heading.find("a")["href"].split("?from=")[0]
            attribution = result.find("div", class_="subhead").text.strip().split("by ")
            entry_artist = attribution[len(attribution)-1]
            is_match = (entry_name.lower() == title.lower() or entry_name.lower().startswith(title.lower())) and (entry_artist.lower() == artist.lower() or entry_artist.lower().startswith(artist.lower()))
            is_album = "/album" in url
            if is_match:
                all_matches.append(url)
                if is_album:
                    album_matches.append(url)
            print("   " + ("[MATCH!] " if is_match else "         ") +  entry_name + " - "+entry_artist + "    " + url)
        
        if len(all_matches) > 0:
            url = all_matches[0]
            if len(album_matches) > 0:
                url = album_matches[0]
            print("SELECTED URL "+url+" FOR DOWNLOAD")
            # Make folder if it doesn't exist
            path = os.path.join(MUSIC_FOLDER, artist, title)
            try:
                os.makedirs(path)
            except OSError as error:
                print("FAILED TO MAKE FOLDER "+path+"!", error)
            # Fetch album length and other details
            # Decide if album is not fully downloaded
            existing_files_count = len(os.listdir(path))
            page_soup = BeautifulSoup(requests.get(url).content, "html.parser")
            track_count = len(page_soup.find_all("tr", class_="track_row_view"))
            print("ALBUM TRACK LENGTH: "+str(track_count))
            print("TRACKS DOWNLOADED: "+str(existing_files_count))
            if existing_files_count < track_count:
                print("DOWNLOADING...")
                subprocess.run("cd \""+path+"\";yt-dlp "+url+" --embed-thumbnail --add-metadata --output \"%(playlist_index)s - %(title)s.%(ext)s\"", shell=True)
                existing_files_count = len(os.listdir(path))
                if existing_files_count < track_count:
                    print("NOT ALL SONGS COULD BE DOWNLOADED (LIKELY BECAUSE PREVIEWS ARE DISABLED)")
                else:
                    print("DOWNLOAD COMPLETED SUCCESSFULLY!")

        


        time.sleep(1)