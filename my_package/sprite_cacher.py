import os
import json
import requests
import time

# Ensure cache directory exists


cache_dir = "professor_cache"
sprites_dir = os.path.join(cache_dir, "sprites")
poke_file = os.path.join(cache_dir, "professordata.json")

def cache_sprites():
    # Ensure cache and sprites directories exist
    os.makedirs(sprites_dir, exist_ok=True)


# Load JSON data
    with open(poke_file, encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        url = entry.get('sprite_url')
        name = entry.get('name')
        if url and name:
            # Use the Pokémon name as the filename
            ext = os.path.splitext(url)[1] or '.png'
            filename = f"{name}{ext}"
            filepath = os.path.join(sprites_dir, filename)
            # Skip if already cached
            if os.path.exists(filepath):
                #print(f"Already cached: {filename}") # Uncomment for cache confirmations
                continue
            try:
                print(f"Downloading {url} ...")
                resp = requests.get(url)
                resp.raise_for_status()
                with open(filepath, 'wb') as img_file:
                    img_file.write(resp.content)
                print(f"Saved: {filename}")
                time.sleep(.5)  # Sleep for .5 second between downloads
            except Exception as e:
                print(f"Failed to download {url}: {e}")