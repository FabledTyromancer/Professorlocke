import json
import os
from typing import Dict, Tuple, Optional
from tkinter import messagebox
import time
#open or create pokemon json data
def fetch_pokemon_data(cache_dir: str = "professor_cache", status_callback=None) -> Optional[Tuple[Dict, Dict]]:
    """Fetch Pokemon Data from API and cache it."""
    poke_file = os.path.join(cache_dir, "professordata.json")

    # Check if cache exists and is valid
    try:
        if os.path.exists(poke_file):
            print(f"professordata.json found!")
            if status_callback:
                status_callback(f"professordata.json found!")
            time.sleep(.1)
            with open(poke_file, 'r') as d:
                return json.load(d)    
    except Exception as e:
        print("Error", f"Failed to fetch Pokémon data: {e}")
        if status_callback:
            status_callback("Error", f"Failed to fetch Pokémon data: {e}")
        time.sleep(2)
    return {}

#open or create egg group cache
def load_egg_group_cache(cache_dir: str = "professor_cache", status_callback=None) -> dict:
    """Load or create egg group cache with proper English names."""
    cache_file = os.path.join(cache_dir, "egg_groups.json")

    try:
        if os.path.exists(cache_file):
            print(f"egg_groups.json found!")
            if status_callback:
                status_callback(f"egg_groups.json found!")
            time.sleep(.1)
            with open(cache_file, 'r') as f:
                return json.load(f)

    except Exception as e:
        print(f"Error loading egg group cache: {e}")
        if status_callback:
            status_callback(f"Error loading egg group cache: {e}")
        time.sleep(2)
        return {}
