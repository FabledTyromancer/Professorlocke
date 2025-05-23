import tkinter as tk
from my_package.ui import QuizUI
from my_package.quiz_logic import check_answer, generate_questions
from my_package.data_fetching import fetch_pokemon_data, load_egg_group_cache
from my_package.utils import meters_to_feet_inches, kg_to_lbs
from my_package.sprite_cacher import cache_sprites
from my_package.professorlockejsongenerator import POKEMON_COUNT
import my_package.cache_clearer as clearer
import os
import winsound
import threading

cache_dir = "professor_cache"

class ProfessorLocke:
    def __init__(self, root):
        self.cache_flag = None
        #starts the main thing
        self.ui = QuizUI(
            root,
            on_start_quiz=self.start_quiz,
            on_prev_question=self.prev_question,
            on_next_question=self.next_question,
            clear_cache=self.clear_cache

        )
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
        sprites_dir = os.path.join(cache_dir, "sprites")
        poke_file = os.path.join(cache_dir, "professordata.json")
        egg_file = os.path.join(cache_dir, "egg_groups.json")

        check_dict = {
            "poke_file": False,
            "sprites_dir": False,
            "egg_groups": False
        }

        if os.path.exists(poke_file): #professordata.json
            check_dict["poke_file"] = True
            self.data = fetch_pokemon_data()

        if os.path.exists(sprites_dir): #sprites directory
                FORM_COUNT = 0
                VARIANT_COUNT = 0
                forms = [f for f in self.data if f.get("forms")]
                formurl = [furl for furl in self.data if furl.get("form_sprite_url")]
                try: 
                    FORM_COUNT += len([1 for form_name, form_url in zip(forms, formurl) if form_url and form_name])
                except Exception as e:
                    print(f"Error calculating FORM_COUNT: {e}")
                variant = [v for v in self.data if v.get("variants")]
                fetchedvariant = [fv for fv in self.data if fv.get("fetched_variants")]
                try:
                    VARIANT_COUNT += len([1 for variant_name, fetched_variant in zip(variant, fetchedvariant) if fetched_variant and variant_name])
                except Exception as e:
                    print(f"Error calculating VARIANT_COUNT: {e}")
                list = os.listdir(sprites_dir)
                spritecount = len(list)
                if spritecount == POKEMON_COUNT + VARIANT_COUNT + FORM_COUNT: #do we have all the sprites? current mon number, tied to the number generating your json.
                    check_dict["sprites_dir"] = True

        if os.path.exists(egg_file): #eggs
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
            else:  #if we don't have it, get it.
                self.set_loading_message("Fetching Pokémon data...")
                self.data = fetch_pokemon_data(status_callback=self.set_fetching_label)
                root.after(300)
            self.set_loading_message("Loading sprites...")
            if self.check_list["sprites_dir"]:
                root.after(100)
            else: #if we don't have it, get it, find everything we're missing, give updates
                self.set_loading_message("Fetching sprites...")
                self.sprite_check = cache_sprites(status_callback=self.set_fetching_label)
                root.after(300)
            self.set_loading_message("Loading egg group cache...")
            if self.check_list["egg_groups"]:
                self.egg_group_cache = load_egg_group_cache()
                root.after(100)
            else:
                self.set_loading_message("Fetching egg group cache...")
                self.egg_group_cache = load_egg_group_cache()
                root.after(300)
            self.set_loading_message("Loading Complete!")
            root.after(200)

            
            self.loading_label.after(0, lambda: self.loading_label.pack_forget())  # Remove loading label when we're done
            self.fetching_label.after(0, lambda: self.fetching_label.pack_forget()) # remove the fetching label now that it's done

            self.cache_flag = True
            self.ui.root.after(0, lambda: self.ui.update_cache_button(self.cache_flag))          

            self.all_pokemon = self.data # set a pool of comparative data
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
        
        # Debug log to show available Pokemon
        self.current_pokemon = next(
            (p for p in self.data if p['name'].lower() == pokemon_name), None) # Find the Pokemon in the data
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
        self.ui.sprite_label.config(image='')  # Clear sprite
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
            winsound.PlaySound(self.ui.correct_sound, winsound.SND_ALIAS | winsound.SND_ASYNC)
        elif close_match:
            self.score += .5
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = ", ".join(correct_answer)
            self.ui.show_feedback(
                f"Partially Correct! The correct answer is:\n{correct_answer}", "orange")
            winsound.PlaySound(self.ui.partial_correct_sound, winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = "\n".join(correct_answer)
            self.ui.show_feedback(
                f"Incorrect! The correct answer is:\n{correct_answer}", "red")
            winsound.PlaySound(self.ui.incorrect_sound, winsound.SND_ALIAS | winsound.SND_ASYNC)


        # Save the user's answer for display
        question["user_answer"] = user_answer
        # ongoing score track
        self.total_questions += 1
        self.answered_questions.add(self.current_question_index)
        self.ui.update_score(self.score, self.total_questions)

        # Show final grade if all questions are answered
        if len(self.answered_questions) == len(self.questions):
            sprite_path = os.path.join("professor_cache", "sprites", f"{self.current_pokemon['name'].lower()}.png")
            self.ui.show_final_grade(
                self.score, self.total_questions, sprite_path)
        else:
            self.show_current_question()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessorLocke(root)
    root.mainloop()