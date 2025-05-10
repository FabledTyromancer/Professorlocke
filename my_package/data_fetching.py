import json
import os
from typing import Dict, Tuple, Optional
import requests
from tkinter import messagebox


def fetch_pokemon_data(pokemon_name: str, cache_dir: str = "./cache") -> Optional[Tuple[Dict, Dict]]:
    """Fetch Pokémon data and species data, using cache if available."""
    cache_file = os.path.join(cache_dir, f"{pokemon_name.lower()}.json")
    species_cache_file = os.path.join(
        cache_dir, f"{pokemon_name.lower()}_species.json")

    if os.path.exists(cache_file) and os.path.exists(species_cache_file):
        with open(cache_file, 'r') as f:
            pokemon_data = json.load(f)
        with open(species_cache_file, 'r') as f:
            species_data = json.load(f)
        return pokemon_data, species_data

    try:
        # Fetch Pokémon data
        response = requests.get(
            f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}")
        response.raise_for_status()
        pokemon_data = response.json()

        # Fetch species data
        species_url = pokemon_data['species']['url']
        species_response = requests.get(species_url)
        species_response.raise_for_status()
        species_data = species_response.json()

        # Cache the data
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(pokemon_data, f)
        with open(species_cache_file, 'w') as f:
            json.dump(species_data, f)

        return pokemon_data, species_data
    except requests.RequestException as e:
        messagebox.showerror(
            "Error", f"Failed to fetch Pokémon data: {str(e)}")
        return None, None


def load_egg_group_cache(cache_dir: str = "./cache") -> dict:
    """Load or create egg group cache with proper English names."""
    cache_file = os.path.join(cache_dir, "egg_groups.json")

    if os.path.exists(cache_file):
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
        return {}
