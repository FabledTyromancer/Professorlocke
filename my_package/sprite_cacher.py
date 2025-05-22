import os
import json
import requests
import time

# Ensure cache directory exists

cache_dir = "professor_cache"
sprites_dir = os.path.join(cache_dir, "sprites")
poke_file = os.path.join(cache_dir, "professordata.json")

FORM_COUNT = 0


def cache_sprites(status_callback=None, sprite_callback=None):
    global FORM_COUNT
    #make directory, don't overwrite if it exists
    os.makedirs(sprites_dir, exist_ok=True)
    #open generator json file so we can pull urls
    if os.path.exists(poke_file):
        with open(poke_file, 'r') as d:
            data = json.load(d)
    #pull urls for each pokemon
    FORM_COUNT = 0
    for entry in data:
        name = entry.get('name')
        url = entry.get('sprite_url')
        forms = entry.get("forms")
        formurl = entry.get('form_sprite_url')
        if url and name:
            ext = os.path.splitext(url)[1] or '.png' 
            filename = f"{name}{ext}"# Use the Pokémon name as the filename
            filepath = os.path.join(sprites_dir, filename)
            # Skip if already cached
            if os.path.exists(filepath):
                # Uncomment for debugging
                if sprite_callback:
                    sprite_callback(filepath)
                msg = f"Already cached: {filename}"
                print(msg) # cache confirmation
                if status_callback:
                    status_callback(msg)
            else:
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
                    msg = f"Failed to download {form_url}: {e}"
                    print(msg)
                    if status_callback:
                        status_callback(msg)

        #pulls form sprites only if they are different from the default. Uncomment if you want to run forms.
        if isinstance(forms, list) and isinstance(formurl, list):
            for form_name, form_url in zip(forms, formurl):
                FORM_COUNT += len([1 for form_name, form_url in zip(forms, formurl) if form_url and form_name])
                if not form_url or not form_name:
                    print(f"Skipping form: {form_name}, url: {form_url} of {FORM_COUNT}")
                    continue
                ext = os.path.splitext(form_url)[1] or '.png'
                filename = f"{form_name}{ext}"
                filepath = os.path.join(sprites_dir, filename)
                if os.path.exists(filepath):
                    continue
                try:
                    print(f"Downloading {form_url}")
                    resp = requests.get(form_url)
                    resp.raise_for_status()
                    with open(filepath, 'wb') as img_file:
                        img_file.write(resp.content)
                    msg = f"Saved: {filename}"
                    print(msg)
                    if status_callback:
                        status_callback(msg)
                    time.sleep(.5)
                except Exception as e:
                    msg = f"Failed to download {form_url}: {e}"
                    print(msg)
                    if status_callback:
                        status_callback(msg)
                    continue