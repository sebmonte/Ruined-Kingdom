import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field
import random
import generators_npc
from models import GameState, Encounter, Choice, Kingdom
from generators_encounters import generate_biome, generate_encounter, next_area
from generators_kingdom import enter_kingdom
from generators_villagers import generate_villager
import re


class GameUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Procedural Text Adventure")
        self.root.geometry("1200x800")
        self.root.minsize(700, 450)

        self.state = GameState()

        # Initialize kingdom with 10 villagers at game start if population is empty
        if not self.state.kingdom.population:
            self.state.kingdom.population = [generate_villager("human") for _ in range(10)]

        # Temporary example inventory if your GameState does not have one yet
        if not hasattr(self.state, "inventory"):
            self.state.inventory = ["Torch", "Old Key", "Health Potion"]

        self.build_layout()
        self.bind_keys()
        self.start_game()

    def build_layout(self) -> None:
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # ----------------------------
        # Top bar
        # ----------------------------
        self.top_frame = ttk.Frame(self.root, padding=10)
        self.top_frame.grid(row=0, column=0, sticky="ew")
        self.top_frame.columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        self.kingdom_var = tk.StringVar()
        self.food_var = tk.StringVar()
        self.army_var = tk.StringVar()
        self.happiness_var = tk.StringVar()
        self.fear_var = tk.StringVar()
        self.population_var = tk.StringVar()
        self.area_var = tk.StringVar()

        ttk.Label(self.top_frame, textvariable=self.kingdom_var).grid(row=0, column=0, sticky="w")
        ttk.Label(self.top_frame, textvariable=self.food_var).grid(row=0, column=1, sticky="w")
        ttk.Label(self.top_frame, textvariable=self.army_var).grid(row=0, column=2, sticky="w")
        ttk.Label(self.top_frame, textvariable=self.happiness_var).grid(row=0, column=3, sticky="w")
        ttk.Label(self.top_frame, textvariable=self.fear_var).grid(row=0, column=4, sticky="w")
        ttk.Label(self.top_frame, textvariable=self.population_var).grid(row=0, column=5, sticky="w")
        ttk.Label(self.top_frame, textvariable=self.area_var).grid(row=0, column=6, sticky="w")

        # ----------------------------
        # Notebook with tabs
        # ----------------------------
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.encounter_tab = ttk.Frame(self.notebook)
        self.inventory_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.encounter_tab, text="Encounter")
        self.notebook.add(self.inventory_tab, text="Inventory")

        # Let encounter tab stretch
        self.encounter_tab.rowconfigure(0, weight=1)
        self.encounter_tab.columnconfigure(0, weight=1)

        # ----------------------------
        # Encounter tab contents
        # ----------------------------
        self.encounter_container = ttk.Frame(self.encounter_tab)
        self.encounter_container.grid(row=0, column=0, sticky="nsew")
        self.encounter_container.rowconfigure(0, weight=1)
        self.encounter_container.columnconfigure(0, weight=1)

        # Middle text section
        self.text_frame = ttk.Frame(self.encounter_container, padding=(0, 0, 0, 10))
        self.text_frame.grid(row=0, column=0, sticky="nsew")
        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)

        self.text_box = tk.Text(
            self.text_frame,
            wrap="word",
            state="disabled",
            font=("Consolas", 15),
            padx=10,
            pady=10
        )
        self.text_box.tag_config("title", font=("Consolas", 20, "bold"))
        self.text_box.tag_config("Bananas", foreground="gold")
        self.text_box.tag_config("Animal Husbandry", foreground="green")
        self.text_box.tag_config("Magic", foreground="purple")
        self.text_box.tag_config("Army", foreground="red")
        self.text_box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.text_frame, command=self.text_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_box.configure(yscrollcommand=scrollbar.set)

        # Bottom choices
        self.bottom_frame = ttk.Frame(self.encounter_container, padding=20)
        self.bottom_frame.grid(row=1, column=0, sticky="ew")
        self.bottom_frame.columnconfigure(0, weight=1)

        self.choice_var = tk.StringVar()
        self.choice_label = ttk.Label(
            self.bottom_frame,
            textvariable=self.choice_var,
            justify="left",
            font=("Arial", 13),
        )
        self.choice_label.grid(row=0, column=0, sticky="w")

        self.hint_label = ttk.Label(
            self.bottom_frame,
            text="Press number keys to choose.",
            font=("Arial", 12, "italic"),
        )
        self.hint_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

        # ----------------------------
        # Inventory tab contents
        # ----------------------------
        self.inventory_tab.rowconfigure(1, weight=1)
        self.inventory_tab.columnconfigure(0, weight=1)

        self.inventory_title = ttk.Label(
            self.inventory_tab,
            text="Inventory",
            font=("Arial", 16, "bold"),
        )
        self.inventory_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.inventory_list = tk.Listbox(
            self.inventory_tab,
            font=("Arial", 13),
            height=15,
        )
        self.inventory_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def bind_keys(self) -> None:
        for key in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            self.root.bind(key, self.handle_choice)

    def start_game(self) -> None:
        self.state.add_log("Your reign begins.")
        enter_kingdom(self.state)
        self.refresh_ui()
        '''
        self.state.current_biome = generate_biome(self.state.area_index)
        self.state.current_encounter = generate_encounter(self.state)
        self.state.add_log("Your journey begins.")
        self.refresh_ui()
        '''
    def handle_choice(self, event: tk.Event) -> None:
        if self.notebook.select() != str(self.encounter_tab): #Stop player from sending input if not in encounter
            return

        encounter = self.state.current_encounter
        if encounter is None:
            return

        pressed = event.keysym
        for choice in encounter.choices:
            if choice.key == pressed:
                choice.effect()
                self.check_game_over()
                self.refresh_ui()
                return

    def check_game_over(self) -> None:
        pass

    def refresh_inventory(self) -> None:
        self.inventory_list.delete(0, tk.END)

        for item in self.state.inventory:
            self.inventory_list.insert(tk.END, item)

        if len(self.state.inventory) == 0:
            self.inventory_list.insert(tk.END, "(empty)")



    def insert_with_highlighted_tags(self, text: str):
        pos = 0
        for match in re.finditer(r"\[([^\]]+)\]", text):
            # insert text before the tag
            self.text_box.insert(tk.END, text[pos:match.start()])

            tag_text = match.group(1)  # text inside brackets
            self.text_box.insert(tk.END, tag_text, tag_text)

            pos = match.end()

        # insert remaining text
        self.text_box.insert(tk.END, text[pos:])

    def refresh_ui(self) -> None:
        k = self.state.kingdom
        #advisor_name = k.advisor.name if k.advisor else "None"
        army_total = sum(k.army_units.values())
        self.kingdom_var.set(f"Kingdom: {k.name}")
        self.food_var.set(f"Food: {k.total_food}")
        self.army_var.set(f"Army: {army_total}")
        self.happiness_var.set(f"Happiness: {k.happiness}")
        self.fear_var.set(f"Fear: {k.fear}")
        self.population_var.set(f"Pop: {len(k.population)}")
        self.area_var.set(f"Area: {self.state.area_index} ({self.state.current_biome})")

        self.text_box.config(state="normal")
        self.text_box.delete("1.0", tk.END)

        encounter = self.state.current_encounter
        if encounter:
            header = f"{encounter.title}\n{'=' * len(encounter.title)}\n\n"
            self.text_box.insert(tk.END, header, "title")
            self.insert_with_highlighted_tags(encounter.description.strip() + "\n\n")

        self.text_box.insert(tk.END, "Recent events:\n")
        self.text_box.insert(tk.END, "-" * 40 + "\n")
        for entry in self.state.log[-8:]:
            self.text_box.insert(tk.END, f"- {entry}\n")

        self.text_box.config(state="disabled")
        self.text_box.see(tk.END)

        if encounter and encounter.choices:
            choice_lines = [f"{c.key}. {c.text}" for c in encounter.choices]
            self.choice_var.set("\n".join(choice_lines))
        else:
            self.choice_var.set("No choices available.")

        self.refresh_inventory()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    app = GameUI(root)
    root.mainloop()