def meters_to_feet_inches(meters: float) -> str:
    """Convert meters to feet and inches."""
    total_inches = meters * 39.3701
    feet = int(total_inches // 12)
    inches = round(total_inches % 12)
    return f"{feet}'{inches}\""


def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462


def censor_pokemon_names(text: str) -> str:
    """Replace Pokémon names with '***' in text."""
    words = text.split()
    censored_words = []
    for word in words:
        if word[0].isupper() and not any(p in word for p in ['.', '!', '?', ',', ';', ':']):
            censored_words.append('***')
        else:
            censored_words.append(word)
    return ' '.join(censored_words)
