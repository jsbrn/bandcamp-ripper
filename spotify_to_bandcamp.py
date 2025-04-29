# Written for Python 3

import time
import os
import subprocess
import sys
import argparse

import requests
from bs4 import BeautifulSoup

SEPARATOR = "----------------------------------"

# Parse command line arguments
argparser = argparse.ArgumentParser()
argparser.add_argument("-p", "--playlists_file", required=True)
argparser.add_argument("-l", "--library_file", required=True)
argparser.add_argument("-o", "--output_folder", required=True)
args = argparser.parse_args()

# Parse both json files into a sorted unique list of "Album :::: Artist" entries separated by newline
# Requires jq to be installed on the system
command = "{ cat "+args.library_file+" | jq .tracks[] | jq -r '.album + \" :::: \" + .artist' ; cat "+args.playlists_file+" | jq .playlists[].items[].track | jq -r '.albumName + \" :::: \" + .artistName' ; } | sort | uniq"
output = subprocess.check_output(command, shell=True, text=True).strip()

# Split the output into an array
albums = output.split("\n")
album_count = len(albums)


print("CHECKING BANDCAMP FOR " + str(album_count) + " ALBUMS\n"+SEPARATOR)

counter = 0
successful_count = 0
existing_count = 0
partially_downloaded_urls = []
albums_not_found = []
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

        # Collect the matches
        all_matches = []
        album_matches = []
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

        # Pick the best match, check if it's not already downloaded, then send to yt-dlp for download
        if len(all_matches) > 0:
            url = all_matches[0]
            if len(album_matches) > 0:
                url = album_matches[0]
            print("SELECTED URL "+url+" FOR DOWNLOAD")
            #Make folder if it doesn't exist
            path = os.path.join(args.output_folder, artist, title)
            try:
                os.makedirs(path)
            except OSError as error:
                print("FAILED TO MAKE DIRECTORY "+path, error)
            # Fetch album length and other details
            existing_files_count = len(os.listdir(path))
            page_soup = BeautifulSoup(requests.get(url).content, "html.parser")
            track_count = len(page_soup.find_all("tr", class_="track_row_view"))
            # Download if missing tracks, otherwise skip
            if existing_files_count < track_count:
                print("MISSING "+str(track_count-existing_files_count)+" / "+str(track_count)+" TRACKS")
                print("DOWNLOADING...")
                subprocess.run("cd \""+path+"\";yt-dlp "+url+" --embed-thumbnail --add-metadata --output \"%(playlist_index)s - %(title)s.%(ext)s\"", shell=True)
                existing_files_count = len(os.listdir(path))
                if existing_files_count < track_count:
                    print("SAVED "+str(existing_files_count)+" TRACKS TO "+path)
                    print("NOT ALL TRACKS COULD BE DOWNLOADED (LIKELY BECAUSE PREVIEWS ARE DISABLED. BUY THE ALBUM!)")
                    print("STILL MISSING "+str(track_count-existing_files_count)+" OUT OF "+str(track_count)+" TRACKS")
                    partially_downloaded_urls.append(title+" BY "+artist+"    "+url)
                else:
                    print("DOWNLOAD COMPLETED SUCCESSFULLY!")
                    successful_count = successful_count + 1
            else:
                print("ALBUM ALREADY DOWNLOADED")
                existing_count = existing_count + 1
            print(SEPARATOR)
        else:
            albums_not_found.append(title+" BY "+artist)

        # Wait a second to avoid getting rate-limited (haven't had any trouble with a 1-second delay)
        time.sleep(1)

print("DONE. REMEMBER TO BUY YOUR ALBUMS! THANK YOU FOR SUPPORTING ARTISTS DIRECTLY AND TAKING A STAND AGAINST DRM.\n")
print("ALBUMS IN SPOTIFY DATA: "+str(album_count))
print("ADDED "+str(successful_count)+" COMPLETE ALBUMS TO LIBRARY (" + str(existing_count) + " FOUND IN LIBRARY)")
print("ALBUMS MISSING TRACKS: "+str(len(partially_downloaded_urls)))
for partial in partially_downloaded_urls:
    print("    * "+partial)
print("ALBUMS NOT FOUND ON BANDCAMP: "+str(len(albums_not_found)))
for notfound in albums_not_found:
    print("    * "+notfound)