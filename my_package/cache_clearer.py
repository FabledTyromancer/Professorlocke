import os
import shutil
import time
import json

# Identify the caches
cache_dir = "professor_cache"
sprites_dir = os.path.join(cache_dir, "sprites")
poke_file = os.path.join(cache_dir, "professordata.json")
egg_file = os.path.join(cache_dir, "egg_groups.json")
counter_file = os.path.join(cache_dir, "sprite_counter.json")

# Deletes the caches, displays a status update, and deletes.
def main(status_callback):
    clear_professordata(status_callback)
    time.sleep(1)
    clear_egg_cache(status_callback)
    time.sleep(1)
    clear_sprites(status_callback)
    time.sleep(1)
    clear_sprite_counter(status_callback)
    time.sleep(1)

# Find & delete professorcache
def clear_professordata(status_callback):
    if os.path.exists(poke_file):
        os.remove(poke_file)
        msg = f"Pokémon cache cleared."
        if status_callback:
            status_callback(msg)
    else:
        msg = f"Pokémon cache not cleared."
        if status_callback:
            status_callback(msg)

#find & delete the egg cache
def clear_egg_cache(status_callback):
    if os.path.exists(egg_file):
        os.remove(egg_file)
        msg = f"Egg cache cleared."
        if status_callback:
            status_callback(msg)
    else:
        msg = f"Egg cache not cleared."
        if status_callback:
            status_callback(msg)

# delete sprites
def clear_sprites(status_callback):
    if os.path.exists(sprites_dir):
        shutil.rmtree(sprites_dir)
        msg = f"Sprites Cleared."
        if status_callback:
            status_callback(msg)
    else:
        msg = f"Sprites could not be cleared."
        if status_callback:
            status_callback(msg)

# reset sprite counter
def clear_sprite_counter(status_callback):
    counter = {"total_downloaded": 0, "last_update": ""}
    try:
        with open(counter_file, 'w') as f:
            json.dump(counter, f)
        msg = f"Sprite counter reset."
        if status_callback:
            status_callback(msg)
    except Exception as e:
        msg = f"Failed to reset sprite counter: {e}"
        if status_callback:
            status_callback(msg)

if __name__ == "__main__":
    def print_status(msg):
        print(msg)
    main(status_callback=print_status)