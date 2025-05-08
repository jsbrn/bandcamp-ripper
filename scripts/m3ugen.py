# Written for Python 3
import time
import os
import subprocess
import sys
import argparse
import pathlib
import re
import json
import glob
import urllib.parse

SEPARATOR = "----------------------------------"

# Parse command line arguments
argparser = argparse.ArgumentParser()
argparser.add_argument("-p", "--playlists_file", type=pathlib.Path, required=True)
argparser.add_argument("-o", "--output_folder", type=pathlib.Path, required=True)
args = argparser.parse_args()

output_folder = os.path.join(args.output_folder)

with open(args.playlists_file, 'r') as file:
    data = json.load(file)
    for playlist in data["playlists"]:
        with open(os.path.join(output_folder, urllib.parse.quote(str(playlist["name"])+".m3u", safe=' ')), "w") as m3u_file:
            #playlists.append()
            for item in playlist["items"]:
                artist_name = item["track"]["artistName"]
                track_name = item["track"]["trackName"]
                path = os.path.join(output_folder, artist_name, "**/*"+str(track_name)+"*")
                print(str(path))
                path_matches = glob.glob(path + "", recursive=True)
                if len(path_matches) > 0:
                    m3u_file.write(path_matches[0]+"\n")
                else:
                    m3u_file.write("#"+str(track_name)+" - "+str(artist_name)+"\n")
    file.close()
