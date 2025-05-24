import os
import json
import requests
import time

# Ensure cache directory exists

cache_dir = "professor_cache"
sprites_dir = os.path.join(cache_dir, "sprites")
poke_file = os.path.join(cache_dir, "professordata.json")
counter_file = os.path.join(cache_dir, "sprite_counter.json")

def load_counter():
    """Load the sprite download counter."""
    if os.path.exists(counter_file):
        try:
            with open(counter_file, 'r') as f:
                return json.load(f)
        except:
            return {"total_downloaded": 0, "last_update": ""}
    return {"total_downloaded": 0, "last_update": ""}

def save_counter(counter):
    """Save the sprite download counter."""
    with open(counter_file, 'w') as f:
        json.dump(counter, f)

def cache_sprites(status_callback=None, sprite_callback=None):
    #make directory, don't overwrite if it exists
    os.makedirs(sprites_dir, exist_ok=True)
    
    # Reset counter at start
    counter = {"total_downloaded": 0, "last_update": time.strftime("%Y-%m-%d %H:%M:%S")}
    save_counter(counter)
    
    downloaded_count = 0
    cached_count = 0
    
    #open generator json file so we can pull urls
    if os.path.exists(poke_file):
        with open(poke_file, 'r') as d:
            data = json.load(d)
    
    # Calculate total number of sprites to process (including forms)
    total_sprites = len(data)
    for entry in data:
        forms = entry.get("forms", [])
        if isinstance(forms, list):
            total_sprites += len(forms)
    
    current_sprite = 0
    #pull urls for each pokemon
    for entry in data:
        name = entry.get('name')
        url = entry.get('sprite_url')
        forms = entry.get("forms")
        formurl = entry.get('form_sprite_url')
        if url and name:
            current_sprite += 1
            ext = os.path.splitext(url)[1] or '.png' 
            filename = f"{name}{ext}"# Use the Pokémon name as the filename
            filepath = os.path.join(sprites_dir, filename)
            # Skip if already cached
            if os.path.exists(filepath):
                # Uncomment for debugging
                if sprite_callback:
                    sprite_callback(filepath)
                msg = f"Already cached: {filename} ({current_sprite}/{total_sprites})"
                print(msg) # cache confirmation
                if status_callback:
                    status_callback(msg)
                cached_count += 1
            else:
                try:
                    print(f"Downloading {url} ... ({current_sprite}/{total_sprites})")
                    resp = requests.get(url)
                    resp.raise_for_status()
                    with open(filepath, 'wb') as img_file:
                        img_file.write(resp.content)
                    msg = f"Saved: {filename} ({current_sprite}/{total_sprites})"
                    print(msg)
                    if status_callback:
                        status_callback(msg)
                    downloaded_count += 1
                    time.sleep(.5)  # Sleep for .5 second between downloads
                except Exception as e:
                    msg = f"Failed to download {form_url}: {e}"
                    print(msg)
                    if status_callback:
                        status_callback(msg)

        #pulls form sprites only if they are different from the default. Uncomment if you want to run forms.
        if isinstance(forms, list) and isinstance(formurl, list):
            for form_name, form_url in zip(forms, formurl):
                if not form_url or not form_name:
                    #print(f"Skipping form: {form_name}, url: {form_url}")
                    continue
                current_sprite += 1
                ext = os.path.splitext(form_url)[1] or '.png'
                filename = f"{form_name}{ext}"
                filepath = os.path.join(sprites_dir, filename)
                if os.path.exists(filepath):
                    cached_count += 1
                    continue
                try:
                    print(f"Downloading {form_url} ({current_sprite}/{total_sprites})")
                    resp = requests.get(form_url)
                    resp.raise_for_status()
                    with open(filepath, 'wb') as img_file:
                        img_file.write(resp.content)
                    msg = f"Saved: {filename} ({current_sprite}/{total_sprites})"
                    print(msg)
                    if status_callback:
                        status_callback(msg)
                    downloaded_count += 1
                    time.sleep(.5)
                except Exception as e:
                    msg = f"Failed to download {form_url}: {e}"
                    print(msg)
                    if status_callback:
                        status_callback(msg)
                    continue
    
    # Update counter with both downloaded and cached sprites
    total_sprites = downloaded_count + cached_count
    counter["total_downloaded"] = total_sprites
    counter["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_counter(counter)
    
    # Show summary message
    if downloaded_count > 0:
        if status_callback:
            status_callback(f"Downloaded {downloaded_count} new sprites. Total sprites: {total_sprites}")
    else:
        if status_callback:
            status_callback(f"No new sprites downloaded. Total sprites: {total_sprites}")