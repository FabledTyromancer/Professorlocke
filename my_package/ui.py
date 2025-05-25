import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict
from PIL import Image, ImageTk, ImageOps
import winsound
import os


DEFAULT_FONT = ('Arial', 16)
FEEDBACK_FONT = ('Arial', 14)

cache_dir = "professor_cache"
  


class QuizUI:
    def __init__(self, root: tk.Tk, on_start_quiz: Callable[[str], None], on_prev_question: Callable, on_next_question: Callable, clear_cache: Callable, on_unit_toggle: Callable[[bool], None]):
        """Initialize the UI."""
        self.root = root
        self.on_start_quiz = on_start_quiz
        self.on_prev_question = on_prev_question
        self.on_next_question = on_next_question
        self.clear_cache = clear_cache
        self.on_unit_toggle = on_unit_toggle

        self.root.title("ProfessorLocke")
        self.root.minsize(600, 550)  # Set minimum size for stable window/placement, can comment out for it to adjust automatically.
        self.root.option_add('*Font', DEFAULT_FONT)
        self.root.option_add('*Font', FEEDBACK_FONT)

        # Initialize UI elements
        self.score_label = None
        self.sprite_label = None
        self.question_frame = None
        self.feedback_frame = None
        self.prev_button = None
        self.next_button = None
        self.pokemon_entry = None
        self.unit_var = None  # For unit toggle

        # Themes for answers
        self.correct_sound = os.path.join(cache_dir, "correct.wav")
        self.incorrect_sound = os.path.join(cache_dir,"incorrect.wav")
        self.partial_correct_sound = os.path.join(cache_dir, "partial_correct.wav")
        # Themes for final grade
        self.victory_theme = os.path.join(cache_dir,"victory.wav")
        self.failure_theme = os.path.join(cache_dir,"failure.wav")

        self.setup_ui()

    def setup_ui(self):
        """Set up the main UI layout."""
        # Pokemon search frame
        search_frame = ttk.Frame(self.root)
        search_frame.pack(pady=5, padx=10, fill="x")

        ttk.Label(search_frame, text="Pokemon:",
                  font=DEFAULT_FONT).pack(side="left", padx=5)
        self.pokemon_entry = ttk.Entry(
            search_frame, width=15, font=DEFAULT_FONT)
        self.pokemon_entry.pack(side="left", padx=5)
        self.pokemon_entry.bind('<Return>', lambda e: self.on_start_quiz(
            self.pokemon_entry.get().strip()))
        ttk.Button(search_frame, text="Start Quiz", command=lambda: self.on_start_quiz(
            self.pokemon_entry.get().strip()), style='Large.TButton').pack(side="left", padx=5)

        # Unit toggle frame
        unit_frame = ttk.Frame(self.root)
        unit_frame.pack(pady=5, padx=10, fill="x")
        
        self.unit_var = tk.BooleanVar(value=True)  # True for metric, False for imperial
        self.unit_button = ttk.Button(
            unit_frame, 
            text="m/kg", 
            command=self.toggle_units,
            style='Large.TButton'
        )
        self.unit_button.pack(side="left", padx=5)

        self.clear_cache_button = ttk.Button(
            unit_frame, text="Reset Cache", command=self.clear_cache, state="disabled", style='warning.Outline.TButton')
        self.clear_cache_button.pack(side="right", padx=5)

        # Question frame
        self.question_frame = ttk.Frame(self.root)
        self.question_frame.pack(pady=5, padx=10, fill="both", expand=True)

        # Feedback frame
        self.feedback_frame = ttk.Frame(self.root)
        self.feedback_frame.pack(pady=5, padx=10, fill="x")

        # Navigation frame
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(pady=5, padx=10, fill="x")

        self.prev_button = ttk.Button(
            nav_frame, text="Previous", command=self.on_prev_question, state="disabled", style='Large.TButton')
        self.prev_button.pack(side="left", padx=5)

        self.next_button = ttk.Button(
            nav_frame, text="Next", command=self.on_next_question, state="disabled", style='Large.TButton')
        self.next_button.pack(side="right", padx=5)

        # Score label
        self.score_label = ttk.Label(
            self.root, text="Score: 0/0", font=DEFAULT_FONT)
        self.score_label.pack(pady=5)

        # Sprite label
        self.sprite_label = ttk.Label(self.root)
        self.sprite_label.pack(pady=5)

        # Configure styles for buttons
        style = ttk.Style()
        style.configure('Large.TButton', font=DEFAULT_FONT)
        style.configure('Large.TRadiobutton', font=DEFAULT_FONT)
        style.configure('Large.TCheckbutton', font=DEFAULT_FONT)
        style.configure('warning.Outline.TButton', font=FEEDBACK_FONT, foreground='red', borderwidth=2)

    def update_score(self, score: int, total_questions: int):
        """Update the score label."""
        self.score_label.config(text=f"Score: {score}/{total_questions}")

    def update_navigation_buttons(self, can_go_prev: bool, can_go_next: bool):
        """Enable or disable navigation buttons."""
        self.prev_button.config(state="normal" if can_go_prev else "disabled")
        self.next_button.config(state="normal" if can_go_next else "disabled")
    
    def update_cache_button(self, cache_issue: bool):
        self.clear_cache_button.config(state="normal" if cache_issue else "disabled")

    def clear_question_frame(self):
        """Clear all widgets from the question frame."""
        for widget in self.question_frame.winfo_children():
            widget.destroy()

    def show_question(self, question: Dict, on_submit: Callable[[str], None], answered: bool):
        """Display the current question."""
        self.clear_question_frame()

        # Question label
        ttk.Label(self.question_frame, text=question["question"], wraplength=500, font=DEFAULT_FONT).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=5)

        # Input frame
        input_frame = ttk.Frame(self.question_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)
        input_frame.grid_columnconfigure(0, weight=1)

        var = None
        if question["type"] == "boolean":
            var = tk.BooleanVar()
            radio_frame = ttk.Frame(self.question_frame)
            radio_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
            ttk.Radiobutton(radio_frame, text="True", variable=var, value=True,
                            style='Large.TRadiobutton').pack(side="left", padx=5)
            ttk.Radiobutton(radio_frame, text="False", variable=var, value=False,
                            style='Large.TRadiobutton').pack(side="left", padx=5)
            radio_frame.winfo_children()[0].focus_set()
        else:
            var = tk.StringVar()
            entry = ttk.Entry(input_frame, textvariable=var,
                              width=25, font=DEFAULT_FONT)
            entry.grid(row=0, column=0, sticky="w", padx=(0, 5))
            entry.focus_set()
        


            # Pre-fill the user's previous answer if it exists
            if "user_answer" in question:
                var.set(question["user_answer"])

        result_label = ttk.Label(
            self.question_frame, text="", font=DEFAULT_FONT, wraplength=600)
        result_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5)

        def submit_answer():
            user_answer = var.get(
            ) if question["type"] == "boolean" else var.get().strip()
            on_submit(user_answer)

        submit_button = ttk.Button(
            input_frame, text="Submit", command=submit_answer, width=8, style='Large.TButton')
        submit_button.grid(row=0, column=1, sticky="e", padx=5)

        # Disable input if already answered
        if answered:
            submit_button.config(state="disabled")
            if question["type"] == "boolean":
                for radio in radio_frame.winfo_children():
                    radio.config(state="disabled")
            else:
                entry.config(state="disabled")
        if not answered and question["type"] != "boolean":
            entry.bind('<Return>', lambda e: submit_answer())
    def show_sprite(self, sprite_path: str, grayscale: bool = False):
        """Fetch and display the Pokémon sprite."""
        try:
            if os.path.isfile(sprite_path):
                image = Image.open(sprite_path)
                if grayscale:
                    # Convert to RGBA if not already
                    if image.mode != 'RGBA':
                        image = image.convert('RGBA')
                    
                    # Split the image into channels
                    r, g, b, a = image.split()
                    
                    # Convert RGB to grayscale while preserving alpha
                    gray = ImageOps.grayscale(image)
                    
                    # Create new image with grayscale RGB and original alpha
                    image = Image.merge('RGBA', (gray, gray, gray, a))
                
                image = image.resize((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.sprite_label.config(image=photo)
                self.sprite_label.image = photo  # Keep a reference
                
                # Update window size to accommodate sprite
                self.root.update_idletasks()
            else:
                print(f"Sprite not found: {sprite_path}")
        except Exception as e:
            print(f"Error loading sprite: {e}")

    def show_final_grade(self, score: int, total_questions: int, sprite_url: str):
        """Display the final grade and Pokémon sprite."""
        percentage = round((score / total_questions) *
                           100) if total_questions > 0 else 0

        # Play victory or failure theme based on score
        if percentage >= 75:
            try:
                winsound.PlaySound(self.victory_theme,
                                   winsound.SND_ALIAS | winsound.SND_ASYNC)
            except:
                pass
        else:
            try:
                winsound.PlaySound(self.failure_theme,
                                   winsound.SND_ALIAS | winsound.SND_ASYNC)
            except:
                pass

        # Fetch and display sprite
        self.show_sprite(sprite_url, grayscale=(percentage < 75))

    def show_feedback(self, message: str, color: str):
        """Display feedback for the user's answer."""

        for widget in self.feedback_frame.winfo_children():
            widget.destroy()

        feedback_label = ttk.Label(
            self.feedback_frame, text=message, font=FEEDBACK_FONT, foreground=color)
        feedback_label.pack(pady=5)

        # Automatically remove feedback after x seconds(In milliseconds)
        self.root.after(5000, feedback_label.destroy)

    def toggle_units(self):
        """Toggle between metric and imperial units."""
        self.unit_var.set(not self.unit_var.get())
        self.unit_button.config(text="m/kg" if self.unit_var.get() else "ft-in/lbs")
        self.on_unit_toggle(self.unit_var.get())
