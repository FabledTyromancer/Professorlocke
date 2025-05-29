import re
import json
import os

# Global unit system setting
USE_METRIC = True

def load_unit_preference():
    """Load the unit system preference from cache."""
    global USE_METRIC
    cache_dir = "professor_cache"
    util_file = os.path.join(cache_dir, "utility.json")
    
    if os.path.exists(util_file):
        try:
            with open(util_file, 'r') as f:
                data = json.load(f)
                USE_METRIC = data.get('use_metric', True)
        except:
            USE_METRIC = True
    return USE_METRIC

def save_unit_preference(use_metric: bool):
    """Save the unit system preference to cache."""
    cache_dir = "professor_cache"
    util_file = os.path.join(cache_dir, "utility.json")
    
    try:
        os.makedirs(cache_dir, exist_ok=True)
        # Load existing data if file exists
        data = {}
        if os.path.exists(util_file):
            try:
                with open(util_file, 'r') as f:
                    data = json.load(f)
            except:
                pass
        
        # Update unit preference while preserving other data
        data['use_metric'] = use_metric
        
        with open(util_file, 'w') as f:
            json.dump(data, f)
    except:
        pass

def set_unit_system(use_metric: bool):
    """Set the unit system to use (True for metric, False for imperial)."""
    global USE_METRIC
    USE_METRIC = use_metric
    save_unit_preference(use_metric)

def meters_to_feet_inches(meters: float) -> str:
    """Convert meters to feet and inches."""
    total_inches = meters * 39.3701
    feet = int(total_inches // 12)
    inches = round(total_inches % 12)
    return f"{feet}'{inches}\""

def format_height(height_dm: float) -> str:
    """Format height based on the current unit system."""
    height_m = height_dm / 10
    if USE_METRIC:
        return f"{height_m:.1f}m"
    else:
        return meters_to_feet_inches(height_m)

def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462

def format_weight(weight_kg: float) -> float:
    """Format weight based on the current unit system."""
    if USE_METRIC:
        return f"{weight_kg:.1f}kg"
    else:
        return f"{round(kg_to_lbs(weight_kg), 1)}lbs"

def get_base_name(name: str) -> str:
    """Extract the base name from a Pokémon name, handling regional variants."""
    name = name.lower()  # Convert to lowercase for consistent comparison
    
    # Handle regional variants and forms in format "pokemon-form"
    for suffix in ["-alola", "-galar", "-hisui", "-paldea", "-shield", "-blade", "-normal", "-altered", "-land", "-sky", "-incarnate", "-therian", "-primal", "-origin", "-mega", "-mega-x", "-mega-y"]:
        if name.endswith(suffix):
            return name[:-len(suffix)]  # Remove the suffix
    
    # Handle regional variants in format "pokemon (region)"
    match = re.match(r"(.+?)\s*\(([^)]+)\)", name)
    if match:
        return match.group(1).strip()
    
    return name

def censor_pokemon_names(text: str, names_to_censor=None) -> str:
    """Replace Pokémon names with '***' in text, handling both base names and regional variants."""
    if not names_to_censor:
        return text
    
    # Create patterns for both the full name and base name
    patterns = []
    for name in names_to_censor:
        base_name = get_base_name(name)
        # Add pattern for the full name
        patterns.append(re.escape(name))
        # Add pattern for the base name if it's different from the full name
        if base_name != name:
            patterns.append(re.escape(base_name))
            # Also add the base name with proper capitalization
            patterns.append(re.escape(base_name.title()))
    
    # Create the final pattern with all variations
    pattern = r'\b(' + '|'.join(patterns) + r')\b'
    return re.sub(pattern, "***", text, flags=re.IGNORECASE)