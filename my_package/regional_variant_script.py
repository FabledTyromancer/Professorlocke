import re
import requests
import time


API_BASE = "https://pokeapi.co/api/v2/"
# same as json generator; if you add more to json generator, you'll want to add it here as well
def get_pokemon_entry(id, spec_id=None, status_callback=None):
    try:
        pokemon_resp = requests.get(API_BASE + f"pokemon/{id}").json() # we hold off on assigning species, as we need to pull it from the variant page, since it can't be passed normally

        name = pokemon_resp["name"]
        types = [t["type"]["name"] for t in pokemon_resp["types"]]
        abilities = []
        for a in pokemon_resp["abilities"]:
            ability_name = a["ability"]["name"]
            ability_effect = get_ability_effect(ability_name)
            abilities.append({
                "name": ability_name,
                "short_effect": ability_effect
            })
        height = pokemon_resp["height"]
        weight = pokemon_resp["weight"]
        held_items = [item["item"]["name"]
                      for item in pokemon_resp["held_items"]]
        sprite = pokemon_resp["sprites"]["front_default"]
        #so we move all the pokemon_resp stuff up, then we extract the species ID from the URL
        spec_url = pokemon_resp["species"]["url"]
        spec_id = extract_spec_id_from_url(spec_url) #here's where the magic happens
        species_resp = requests.get(API_BASE + f"pokemon-species/{spec_id}").json() #now we can pull species for those deets
        GENUS_OVERRIDES = {
            "ponyta-galar": ["Unique Horn Pok\u00e9mon"],
            "rapidash-galar": ["Unique Horn Pok\u00e9mon"], 
            "growlithe-hisui": ["Scout Pok\u00e9mon"], 
            "voltorb-hisui": ["Sphere Pok\u00e9mon"], 
            "electrode-hisui": ["Sphere Pok\u00e9mon"], 
            "mr-mime-galar": ["Dancing Pok\u00e9mon"], 
            "articuno-galar": ["Cruel Pok\u00e9mon"], 
            "zapdos-galar": ["Strong Legs Pok\u00e9mon"], 
            "moltres-galar": ["Malevolent Pok\u00e9mon"],
            "typholosion-hisui": ["Ghost Flame Pok\u00e9mon"],
            "wooper-paldea": ["Mud Fish Pok\u00e9mon"],
            "slowking-galar": ["Hexpert Pok\u00e9mon"],
            "lilligant-hisui": ["Spinning Pok\u00e9mon"],
            "darumanitan-galar": ["Zen Charm Pok\u00e9mon"],
            "zorua-hisui": ["Spiteful Fox Pok\u00e9mon"],
            "zoroark-hisui": ["Baneful Fox Pok\u00e9mon"],
            "braviary-hisui": ["Battle Cry Pok\u00e9mon"],
            "sliggoo-hisui": ["Snail Pok\u00e9mon"],
            "goodra-hisui": ["Shell Bunker Pok\u00e9mon"]
        } #so genuses are encoded at the species level in the API. This fixes the few bugs as a result.
        # If new regions add new regional forms that use the same species but have different genuses, you'll need to manually add them.

        genus = []
        for gen in species_resp["genera"]:
            if gen.get("language", {}).get("name") == "en":  # Ensure it's in English
                genus.append(gen["genus"])
        if name in GENUS_OVERRIDES: # if needs genus fix,
            genus = GENUS_OVERRIDES[name] #apply genus fix

        # from here it's largely the same as the base script, hence original base script notes.
        # I can only copy paste and delete stuff so much

        #fetch egg groups
        egg_groups = [e["name"] for e in species_resp["egg_groups"]]

        #fetch dex entries
        flavor_texts = []  # Create a list to store all English flavor texts
        flavor_text_entries = species_resp.get("flavor_text_entries", [])
        for f in flavor_text_entries:
                if f.get("language", {}).get("name") == "en":  # Ensure it's in English
                    flavor_texts.append(f.get("flavor_text", ""))  # Append to the list
                    flavor_texts = list(set(flavor_texts))  # Remove duplicates

        #fetch evolution chain (all entries) and details
        evolution_chain = []
        if "evolution_chain" in species_resp and species_resp["evolution_chain"]["url"]:
            evo_chain_url = species_resp["evolution_chain"]["url"]
            evo_chain_data = requests.get(evo_chain_url).json()
            evolution_chain = extract_evolution_chain(evo_chain_data["chain"])
            triggers = extract_evolution_chain_details(evo_chain_data["chain"])

        #if you pull more data from a pokemon, you'll have to add it here, as this is the json build
        return {
            "id": id,  # Add the Pokémon ID here
            "name": name,
            "genus": genus,
            "flavor_text": flavor_texts,
            "types": types,
            "abilities": abilities,
            "height": height,
            "weight": weight,
            "egg_groups": egg_groups,
            "held_items": held_items,
            "evolution_chain": evolution_chain,
            "evolution_chain_details": triggers,
            "sprite_url": sprite,
            
        } # no forms or variants here, as they should be covered in the base script. If we come to needing it, we can add it in similarly, but stuff will get real dicey
    except Exception as e:
        print(f"Error fetching Pokémon ID {id}: {e}")
        if status_callback:
            status_callback(f"Error fetching Pokémon ID {id}: {e}")
        return None

def get_ability_effect(ability_name):
    """Fetch the short_effect of an ability by its name."""
    try:
        ability_resp = requests.get(
            API_BASE + f"ability/{ability_name}").json()
        effect_entries = ability_resp.get("effect_entries", [])
        for entry in effect_entries:
            if entry.get("language", {}).get("name") == "en":  # Ensure it's in English
                return entry.get("short_effect", "No effect description available.")
        return "No effect description available."
    except Exception as e:
        print(f"Error fetching ability {ability_name}: {e}")
        return "Error fetching effect."

def extract_evolution_chain(chain):
    evolutions = []
    

    def recurse(chain_link):
        if chain_link:
            evolutions.append(chain_link["species"]["name"])
            for evo in chain_link.get("evolves_to", []):
                    recurse(evo)
    recurse(chain)
    return evolutions

def extract_evolution_chain_details(chain):
    triggers = []
    
    def find_next_evolution(evolution_details):
        if not evolution_details:
            return
        #ensures we're pulling for our pokemon in question         
        current_species = evolution_details.get("species", {}).get("name", "unknown")
        #separates evolution for current pokemon and evolution target, then proceeds through sorting that information for text entries
        for evo in evolution_details.get("evolves_to", []):
            evolution_data = evo.get("evolution_details", [])
            evolves_to = evo.get("species", {}).get("name", "unknown")
            
            if evolution_data:
                for detail in evolution_data:
                    trigger_desc = f"{current_species} to {evolves_to}: "
                    trigger_info = detail.get("trigger", {}).get("name", "unknown")

                    # Base trigger
                    trigger_desc += trigger_info
                    
                    # Level requirement
                    if detail.get("min_level"):
                        trigger_desc += f" at level {detail['min_level']}"
                    
                    # Item usage
                    if detail.get("item"):
                        item_name = detail["item"]["name"].replace("-", " ")
                        trigger_desc = f"{current_species} to {evolves_to}: use a {item_name}"
                    
                    # Gender requirement
                    if detail.get("gender") is not None:
                        gender = "female" if detail["gender"] == 1 else "male"
                        trigger_desc += f" ({gender} only)"
                    
                    # Held item
                    if detail.get("held_item"):
                        held_item_name = detail["held_item"]["name"].replace("-", " ")
                        trigger_desc += f" while holding {held_item_name}"
                    
                    # Known move
                    if detail.get("known_move"):
                        trigger_desc += f" knowing {detail['known_move']['name']}"
                    
                    # Known move type
                    if detail.get("known_move_type"):
                        trigger_desc += f" knowing a {detail['known_move_type']['name']} move"
                    
                    # Location
                    if detail.get("location"):
                        location_name = detail["location"]["name"].replace("-", " ")
                        trigger_desc += f" at {location_name}"
                    
                    # Affection/Beauty
                    if detail.get("min_affection"):
                        trigger_desc += f" with high affection"
                    if detail.get("min_beauty"):
                        trigger_desc += f" with high beauty"
                    
                    # Happiness
                    if detail.get("min_happiness"):
                        trigger_desc += f" with high happiness"
                    
                    # Weather
                    if detail.get("needs_overworld_rain"):
                        trigger_desc += " while raining"
                    
                    # Party requirements
                    if detail.get("party_species"):
                        trigger_desc += f" with {detail['party_species']['name']} in party"
                    if detail.get("party_type"):
                        trigger_desc += f" with a {detail['party_type']['name']} type in party"
                    
                    # Stats comparison
                    if detail.get("relative_physical_stats") is not None:
                        stat_relation = {-1: "higher Defense than Attack", 0: "equal Attack and Defense", 1: "higher Attack than Defense"}
                        trigger_desc += f" with {stat_relation[detail['relative_physical_stats']]}"
                    
                    # Time of day
                    if detail.get("time_of_day"):
                        trigger_desc += f" during {detail['time_of_day']}"
                    
                    # Trade species
                    if detail.get("trade_species"):
                        trigger_desc += f" when traded for {detail['trade_species']['name']}"
                    
                    # Turn upside down
                    if detail.get("turn_upside_down"):
                        trigger_desc += " while holding console upside down"
                    
                    triggers.append(trigger_desc)

            find_next_evolution(evo)
                
    find_next_evolution(chain)
    return triggers

# Clean up the evolution details for stones to make it not "use-item using x" for human readability
def clean_evolution_detail(detail):
    # For "use-item using X-stone" → "use a X stone"
    match = re.match(r"use-item using ([\w-]+)", detail)
    if match:
        item = match.group(1).replace("-", " ")
        return f"use a {item}"
    # You can add more rules for other patterns if needed
    return detail



# needed to handle pokemon to species for variants, as variants are the same species.
def extract_spec_id_from_url(url):
    match = re.search(r'/pokemon-species/(\d+)/', url)
    if match:
        return int(match.group(1))
    return None

def main(fetched_variants: list, status_callback=None):
    all_forms = []
    VARIANT_COUNT = len(all_forms)
    for i in fetched_variants:
        msg = f"Fetching Pokémon variety {i}/{VARIANT_COUNT}..."
        print(msg)
        if status_callback:
            status_callback(msg)
        entry = get_pokemon_entry(i, status_callback)
        if entry:
            all_forms.append(entry)
        time.sleep(.5)
    return all_forms #sends it back
