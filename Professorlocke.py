import tkinter as tk
from my_package.ui import QuizUI
from my_package.quiz_logic import check_answer, generate_questions
from my_package.data_fetching import fetch_pokemon_data, load_egg_group_cache
from my_package.utils import meters_to_feet_inches, kg_to_lbs, set_unit_system, load_unit_preference
import my_package.cache_clearer as clearer
import os
import threading
import json
import re

cache_dir = "professor_cache"

#memory tracking, uncomment at top and bottom to run
#import tracemalloc
#tracemalloc.start()




class ProfessorLocke:
    def __init__(self, root):
        self.cache_flag = None
        # Load unit preference
        use_metric = load_unit_preference()
        #starts the main thing
        self.ui = QuizUI(
            root,
            on_start_quiz=self.start_quiz,
            on_prev_question=self.prev_question,
            on_next_question=self.next_question,
            clear_cache=self.clear_cache,
            on_unit_toggle=self.toggle_unit_system
        )
        # Set initial unit preference
        self.ui.unit_var.set(use_metric)
        self.ui.unit_button.config(text="m/kg" if use_metric else "ft-in/lbs")
        set_unit_system(use_metric)
        # label for loading data to display current status
        self.loading_label = tk.Label(root, text="", font=("Arial", 16), fg="blue")
        self.loading_label.pack(pady=10)
        # label for fetching data to display current status underneath loading label
        self.fetching_label = tk.Label(root, text="", font=("Arial", 16))
        self.fetching_label.pack(pady=10)

        # Show loading message before starting data checks and download(s)
        self.set_loading_message("Initializing...")
        self.check_data(cache_dir)
        self.check_list = self.check_data(cache_dir) # what data we need to download
        root.after(100, self.load_data) #load/download depending on check list

    #checks data, returns "true" to dict
    def check_data(self, cache_dir):
        poke_file = os.path.join(cache_dir, "professordata.json")
        egg_file = os.path.join(cache_dir, "egg_groups.json")

        check_dict = {
            "poke_file": False,
            "egg_groups": False
        }

        if os.path.exists(poke_file): #professordata.json
            check_dict["poke_file"] = True


        if os.path.exists(egg_file): #egg groups to modern english names
            check_dict["egg_groups"] = True

        return check_dict



    # data checks and downloads, from package, to show it's working and when it's ready
    def load_data(self):
        def task():
            self.loading_label.after(0, lambda:self.loading_label.pack(pady=10))        
            self.fetching_label.after(0, lambda:self.fetching_label.pack(pady=10))
            self.set_loading_message("Loading Pokémon data...")
            if self.check_list["poke_file"]:  #if we have it, load it, but faster.
                self.data = fetch_pokemon_data()
                root.after(100)
            else:
                self.set_loading_message("Redownload or move cache, professordata.json not found")
            self.set_loading_message("Loading egg group cache...")
            if self.check_list["egg_groups"]:
                self.egg_group_cache = load_egg_group_cache()
                root.after(100)
            else:
                self.set_loading_message("Redownload or move cache, egg_groups.json not found")

            self.set_loading_message("Loading Complete!")
            root.after(200)

            
            self.loading_label.after(0, lambda: self.loading_label.pack_forget())  # Remove loading label when we're done
            self.fetching_label.after(0, lambda: self.fetching_label.pack_forget()) # remove the fetching label now that it's done

            self.cache_flag = True
            self.ui.root.after(0, lambda: self.ui.update_cache_button(self.cache_flag))          

            self.all_pokemon = self.data # set a pool of comparative data, for pokedex entries, but could be used to generate a random mon to do taller/shorter, heavier/lighter or other comparisons.
            self.current_pokemon = None
            self.current_question_index = 0
            self.score = 0
            self.total_questions = 0
            self.answered_questions = set()
            self.leniency = 0.15  # Numerical leniency in percentage
                # String similarity threshold in percentage
            self.string_similarity_threshold = 0.7
            self.ui.update_score(self.score, self.total_questions)

        threading.Thread(target=task, daemon=True).start() # runs the load data function in a separate thread to avoid freezing the UI or holding it up so the labels will update
#updates overall loading data status
    def set_loading_message(self, message: str):
        self.loading_label.config(text="")
        self.loading_label.update_idletasks()
        self.loading_label.config(text=message)
        self.loading_label.update_idletasks()
        self.loading_label.after(0, lambda: self.loading_label.config(text=message))
#updates specific loading data status
    def set_fetching_label(self, msg: str):
        self.fetching_label.config(text="")
        self.fetching_label.update_idletasks()
        self.fetching_label.config(text=msg)
        self.fetching_label.update_idletasks()
        self.fetching_label.after(0, lambda: self.fetching_label.config(text=msg))

    def start_quiz(self, pokemon_name: str):
        if not pokemon_name.strip():
            self.ui.show_feedback("Please enter a Pokemon name!", "red") # error if no name is entered
            return
        # Set current pokemon and generate questions
        pokemon_name = pokemon_name.lower().strip() # Normalize input
        print(f"Searching for Pokemon: {pokemon_name}")  # Debug log
        
        # Handle regional variant names in both formats; Vulpix (Alola) vs vulpix-alola
            # First try direct match
        self.current_pokemon = next(
            (p for p in self.data if p['name'].lower() == pokemon_name), None)
            
            # If not found, try converting from "pokemon (region)" format to "pokemon-region"
        if not self.current_pokemon:
            match = re.match(r"(.+?)\s*\(([^)]+)\)", pokemon_name)
            if match:
                base_name, region = match.groups()
                formatted_name = f"{base_name.strip()}-{region.strip().lower()}"
                self.current_pokemon = next(
                    (p for p in self.data if p['name'].lower() == formatted_name), None)
        
        if not self.current_pokemon: # If not found, show error, clear quiz frame (because of unknowable bugs that i don't want to solve), and reset the quiz
            self.ui.show_feedback("Pokemon not found.", "orange")
            self.reset_quiz()
            return
        
        print(f"Found Pokemon: {self.current_pokemon['name']}")  # Debug log 

        # Reset quiz state
        self.reset_quiz()

        self.questions = generate_questions(
            self.current_pokemon, self.egg_group_cache, self.all_pokemon)

        # Show the first question
        self.show_current_question()
    # lol function because i'm using it in a few places and got lazy
    def reset_quiz(self):
        self.score = 0
        self.total_questions = 0
        self.current_question_index = 0
        self.questions = []
        self.answered_questions.clear()
        self.ui.clear_question_frame()  # Clear previous questions
    #go backwards in list
    def prev_question(self):
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.show_current_question()
    #go forwards in list
    def next_question(self):
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.show_current_question()
    # Delete cache function for the button
    def clear_cache(self):
        def clear():
            if self.cache_flag:
                clearer.main(status_callback=self.set_loading_message)
                self.cache_flag = False #says we don't have a cache, disabling the button
                self.check_list = self.check_data(cache_dir) # Rebuild list of directories
                root.after(100, self.load_data) # Reload data
            else:
                print(f"no cache to clear")
        threading.Thread(target=clear, daemon=True).start() # threading to work easier.
    
        

    #show the current question
    def show_current_question(self):
        question = self.questions[self.current_question_index]
        self.ui.show_question(
            question,
            on_submit=self.submit_answer,
            answered=self.current_question_index in self.answered_questions
        )
        # updates buttons 
        self.ui.update_navigation_buttons(
            can_go_prev=self.current_question_index > 0,
            can_go_next=self.current_question_index < len(self.questions) - 1
        )

        self.ui.update_cache_button(
            cache_issue = self.cache_flag
        )
    
    # you probably get the gist, answer submits
    def submit_answer(self, user_answer: str):
        question = self.questions[self.current_question_index]
        exact_match, close_match = check_answer(
            user_answer, question, self.current_pokemon, self.leniency, self.string_similarity_threshold)

        # Display feedback based on the result
        if exact_match:
            self.score += 1
            self.ui.show_feedback("Correct!", "green")
        elif close_match:
            self.score += .5
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = ", ".join(correct_answer)
            self.ui.show_feedback(
                f"Partially Correct! The correct answer is:\n{correct_answer}", "orange")
        else:
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = "\n".join(correct_answer)
            self.ui.show_feedback(
                f"Incorrect! The correct answer is:\n{correct_answer}", "red")


        # Save the user's answer for display
        question["user_answer"] = user_answer
        # ongoing score track
        self.total_questions += 1
        self.answered_questions.add(self.current_question_index)
        self.ui.update_score(self.score, self.total_questions)

        # Show final grade if all questions are answered
        if len(self.answered_questions) == len(self.questions):
            self.ui.show_final_grade(
                self.score, self.total_questions)
        else:
            self.show_current_question()

    def toggle_unit_system(self, use_metric: bool):
        """Toggle between metric and imperial units."""
        set_unit_system(use_metric)
        # If we have a current quiz, regenerate questions with new units
        if self.current_pokemon:
            self.questions = generate_questions(
                self.current_pokemon, self.egg_group_cache, self.all_pokemon)
            self.show_current_question()

    
    


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessorLocke(root)
    root.mainloop()

#end of memory tracking, returns results when application closes
#current, peak = tracemalloc.get_traced_memory()
#print(f"Current memory usage: {current / (1024 * 1024)} MB")
#print(f"Peak memory usage: {peak / (1024 * 1024)} MB")
#tracemalloc.stop()