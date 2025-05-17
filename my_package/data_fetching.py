import json
import os
from typing import Dict, Tuple, Optional
import requests
from tkinter import messagebox
import my_package.professorlockejsongenerator as generator
import time
#open or create pokemon json data
def fetch_pokemon_data(cache_dir: str = "professor_cache", status_callback=None) -> Optional[Tuple[Dict, Dict]]:
    """Fetch Pokemon Data from API and cache it."""
    poke_file = os.path.join(cache_dir, "professordata.json")

    # Check if cache exists and is valid
    if os.path.exists(poke_file):
            print(f"professordata.json found!")
            if status_callback:
                status_callback(f"professordata.json found!")
            time.sleep(.1)
            with open(poke_file, 'r') as d:
                return json.load(d)


    try:
        # Generate new data if cache doesn't exist or is invalid
        generator.main(status_callback=status_callback)
    
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch Pokémon data: {e}")
        if status_callback:
            status_callback("Error", f"Failed to fetch Pokémon data: {e}")
        time.sleep(2)
        return {}

    #verifies it worked, then reopens the file for use
    if os.path.exists(poke_file):
            with open(poke_file, 'r') as d:
                return json.load(d)

#open or create egg group cache
def load_egg_group_cache(cache_dir: str = "professor_cache", status_callback=None) -> dict:
    """Load or create egg group cache with proper English names."""
    cache_file = os.path.join(cache_dir, "egg_groups.json")

    if os.path.exists(cache_file):
        print(f"egg_groups.json found!")
        if status_callback:
            status_callback(f"egg_groups.json found!")
        time.sleep(.1)
        with open(cache_file, 'r') as f:
            return json.load(f)
    try:
        response = requests.get("https://pokeapi.co/api/v2/egg-group")
        response.raise_for_status()
        egg_groups = response.json()['results']

        egg_group_cache = {}
        for group in egg_groups:
            group_response = requests.get(group['url'])
            group_response.raise_for_status()
            group_data = group_response.json()

            # Get English name from names array
            english_name = next(
                (name['name'] for name in group_data['names']
                 if name['language']['name'] == 'en'),
                group_data['name']
            )
            egg_group_cache[group_data['name']] = english_name

        # Save to cache file
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(egg_group_cache, f)

        return egg_group_cache
    except requests.RequestException as e:
        print(f"Error loading egg group cache: {e}")
        if status_callback:
            status_callback(f"Error loading egg group cache: {e}")
        time.sleep(2)
        return {}
