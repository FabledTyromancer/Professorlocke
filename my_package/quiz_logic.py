import requests
import random
from typing import Dict, List, Union, Tuple
from my_package.utils import meters_to_feet_inches, kg_to_lbs
from difflib import SequenceMatcher
import unicodedata


def normalize_string(input_string: str) -> str:
    """Normalize a string by converting to lowercase and removing accents."""
    normalized = unicodedata.normalize('NFD', input_string)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').lower().strip()


def generate_questions(current_pokemon: Dict, species_data: Dict, egg_group_cache: Dict) -> List[Dict]:
    """Generate quiz questions based on Pokémon data."""
    questions = [
        {
            "type": "text",
            "question": f"What is {current_pokemon['name'].title()}'s genus?",
            "answer": next((g['genus'] for g in species_data['genera'] if g['language']['name'] == 'en'), ''),
            "field": "genus"
        },
        {
            "type": "text",
            "question": f"What type(s) is {current_pokemon['name'].title()}?",
            "answer": [t['type']['name'] for t in current_pokemon['types']],
            "field": "type"
        },
        {
            "type": "text",
            "question": f"What is {current_pokemon['name'].title()}'s height in feet and inches? (e.g., 5'11\")",
            "answer": meters_to_feet_inches(current_pokemon['height'] / 10),
            "field": "height"
        },
        {
            "type": "text",
            "question": f"What is {current_pokemon['name'].title()}'s weight in pounds?",
            "answer": round(kg_to_lbs(current_pokemon['weight'] / 10), 1),
            "field": "weight"
        },
        {
            "type": "text",
            "question": f"What egg group(s) does {current_pokemon['name'].title()} belong to?",
            "answer": [egg_group_cache.get(eg['name'], eg['name']) for eg in species_data['egg_groups']],
            "field": "egg_group"
        },
        {
            "type": "text",
            "question": f"What ability/abilities does {current_pokemon['name'].title()} have?",
            "answer": [a['ability']['name'] for a in current_pokemon['abilities']],
            "field": "ability"
        }
    ]

    # Add evolution chain question if available
    if species_data.get('evolution_chain'):
        try:
            evolution_response = requests.get(
                species_data['evolution_chain']['url'])
            evolution_response.raise_for_status()
            evolution_data = evolution_response.json()

            # Process evolution chain logic here (if needed)
            # Add evolution-related questions to the `questions` list
        except requests.RequestException:
            pass

    return questions


def check_boolean_answer(user_answer: bool, correct_answer: bool) -> bool:
    """Check if the boolean answer is correct."""
    return user_answer == correct_answer


def check_list_answer(user_answer: str, correct_answers: List[str], normalize_hyphens: bool = False) -> bool:
    """Check if the user's answer matches a list of correct answers."""
    user_answers = [a.strip().lower() for a in user_answer.split(',')]
    correct_answers = [a.lower() for a in correct_answers]

    if normalize_hyphens:
        user_answers = [a.replace('-', ' ') for a in user_answers]
        correct_answers = [a.replace('-', ' ') for a in correct_answers]

    return any(user_answer in correct_answers for user_answer in user_answers)


def check_set_answer(user_answer: str, correct_answers: List[str]) -> bool:
    """Check if the user's answers match the correct answers as a set (order-independent)."""
    user_answers = set(a.strip().lower() for a in user_answer.split(','))
    correct_answers = set(a.lower() for a in correct_answers)
    return user_answers == correct_answers


def check_height_answer(user_answer: str, correct_height_dm: float, margin: float = 0.15) -> bool:
    """Check if the user's height answer is within the margin of error."""
    try:
        parts = user_answer.split("'")
        if len(parts) == 2:
            feet = float(parts[0])
            inches = float(parts[1].strip('"'))
            total_inches = feet * 12 + inches
            meters = total_inches * 0.0254
            correct_meters = correct_height_dm / 10
            return abs(meters - correct_meters) <= (correct_meters * margin)
    except ValueError:
        return False


def check_weight_answer(user_answer: str, correct_weight_kg: float, margin: float = 0.15) -> bool:
    """Check if the user's weight answer is within the margin of error."""
    try:
        user_value = float(user_answer)
        return abs(user_value - correct_weight_kg) <= (correct_weight_kg * margin)
    except ValueError:
        return False


def check_genus_answer(user_answer: str, correct_genus: str) -> bool:
    """Check if the user's genus answer matches the correct genus."""
    normalized_user_genus = normalize_string(user_answer)
    normalized_correct_genus = normalize_string(
        correct_genus).replace(" pokemon", "").replace(" pokémon", "")
    return normalized_user_genus == normalized_correct_genus


def is_similar_string(user_answer: str, correct_answer: str, threshold: float = 0.8) -> bool:
    """Check if two strings are similar based on a similarity threshold."""
    similarity = SequenceMatcher(None, user_answer.strip(
    ).lower(), correct_answer.strip().lower()).ratio()
    return similarity >= threshold


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
                normalize_hyphens = question["field"] == "ability"
                exact_match = check_list_answer(
                    user_answer, question["answer"], normalize_hyphens)
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
