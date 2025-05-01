import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
import random
from typing import Dict, List, Optional, Tuple
import math
import winsound # For correct/incorrect chimes, and the final check, can delete if not interested in sounds
from PIL import Image, ImageTk, ImageOps #for sprite handling
import io
from ctypes import windll # help with resolution, can delete if not streaming/recording

windll.shcore.SetProcessDpiAwareness(1) # help with window scaling, can delete if not streaming/recording

# Define default font, just makes readability and spacing nice
DEFAULT_FONT = ('Arial', 16)

class ProfessorLocke:
    def __init__(self, root):
        self.root = root
        self.root.title("ProfessorLocke")
        self.root.geometry("600x550") # window size

        # Set font
        self.root.option_add('*Font', DEFAULT_FONT) 

        # cache directory
        self.cache_dir = "pokemon_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Egg group cache setup
        self.egg_group_cache = {}
        self.load_egg_group_cache()
        
        # Sound effects
        self.correct_sound = {filepath}  # correct answer sound
        self.incorrect_sound = {filepath}  # incorrect answer sound
        self.victory_theme = {filepath}  # Victory theme
        self.failure_theme = {filepath}  # Failure theme

        # Initialize variables
        self.current_pokemon: Optional[Dict] = None
        self.species_data: Optional[Dict] = None
        self.questions: List[Dict] = []
        self.current_question_index: int = 0
        self.answers: Dict[str, str] = {}
        self.score: int = 0
        self.total_questions: int = 0
        self.answered_questions: set = set()  # Track which questions have been answered
        self.sprite_label: Optional[ttk.Label] = None  # For displaying sprite
        
        self.setup_ui()
        
    def setup_ui(self):
        # Pokemon search frame
        search_frame = ttk.Frame(self.root)
        search_frame.pack(pady=5, padx=10, fill="x")  
        
        ttk.Label(search_frame, text="Pokemon:", font=DEFAULT_FONT).pack(side="left", padx=5)
        self.pokemon_entry = ttk.Entry(search_frame, width=15, font=DEFAULT_FONT)
        self.pokemon_entry.pack(side="left", padx=5)
        self.pokemon_entry.bind('<Return>', lambda e: self.start_quiz())  # Add Enter key binding
        ttk.Button(search_frame, text="Start Quiz", command=self.start_quiz, style='Large.TButton').pack(side="left", padx=5)
        
        # Question frame
        self.question_frame = ttk.Frame(self.root)
        self.question_frame.pack(pady=5, padx=10, fill="both", expand=True)  
        
        # Navigation frame
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(pady=5, padx=10, fill="x") 
        
        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self.prev_question, state="disabled", style='Large.TButton')
        self.prev_button.pack(side="left", padx=5)
        
        self.next_button = ttk.Button(nav_frame, text="Next", command=self.next_question, state="disabled", style='Large.TButton')
        self.next_button.pack(side="right", padx=5)
        
        # Score label
        self.score_label = ttk.Label(self.root, text=f"Score: {self.score}/{self.total_questions}", font=DEFAULT_FONT)
        self.score_label.pack(pady=5) 
        
        # Sprite label
        self.sprite_label = ttk.Label(self.root)
        self.sprite_label.pack(pady=5)  
        
        # Configure styles for buttons
        style = ttk.Style()
        style.configure('Large.TButton', font=DEFAULT_FONT)
        style.configure('Large.TRadiobutton', font=DEFAULT_FONT)

        #configure units to America. 
    def meters_to_feet_inches(self, meters: float) -> str:
        total_inches = meters * 39.3701
        feet = int(total_inches // 12)
        inches = round(total_inches % 12)
        return f"{feet}'{inches}\""
        
    def kg_to_lbs(self, kg: float) -> float:
        return kg * 2.20462
        
    def fetch_pokemon_data(self, pokemon_name: str) -> Optional[Tuple[Dict, Dict]]:
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"{pokemon_name.lower()}.json")
        species_cache_file = os.path.join(self.cache_dir, f"{pokemon_name.lower()}_species.json")
        
        if os.path.exists(cache_file) and os.path.exists(species_cache_file):
            with open(cache_file, 'r') as f:
                pokemon_data = json.load(f)
            with open(species_cache_file, 'r') as f:
                species_data = json.load(f)
            return pokemon_data, species_data
        
        # Fetch from API if not in cache
        try:
            # Fetch Pokemon data
            response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}")
            response.raise_for_status()
            pokemon_data = response.json()
            
            # Fetch species data
            species_url = pokemon_data['species']['url']
            species_response = requests.get(species_url)
            species_response.raise_for_status()
            species_data = species_response.json()
            
            # Cache the data
            with open(cache_file, 'w') as f:
                json.dump(pokemon_data, f)
            with open(species_cache_file, 'w') as f:
                json.dump(species_data, f)
            
            return pokemon_data, species_data
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch Pokemon data: {str(e)}")
            return None, None
            
    def start_quiz(self):
        pokemon_name = self.pokemon_entry.get().strip()
        if not pokemon_name:
            messagebox.showwarning("Warning", "Please enter a Pokemon name")
            return
            
        # Reset variables
        self.answers = {}
        self.score = 0
        self.total_questions = 0
        self.current_question_index = 0
        self.answered_questions.clear()
        self.sprite_label.config(image='')  # Clear sprite
        
        # Fetch Pokemon data
        self.current_pokemon, self.species_data = self.fetch_pokemon_data(pokemon_name)
        if not self.current_pokemon or not self.species_data:
            return
            
        # Generate questions
        self.generate_questions()
        
        # Show first question
        self.show_current_question()
        
    def show_current_question(self):
        # Clear previous question
        for widget in self.question_frame.winfo_children():
            widget.destroy()
            
        if not self.questions:
            return
            
        # Update navigation buttons
        self.prev_button.config(state="normal" if self.current_question_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_question_index < len(self.questions) - 1 else "disabled")
        
        # Show current question
        question = self.questions[self.current_question_index]
        self.create_question_ui(question)
        
        # Check if all questions are answered
        if len(self.answered_questions) == len(self.questions):
            self.show_final_grade()
            
    def prev_question(self):
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.show_current_question()
            
    def next_question(self):
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.show_current_question()

    def show_final_grade(self): # required to progress to end-grade screen
        percentage = round((self.score / self.total_questions) * 100) if self.total_questions > 0 else 0 # this isn't doing anything, but won't progress screen without if/else, seems like

        # Play victory or failure theme based on score
        if percentage >= 75:
            winsound.PlaySound(self.victory_theme, winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            winsound.PlaySound(self.failure_theme, winsound.SND_ALIAS | winsound.SND_ASYNC)
        
        # Fetch and display sprite
        try:
            sprite_url = self.current_pokemon['sprites']['front_default']
            response = requests.get(sprite_url)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                # Convert to grayscale if score is below 75%
                if percentage < 75:
                    image = ImageOps.grayscale(image)
                # Resize sprite to larger size
                image = image.resize((200, 200), Image.Resampling.LANCZOS)
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)
                self.sprite_label.config(image=photo)
                self.sprite_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error loading sprite: {e}")
            
    def censor_pokemon_names(self, text: str) -> str:
        """Replace Pokémon names with '***' in text."""
        # Common Pokémon name patterns (including with spaces and hyphens)
        words = text.split()
        censored_words = []
        for word in words:
            # Check if word looks like a Pokémon name (capitalized and not at start of sentence)
            if word[0].isupper() and not any(p in word for p in ['.', '!', '?', ',', ';', ':']):
                censored_words.append('***')
            else:
                censored_words.append(word)
        return ' '.join(censored_words)
        
    def load_egg_group_cache(self):
        """Load or create egg group cache with proper English names."""
        cache_file = os.path.join(self.cache_dir, "egg_groups.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                self.egg_group_cache = json.load(f)
            return
        try:
            response = requests.get("https://pokeapi.co/api/v2/egg-group")
            response.raise_for_status()
            egg_groups = response.json()['results']
            
            for group in egg_groups:
                group_response = requests.get(group['url'])
                group_response.raise_for_status()
                group_data = group_response.json()
                
                # Get English name from names array
                english_name = next(
                    (name['name'] for name in group_data['names'] if name['language']['name'] == 'en'),
                    group_data['name']
                )
                
                self.egg_group_cache[group_data['name']] = english_name
            # Save to cache file
            with open(cache_file, 'w') as f:
                json.dump(self.egg_group_cache, f)

        except requests.RequestException as e:
            print(f"Error loading egg group cache: {e}")
            # If we can't load the cache, use a basic mapping
            self.egg_group_cache = {
                'monster': 'Monster',
                'water1': 'Water 1',
                'bug': 'Bug',
                'flying': 'Flying',
                'ground': 'Field',
                'fairy': 'Fairy',
                'plant': 'Grass',
                'humanshape': 'Human-Like',
                'water3': 'Water 3',
                'mineral': 'Mineral',
                'indeterminate': 'Amorphous',
                'water2': 'Water 2',
                'ditto': 'Ditto',
                'dragon': 'Dragon',
                'no-eggs': 'No Eggs Discovered'
            }

    def get_egg_group_name(self, group_id: str) -> str:
        """Get the proper English name for an egg group."""
        return self.egg_group_cache.get(group_id, group_id)
        
    def generate_questions(self):
        if not self.current_pokemon or not self.species_data:
            return
            
        # Generate questions based on Pokemon data
        questions = [
            {
                "type": "text",
                "question": f"What is {self.current_pokemon['name'].title()}'s genus?",
                "answer": next((g['genus'] for g in self.species_data['genera'] if g['language']['name'] == 'en'), ''),
                "field": "genus"
            },
            {
                "type": "text",
                "question": f"What type(s) is {self.current_pokemon['name'].title()}?",
                "answer": [t['type']['name'] for t in self.current_pokemon['types']],
                "field": "type"
            },
            {
                "type": "text",
                "question": f"What is {self.current_pokemon['name'].title()}'s height in feet and inches? (e.g., 5'11\")",
                "answer": self.meters_to_feet_inches(self.current_pokemon['height'] / 10),
                "field": "height"
            },
            {
                "type": "text",
                "question": f"What is {self.current_pokemon['name'].title()}'s weight in pounds?",
                "answer": round(self.kg_to_lbs(self.current_pokemon['weight'] / 10), 1),
                "field": "weight"
            },
            {
                "type": "text",
                "question": f"What egg group(s) does {self.current_pokemon['name'].title()} belong to?",
                "answer": [self.get_egg_group_name(eg['name']) for eg in self.species_data['egg_groups']],
                "field": "egg_group"
            },
            {
                "type": "text",
                "question": f"What ability/abilities does {self.current_pokemon['name'].title()} have?",
                "answer": [a['ability']['name'] for a in self.current_pokemon['abilities']],
                "field": "ability"
            }
        ]
        
        # Add evolution chain question if available
        if self.species_data.get('evolution_chain'):
            try:
                evolution_response = requests.get(self.species_data['evolution_chain']['url'])
                evolution_response.raise_for_status()
                evolution_data = evolution_response.json()
                
                # Find the current Pokemon in the evolution chain
                current_species = self.species_data['name']
                evolution_chain = evolution_data['chain']
                
                while evolution_chain['species']['name'] != current_species:
                    if evolution_chain['evolves_to']:
                        evolution_chain = evolution_chain['evolves_to'][0]
                    else:
                        break
                
                if evolution_chain['evolves_to']:
                    answers = []
                    # Process all possible evolution branches
                    for evolution in evolution_chain['evolves_to']:
                        for details in evolution.get('evolution_details', []):
                            trigger = details.get('trigger', {}).get('name', '')
                            
                            # Handle level-up evolutions
                            if trigger == 'level-up':
                                conditions = []
                                conditions.append("level-up")
                                
                                # Add level if specified and not None
                                level = details.get('min_level')
                                if level is not None:
                                    conditions.append(f"at level {level}")
                                
                                # Add time of day if specified
                                if details.get('time_of_day'):
                                    conditions.append(f"during {details['time_of_day']}")
                                
                                # Add held item if specified
                                if details.get('held_item'):
                                    item = details['held_item']['name'].replace('-', ' ').title()
                                    conditions.append(f"while holding {item}")
                                
                                # Add other conditions
                                if details.get('min_happiness'):
                                    conditions.append("with high friendship")
                                elif details.get('min_affection'):
                                    conditions.append("with high affection")
                                elif details.get('relative_physical_stats'):
                                    if details.get('relative_physical_stats') == 1:
                                        conditions.append("with higher attack than defense")
                                    else:
                                        conditions.append("with higher defense than attack")
                                
                                answers.append(" ".join(conditions))
                            
                            # Handle item-based evolutions
                            elif trigger == 'use-item':
                                item = details.get('item', {}).get('name', '').replace('-', ' ').title()
                                if details.get('time_of_day'):
                                    answers.append(f"use {item} during {details['time_of_day']}")
                                else:
                                    answers.append(f"use {item}")
                            
                            # Handle location-based evolutions
                            elif details.get('location'):
                                location = details['location']['name'].replace('-', ' ').title()
                                if self.current_pokemon['name'].lower() == 'eevee':
                                    if location.lower() == 'moss rock':
                                        answers.append("level-up near moss rock")
                                    elif location.lower() == 'ice rock':
                                        answers.append("level-up near ice rock")
                                else:
                                    answers.append(f"level-up at {location}")
                            
                            # Handle trade evolutions
                            elif trigger == 'trade':
                                if details.get('held_item'):
                                    item = details['held_item']['name'].replace('-', ' ').title()
                                    answers.append(f"trade while holding {item}")
                                else:
                                    answers.append("trade")
                    
                    # Remove duplicates while preserving order
                    answers = list(dict.fromkeys(answers))
                    
                    if answers:
                        questions.append({
                            "type": "text",
                            "question": f"How does {self.current_pokemon['name'].title()} evolve? (any possible methods)",
                            "answer": answers,
                            "field": "evolution"
                        })
            except requests.RequestException:
                pass
        
        # Add Pokedex entry question
        pokedex_entries = [e['flavor_text'] for e in self.species_data['flavor_text_entries'] 
                         if e['language']['name'] == 'en']
        if pokedex_entries:
            # Get a random Pokemon for false entry
            random_id = random.randint(1, 1025)  # increased from 151 to others
            try:
                random_response = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{random_id}")
                random_response.raise_for_status()
                random_data = random_response.json()
                random_entries = [e['flavor_text'] for e in random_data['flavor_text_entries'] 
                                if e['language']['name'] == 'en']
                
                if random_entries:
                    # 50% chance of being true
                    is_true = random.random() < 0.5
                    entry = random.choice(pokedex_entries if is_true else random_entries)
                    censored_entry = self.censor_pokemon_names(entry)
                    questions.append({
                        "type": "boolean",
                        "question": f"Is this a Pokedex entry for {self.current_pokemon['name'].title()}?\n{censored_entry}",
                        "answer": is_true,
                        "field": "pokedex"
                    })
            except requests.RequestException:
                pass
        
        self.questions = questions
        
    def create_question_ui(self, question: Dict):
        # Create a grid layout for the question
        self.question_frame.grid_columnconfigure(1, weight=1)
        
        # Question label with larger font
        ttk.Label(self.question_frame, text=question["question"], wraplength=500, font=DEFAULT_FONT).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        
        # Input frame to hold entry and button
        input_frame = ttk.Frame(self.question_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)
        input_frame.grid_columnconfigure(0, weight=1)
        
        if question["type"] == "boolean":
            var = tk.BooleanVar()
            radio_frame = ttk.Frame(self.question_frame)
            radio_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
            ttk.Radiobutton(radio_frame, text="True", variable=var, value=True, style='Large.TRadiobutton').pack(side="left", padx=5)
            ttk.Radiobutton(radio_frame, text="False", variable=var, value=False, style='Large.TRadiobutton').pack(side="left", padx=5)
        else:
            var = tk.StringVar()
            entry = ttk.Entry(input_frame, textvariable=var, width=25, font=DEFAULT_FONT)
            entry.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        result_label = ttk.Label(self.question_frame, text="", font=DEFAULT_FONT, wraplength=600)
        result_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        
        def check_answer():
            # Check if question has already been answered
            if self.current_question_index in self.answered_questions:
                messagebox.showwarning("Warning", "You've already answered this question!")
                return
                
            if question["type"] == "boolean":
                user_answer = var.get()
            else:
                user_answer = var.get().strip().lower()
            
            correct = self.check_answer(user_answer, question)
            
            if correct:
                result_label.config(text="Correct!", foreground="green")
                self.score += 1
                winsound.PlaySound(self.correct_sound, winsound.SND_ALIAS | winsound.SND_ASYNC)
            else:
                if question["field"] == "evolution" and isinstance(question["answer"], list):
                    answer_text = "Possible answers:\n" + "\n".join(f"- {ans}" for ans in question["answer"])
                else:
                    answer_text = f"Incorrect. The correct answer is: {question['answer']}"
                result_label.config(text=answer_text, foreground="red")
                winsound.PlaySound(self.incorrect_sound, winsound.SND_ALIAS | winsound.SND_ASYNC)
            #score
            self.total_questions += 1
            self.score_label.config(text=f"Score: {self.score}/{self.total_questions}")
            
            # Mark question as answered
            self.answered_questions.add(self.current_question_index)
            
            # Disable submit button and entry/radio buttons
            submit_button.config(state="disabled")
            if question["type"] == "boolean":
                for radio in radio_frame.winfo_children():
                    radio.config(state="disabled")
            else:
                entry.config(state="disabled")
            
            # Check if all questions are answered
            if len(self.answered_questions) == len(self.questions):
                self.show_final_grade()
            
        submit_button = ttk.Button(input_frame, text="Submit", command=check_answer, width=8, style='Large.TButton')
        submit_button.grid(row=0, column=1, sticky="e", padx=5)
        
        # Disable submit button if question already answered
        if self.current_question_index in self.answered_questions:
            submit_button.config(state="disabled")
            if question["type"] == "boolean":
                for radio in radio_frame.winfo_children():
                    radio.config(state="disabled")
            else:
                entry.config(state="disabled")
        else:
            # Bind Enter key to submit for unanswered questions
            entry.bind('<Return>', lambda e: check_answer())

            
        # Set focus to entry or first radio button
        if question["type"] == "boolean":
            radio_frame.winfo_children()[0].focus_set()
        else:
            entry.focus_set()

    def check_answer(self, user_answer: str, question: Dict) -> bool:
        if question["type"] == "boolean":
            return user_answer == question["answer"]
        elif question["type"] == "text":
            if isinstance(question["answer"], list):
                # For type and egg group questions, check if all answers are present in any order
                if question["field"] in ["type", "egg_group"]:
                    user_answers = set(a.strip().lower() for a in user_answer.split(','))
                    correct_answers = set(a.lower() for a in question["answer"])
                    print(f"User answers: {user_answers}")  # Debug print
                    print(f"Correct answers: {correct_answers}")  # Debug print
                    return user_answers == correct_answers
                # For ability and evolution questions, check if at least one answer is correct
                elif question["field"] in ["ability", "evolution"]:
                    user_answers = [a.strip().lower() for a in user_answer.split(',')]
                    correct_answers = [a.lower() for a in question["answer"]]
                    # For abilities, normalize both user and correct answers to handle hyphens
                    if question["field"] == "ability":
                        user_answers = [a.replace('-', ' ') for a in user_answers]
                        correct_answers = [a.replace('-', ' ') for a in correct_answers]
                    return any(user_answer in correct_answers for user_answer in user_answers)
            elif question["field"] in ["height", "weight"]:
                try:
                    if question["field"] == "height":
                        # Parse feet and inches format
                        parts = user_answer.split("'")
                        if len(parts) == 2:
                            feet = float(parts[0])
                            inches = float(parts[1].strip('"'))
                            total_inches = feet * 12 + inches
                            meters = total_inches * 0.0254
                            correct_meters = self.current_pokemon['height'] / 10
                            margin = 0.15  # 15% margin of error
                            return abs(meters - correct_meters) <= (correct_meters * margin)
                    else:
                        # Weight in pounds
                        user_value = float(user_answer)
                        correct_value = question["answer"]
                        margin = 0.15  # 15% margin of error
                        return abs(user_value - correct_value) <= (correct_value * margin)
                except ValueError:
                    return False
            elif question["field"] == "genus":
                # Remove "Pokémon" from the genus and compare
                correct_genus = str(question["answer"]).lower()
                if correct_genus.endswith(" pokémon"):
                    correct_genus = correct_genus[:-8]  # Remove " pokémon" from the end
                user_genus = user_answer.lower()
                if user_genus.endswith(" pokemon") or user_genus.endswith(" pokémon"):
                    user_genus = user_genus[:-8]  # Remove " pokemon" or " pokémon" from the end
                return user_genus.strip() == correct_genus.strip()
            else:
                return user_answer == str(question["answer"]).lower()
        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessorLocke(root)
    root.mainloop() 
