# Written for Python 3

import time
import os
import subprocess
import sys
import argparse
import re
import json
import glob

import yt_dlp
import requests
from bs4 import BeautifulSoup

SEPARATOR = "----------------------------------"

# Parse command line arguments
argparser = argparse.ArgumentParser()
argparser.add_argument("-p", "--playlists_file", required=True)
argparser.add_argument("-l", "--library_file", required=True)
argparser.add_argument("-o", "--output_folder", required=True)
argparser.add_argument("-a", "--artist", default="")
args = argparser.parse_args()

# Parse both json files into a set of of "Album :::: Artist" entries separated by newline
# TODO: if other streaming sites are added as a source this part will need to be more robust
parsed_albums = []
with open(args.library_file, 'r') as file:
    data = json.load(file)
    entries = data["tracks"] + data["albums"]
    for entry in entries:
        if args.artist == "" or entry["artist"] == args.artist:
            parsed_albums.append(entry["album"] + " :::: " + entry["artist"])
    file.close()

with open(args.playlists_file, 'r') as file:
    data = json.load(file)
    for playlist in data["playlists"]:
        for item in playlist["items"]:
            if args.artist == "" or item["track"]["artistName"] == args.artist:
                parsed_albums.append(item["track"]["albumName"] + " :::: " + item["track"]["artistName"])
    file.close()

albums = set(parsed_albums)
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

        if len(results) == 0:
            print("            (none)")

        # Collect the matches
        all_matches = []
        album_matches = []
        for result in results:
            heading = result.find("div", class_="heading")
            entry_name = heading.text.strip()
            url = heading.find("a")["href"].split("?from=")[0]
            attribution = result.find("div", class_="subhead").text.strip().split("by ")
            entry_artist = attribution[len(attribution)-1]

            clean_title = re.sub(r"\s", "", title).lower()
            clean_entry_name = re.sub(r"\s", "", entry_name).lower()
            clean_artist = re.sub(r"\s", "", artist).lower()
            clean_entry_artist = re.sub(r"\s", "", entry_artist).lower()

            #print(clean_title, clean_entry_name, clean_artist, clean_entry_artist)

            is_match = (clean_entry_name == clean_title or clean_entry_name.startswith(clean_title)) and (clean_entry_artist == clean_artist or clean_entry_artist.startswith(clean_artist))
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
            track_count = max(1, len(page_soup.find_all("tr", class_="track_row_view")))

            # Download if missing tracks, otherwise skip
            print("TRACK COUNT: "+str(existing_files_count)+" / " + str(track_count))
            if existing_files_count < track_count:
                print("MISSING "+str(track_count-existing_files_count)+" OUT OF "+str(track_count)+" TRACKS")
                print("DOWNLOADING...")

                # Download the album
                ytdl_opts = {
                    "ignoreerrors": True, 
                    "verbose": False, 
                    "outtmpl": path+"/%(playlist_index)s - %(title)s.%(ext)s", 
                    "writethumbnail": True,
                    'postprocessors': [
                        {
                            'key': 'FFmpegMetadata'
                        }, 
                        {
                            'key': 'EmbedThumbnail',
                            'already_have_thumbnail': True, 
                        }
                    ] 
                }
                with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                    try:
                        error_code = ydl.download(url)
                    except:
                        pass

                # Clean up artwork
                for f in glob.glob(os.path.join(path, "*.jpg")):
                    os.remove(f)

                # Verify download
                existing_files_count = len(os.listdir(path))
                if existing_files_count < track_count:
                    print("SAVED "+str(existing_files_count)+" TRACKS TO "+path)
                    print("NOT ALL TRACKS COULD BE DOWNLOADED (LIKELY BECAUSE PREVIEWS ARE DISABLED. BUY THE ALBUM!)")
                    print("STILL MISSING "+str(track_count-existing_files_count)+" OUT OF "+str(track_count)+" TRACKS")
                    partially_downloaded_urls.append(title+" BY "+artist+" ("+str(existing_files_count)+"/"+str(track_count)+" DOWNLOADED)    "+url)
                else:
                    print("DOWNLOAD COMPLETED SUCCESSFULLY!")
                    successful_count = successful_count + 1
            else:
                print("ALBUM ALREADY DOWNLOADED")
                existing_count = existing_count + 1
        else:
            albums_not_found.append(title+" BY "+artist+" ("+str(len(results))+" results, "+str(len(all_matches))+" matches)")

        # Wait a second to avoid getting rate-limited (haven't had any trouble with a 1-second delay)
        time.sleep(1)
        print(SEPARATOR)

# Show summary
print("DONE. REMEMBER TO BUY YOUR ALBUMS! THANK YOU FOR SUPPORTING ARTISTS DIRECTLY AND TAKING A STAND AGAINST DRM.\n")
print("ALBUMS IN SPOTIFY DATA: "+str(album_count))
print("ADDED "+str(successful_count)+" COMPLETE ALBUMS TO LIBRARY (" + str(existing_count) + " FOUND IN LIBRARY)")
print("ALBUMS MISSING TRACKS: "+str(len(partially_downloaded_urls)))
for partial in partially_downloaded_urls:
    print("    * "+partial)
print("ALBUMS NOT FOUND ON BANDCAMP: "+str(len(albums_not_found)))
if len(albums_not_found) > 0:
    print("    (You might consider looking these up yourself just in case)")
for notfound in albums_not_found:
    print("    * "+notfound)