import tkinter as tk
from my_package.ui import QuizUI
from my_package.quiz_logic import check_answer, generate_questions
from my_package.data_fetching import fetch_pokemon_data, load_egg_group_cache
from my_package.utils import meters_to_feet_inches, kg_to_lbs
from my_package.sprite_cacher import cache_sprites
import os
import winsound
import threading


class ProfessorLocke:
    def __init__(self, root):
        self.ui = QuizUI(
            root,
            on_start_quiz=self.start_quiz,
            on_prev_question=self.prev_question,
            on_next_question=self.next_question
        )

        self.loading_label = tk.Label(root, text="", font=("Arial", 16), fg="blue")
        self.loading_label.pack(pady=20)

        self.set_loading_message("Initializing...")
        root.after(800, self.load_data)

    def load_data(self):
        def task():
            self.set_loading_message("Loading Pokémon data...")
            self.data = fetch_pokemon_data()
            root.after(300)
            self.set_loading_message("Loading sprites...")
            self.sprite_check = cache_sprites()
            root.after(300)
            self.set_loading_message("Loading egg group cache...")
            self.egg_group_cache = load_egg_group_cache()
            root.after(300)
            self.set_loading_message("Loading complete!")
            root.after(300)

            self.loading_label.destroy()  # Remove loading label
            

            self.data = fetch_pokemon_data()
            self.sprite_check = cache_sprites()
            self.egg_group_cache = load_egg_group_cache()
            self.all_pokemon = self.data
            self.current_pokemon = None
            self.questions = []
            self.current_question_index = 0
            self.score = 0
            self.total_questions = 0
            self.answered_questions = set()
            self.leniency = 0.15  # Numerical leniency in percentage
            # String similarity threshold in percentage
            self.string_similarity_threshold = 0.7
            self.ui.update_score(self.score, self.total_questions)

        threading.Thread(target=task).start()

    def set_loading_message(self, message: str):
        self.loading_label.config(text="")
        self.loading_label.update_idletasks()
        self.loading_label.config(text=message)
        self.loading_label.update_idletasks()

    def start_quiz(self, pokemon_name: str):
        if not pokemon_name.strip():
            self.ui.show_feedback("Please enter a Pokemon name!", "red")
            return
        # Set current pokemon and generate questions
        pokemon_name = pokemon_name.lower().strip()
        print(f"Searching for Pokemon: {pokemon_name}")  # Debug log
        
        # Debug log to show available Pokemon
        self.current_pokemon = next(
            (p for p in self.data if p['name'].lower() == pokemon_name), None)
        if not self.current_pokemon:
            self.ui.show_feedback("Pokemon not found.", "orange")
            return
        
        print(f"Found Pokemon: {self.current_pokemon['name']}")  # Debug log


        self.questions = generate_questions(
            self.current_pokemon, self.egg_group_cache, self.all_pokemon)

        # Reset quiz state
        self.score = 0
        self.total_questions = 0
        self.current_question_index = 0
        self.answered_questions.clear()
        self.ui.sprite_label.config(image='')  # Clear sprite


        # Show the first question
        self.show_current_question()

    def prev_question(self):
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.show_current_question()

    def next_question(self):
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.show_current_question()

    def show_current_question(self):
        question = self.questions[self.current_question_index]
        self.ui.show_question(
            question,
            on_submit=self.submit_answer,
            answered=self.current_question_index in self.answered_questions
        )
        self.ui.update_navigation_buttons(
            can_go_prev=self.current_question_index > 0,
            can_go_next=self.current_question_index < len(self.questions) - 1
        )

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
            self.score += 1
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = ", ".join(correct_answer)
            self.ui.show_feedback(
                f"Partially Correct! The correct answer is: {correct_answer}", "orange")
            winsound.PlaySound(self.ui.partial_correct_sound, winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = "\n".join(correct_answer)
            self.ui.show_feedback(
                f"Incorrect! The correct answer is: \n{correct_answer}", "red")
            winsound.PlaySound(self.ui.incorrect_sound, winsound.SND_ALIAS | winsound.SND_ASYNC)


        # Save the user's answer for display
        question["user_answer"] = user_answer

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