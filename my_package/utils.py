import re

def meters_to_feet_inches(meters: float) -> str:
    """Convert meters to feet and inches."""
    total_inches = meters * 39.3701
    feet = int(total_inches // 12)
    inches = round(total_inches % 12)
    return f"{feet}'{inches}\""


def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462

#censor function, name based
def censor_pokemon_names(text: str, names_to_censor=None) -> str:
    """Replace Pokémon names with '***' in text."""
    if not names_to_censor:
        return text
    pattern = r'\b(' + '|'.join(re.escape(name) for name in names_to_censor) + r')\b'
    return re.sub(pattern, "***", text, flags=re.IGNORECASE)