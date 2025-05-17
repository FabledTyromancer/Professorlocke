import os
import json
import requests
import time

# Ensure cache directory exists

cache_dir = "professor_cache"
sprites_dir = os.path.join(cache_dir, "sprites")
poke_file = os.path.join(cache_dir, "professordata.json")


def cache_sprites(status_callback=None, sprite_callback=None):
    #make directory, don't overwrite if it exists
    os.makedirs(sprites_dir, exist_ok=True)
    #open generator json file so we can pull urls
    if os.path.exists(poke_file):
        with open(poke_file, 'r') as d:
            data = json.load(d)
    #pull urls for each pokemon
    for entry in data:
        name = entry.get('name')
        url = entry.get('sprite_url')
        if url and name:
            # Use the Pokémon name as the filename
            ext = os.path.splitext(url)[1] or '.png'
            filename = f"{name}{ext}"
            filepath = os.path.join(sprites_dir, filename)
            # Skip if already cached
            if os.path.exists(filepath):
                # Uncomment for debugging
                #if sprite_callback:
                #    sprite_callback(filepath)
                #msg = f"Already cached: {filename}"
                #print(msg) # cache confirmation
                #if status_callback:
                #    status_callback(msg)
                continue
            try:
                print(f"Downloading {url} ...")
                resp = requests.get(url)
                resp.raise_for_status()
                with open(filepath, 'wb') as img_file:
                    img_file.write(resp.content)
                msg = f"Saved: {filename}"
                print(msg)
                if status_callback:
                    status_callback(msg)
                time.sleep(.5)  # Sleep for .5 second between downloads
            except Exception as e:
                msg = f"Failed to download {url}: {e}"
                print(msg)
                if status_callback:
                    status_callback(msg)