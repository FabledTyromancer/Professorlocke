import random
from typing import Dict, List, Union, Tuple
from my_package.utils import format_height, format_weight, censor_pokemon_names, USE_METRIC
from difflib import SequenceMatcher
import unicodedata
import re

def normalize_string(input_string: str) -> str:
    """Normalize a string by converting to lowercase and removing accents."""
    normalized = unicodedata.normalize('NFD', input_string)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').lower().strip()

def format_pokemon_name(name: str) -> str:
    """Format a Pokémon name to display regional variants in a user-friendly way."""
    # Convert to lowercase for consistent comparison
    name = name.lower()
    
    # Handle regional variants in format "pokemon-region"
    for region in ["alola", "galar", "hisui", "paldea"]:
        if name.endswith(f"-{region}"):
            base_name = name[:-len(region)-1]  # Remove "-region"
            return f"{base_name.title()} ({region.title()})"
    
    return name.title()

def generate_questions(pokemon: Dict, egg_group_cache: Dict, all_pokemon: List[Dict]) -> List[Dict]:
    """Generate quiz questions based on Pokémon data."""
    # Format the Pokémon name for display
    display_name = format_pokemon_name(pokemon.get('name'))
    
    questions = [
        {
            "type": "text",
            "question": f"What is {display_name}'s genus?",
            "answer": pokemon['genus'][0] if pokemon['genus'] else "unknown",
            "field": "genus"
        },
        {
            "type": "text",
            "question": f"What type(s) is {display_name}?",
            "answer": pokemon.get('types', []),
            "field": "type"
        },
        {
            "type": "text",
            "question": f"What is {display_name}'s height?",
            "answer": format_height(pokemon.get('height')),
            "field": "height"
        },
        {
            "type": "text",
            "question": f"What is {display_name}'s weight?",
            "answer": format_weight(pokemon.get('weight') / 10),
            "field": "weight"
        },
        {
            "type": "text",
            "question": f"What egg group(s) does {display_name} belong to?",
            "answer": [egg_group_cache.get(eg, eg) for eg in pokemon['egg_groups']],
            "field": "egg_group"
        },
        {
            "type": "text",
            "question": f"What ability/abilities does {display_name} have?",
            "answer": [a['name'] for a in pokemon['abilities']],
            "field": "ability"
        }

    ]

    # Add evolution chain question if available
    evo_details = pokemon.get('evolution_chain_details', [])
    if evo_details:
        methods = []
        base_name = pokemon['name']
        for suffix in ["-alola", "-galar", "-hisui", "-paldea"]:
            if base_name.endswith(suffix):
                base_name = base_name.removesuffix(suffix)
        # Only include evolutions where the 'from' is the current Pokémon
        for evo in evo_details:
            if evo.lower().startswith(base_name.lower() + " to "):
                # The answer is the part after the colon and space
                parts = evo.split(": ", 1)
                if len(parts) > 1:
                    methods.append(parts[1])
        if methods: #only add if it evolves
            questions.append(
                {
                    "type": "text",
                    "question": f"How does {display_name} evolve (any method)?",
                    "answer": methods,
                    "field": "evolution"
                }
            )

    # get a random flavor text from our pokemon or from all_pokemon, then censor pokemon names.
    flavor_texts = pokemon.get('flavor_text', [])
    if flavor_texts:
        use_current = random.random() < .65 # weight to decide current pokemon or a random one
        if use_current:
            chosen_text = random.choice(flavor_texts) #picks a random entry
            names_to_censor = [pokemon['name']]
            censored_entry = censor_pokemon_names(chosen_text, names_to_censor)
            correct_answer = True
        else:
            other_pokemon = random.choice([p for p in all_pokemon if p['name'] != pokemon['name']])
            flavor_pokemon_name = other_pokemon['name']
            other_flavor_texts = other_pokemon.get('flavor_text', [])
            if other_flavor_texts:
                chosen_text = random.choice(other_flavor_texts)
                names_to_censor = [pokemon['name'], flavor_pokemon_name]
                censored_entry = censor_pokemon_names(chosen_text, names_to_censor)
                correct_answer = False
            else:
                chosen_text = random.choice(flavor_texts)
                correct_answer = True
        #adds this question to the list with the information above.
        questions.append(
            {
                "type": "boolean",
                "question": f"Is this a Pokédex entry for {display_name}? {censored_entry}",
                "answer": correct_answer,
                "field": "flavor_text"
            }
        )

    return questions

# for boolean questions
def check_boolean_answer(user_answer: bool, correct_answer: bool) -> bool:
    """Check if the boolean answer is correct."""
    return user_answer == correct_answer

# for multiple correct answers, one
def check_list_answer(user_answer: str, correct_answers: List[str], normalize_hyphens: bool = False) -> bool:
    """Check if the user's answer matches a list of correct answers."""
    user_answers = [a.strip().lower() for a in user_answer.split(',')]
    correct_answers = [a.lower() for a in correct_answers]

    if normalize_hyphens:
        user_answers = [a.replace('-', ' ') for a in user_answers]
        correct_answers = [a.replace('-', ' ') for a in correct_answers]

    return any(user_answer in correct_answers for user_answer in user_answers)

# for order independent answering (a + b or b + a, but both needed)
def check_set_answer(user_answer: str, correct_answers: List[str]) -> bool:
    """Check if the user's answers match the correct answers as a set (order-independent)."""
    user_answers = set(a.strip().lower() for a in user_answer.split(','))
    correct_answers = set(a.lower() for a in correct_answers)
    return user_answers == correct_answers


def check_height_answer(user_answer: str, correct_height_dm: float, margin: float = 0.15) -> bool:
    """Check if the user's height answer is within the margin of error."""
    try:
        # First try to parse as imperial (feet'inches")
        if "'" in user_answer:
            parts = user_answer.split("'")
            if len(parts) != 2:
                return False
            feet = float(parts[0])
            inches = float(parts[1].strip('"'))
            total_inches = feet * 12 + inches
            user_meters = total_inches * 0.0254
            correct_meters = correct_height_dm / 10
            print(f"Imperial check - User: {feet}'{inches}\", Correct: {correct_meters}m")
            return abs(user_meters - correct_meters) <= (correct_meters * margin)
        else:
            # Try to parse as metric
            user_value = float(''.join(c for c in user_answer if c.isdigit() or c == '.'))
            correct_meters = correct_height_dm / 10
            print(f"Metric check - User: {user_value}m, Correct: {correct_meters}m")
            return abs(user_value - correct_meters) <= (correct_meters * margin)
    except ValueError as e:
        print(f"Error parsing height: {e}")
        return False


def check_weight_answer(user_answer: str, correct_answer: str, margin: float = 0.15) -> bool:
    """Check if the user's weight answer is within the margin of error."""
    try:
        # Extract numeric values from both answers, ignoring units and rounding to integers
        user_value = round(float(''.join(c for c in user_answer if c.isdigit() or c == '.')))
        correct_value = round(float(''.join(c for c in correct_answer if c.isdigit() or c == '.')))
        
        return abs(user_value - correct_value) <= (correct_value * margin)
    except ValueError:
        return False

# ignore "pokemon" at the end of the genus
def check_genus_answer(user_answer: str, correct_genus: str) -> bool:
    """Check if the user's genus answer matches the correct genus."""
    normalized_user_genus = normalize_string(user_answer)
    normalized_correct_genus = normalize_string(
        correct_genus).replace(" pokemon", "").replace(" pokémon", "")
    return normalized_user_genus == normalized_correct_genus

# spelling/error tolerance
def is_similar_string(user_answer: str, correct_answer: str, threshold: float = 0.8) -> bool:
    """Check if two strings are similar based on a similarity threshold."""
    # check if "level-up at level" and compare for similarity
    user_level = extract_level(user_answer)
    correct_level = extract_level(correct_answer)
    if user_level is not None and correct_level is not None:
        if abs(user_level - correct_level) <= 1: #if you only want to get exact level matches, set this to 0, or comment the code out entirely
            return True
        else:
            return False

    similarity = SequenceMatcher(None, user_answer.strip(
    ).lower(), correct_answer.strip().lower()).ratio()
    return similarity >= threshold
# pull out levels to compare for similarity
def extract_level(s: str):
    match = re.search(r'level\s*(?:up\s*at\s*)?level\s*(\d+)', s.lower())
    if match:
        return int(match.group(1))
    return None

def check_answer(user_answer: Union[str, bool], question: Dict, current_pokemon: Dict, leniency: float = 0.15, string_similarity_threshold: float = 0.8) -> Tuple[bool, bool]:
    """Main function to check the user's answer based on the question type."""
    exact_match = False
    close_match = False

    if question["type"] == "boolean":
        exact_match = check_boolean_answer(user_answer, question["answer"])
    elif question["type"] == "text":
        if isinstance(question["answer"], list):
            if question["field"] in ["type", "egg_group"]:
                exact_match = check_set_answer(user_answer, question["answer"])
                if not exact_match:
                    user_answers = set(a.strip().lower()
                                       for a in user_answer.split(','))
                    correct_answers = set(a.lower()
                                          for a in question["answer"])
                    close_match = any(
                        is_similar_string(
                            user, correct, threshold=string_similarity_threshold)
                        for user in user_answers
                        for correct in correct_answers
                    )
            elif question["field"] in ["ability", "evolution"]:
                normalize_hyphens = question["field"] == "ability" or question["field"] == "evolution"
                exact_match = check_list_answer(
                    user_answer, question["answer"], normalize_hyphens)
                if not exact_match:
                    user_answers = [a.strip().lower().replace('-', ' ') for a in user_answer.split(',')]
                    correct_answers = [a.lower().replace('-', ' ') for a in question["answer"]]
                    close_match = any(
                        is_similar_string(
                            user, correct, threshold=string_similarity_threshold)
                        for user in user_answers
                        for correct in correct_answers
                    )

        elif question["field"] == "height":
            exact_match = check_height_answer(
                user_answer, current_pokemon['height'], leniency)
        elif question["field"] == "weight":
            exact_match = check_weight_answer(
                user_answer, question["answer"], leniency)
        elif question["field"] == "genus":
            # Use the updated check_genus_answer function
            exact_match = check_genus_answer(user_answer, question["answer"])
            if not exact_match:
                close_match = is_similar_string(
                    user_answer, question["answer"], threshold=string_similarity_threshold)
        else:
            exact_match = user_answer.strip().lower() == str(
                question["answer"]).strip().lower()
            if not exact_match:
                close_match = is_similar_string(user_answer, str(
                    question["answer"]), threshold=string_similarity_threshold)

    return exact_match, close_match
