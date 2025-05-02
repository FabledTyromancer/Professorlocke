import tkinter as tk
from my_package.ui import QuizUI
from my_package.quiz_logic import check_answer, generate_questions
from my_package.data_fetching import fetch_pokemon_data, load_egg_group_cache
from my_package.utils import meters_to_feet_inches, kg_to_lbs


class ProfessorLocke:
    def __init__(self, root):
        self.ui = QuizUI(
            root,
            on_start_quiz=self.start_quiz,
            on_prev_question=self.prev_question,
            on_next_question=self.next_question
        )
        self.current_pokemon = None
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.total_questions = 0
        self.answered_questions = set()
        self.egg_group_cache = load_egg_group_cache()
        self.leniency = 0.15  # Numerical leniency in percentage
        # String similarity threshold in percentage
        self.string_similarity_threshold = 0.7
        self.ui.update_score(self.score, self.total_questions)

    def start_quiz(self, pokemon_name: str):
        # Fetch Pokémon data
        self.current_pokemon, species_data = fetch_pokemon_data(pokemon_name)
        if not self.current_pokemon or not species_data:
            return

        # Generate questions
        self.questions = generate_questions(
            self.current_pokemon, species_data, self.egg_group_cache)

        # Reset quiz state
        self.score = 0
        self.total_questions = 0
        self.current_question_index = 0
        self.answered_questions.clear()

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
        elif close_match:
            self.score += 1
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = ", ".join(correct_answer)
            self.ui.show_feedback(
                f"Partially Correct! The correct answer is: {correct_answer}", "orange")
        else:
            correct_answer = question["answer"]
            if isinstance(correct_answer, list):
                correct_answer = ", ".join(correct_answer)
            self.ui.show_feedback(
                f"Incorrect! The correct answer is: {correct_answer}", "red")

        # Save the user's answer for display
        question["user_answer"] = user_answer

        self.total_questions += 1
        self.answered_questions.add(self.current_question_index)
        self.ui.update_score(self.score, self.total_questions)

        # Show final grade if all questions are answered
        if len(self.answered_questions) == len(self.questions):
            sprite_url = self.current_pokemon['sprites']['front_default']
            self.ui.show_final_grade(
                self.score, self.total_questions, sprite_url)
        else:
            self.show_current_question()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessorLocke(root)
    root.mainloop()
