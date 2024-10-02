from PIL import ImageTk, Image
import tkinter as tk
import os
from src import constants, custom_utils
from pathlib import Path
from src.execution_variables import current_run
exception_list = ["Empty", "Coin", "Metal", "Wood", "Fog"]
stages_fixed_list = ['BUG', 'DARK', 'DRAGON', 'ELECTRIC', 'FAIRY', 'FIGHTING', 'FIRE', 'FLYING', 'GHOST', 'GRASS', 'GROUND', 'ICE', 'MEOWTH COIN MANIA', 'NONE', 'NORMAL', 'POISON', 'PSYCHIC', 'ROCK', 'STEEL', 'WATER', 'SP_084', 'MEOWTH COIN MANIA', constants.SURVIVAL_MODE_STAGE_NAME, '037']
stages_set = set(stages_fixed_list)

class TeamData():
    
    def __init__(self, stage, icons, stage_added=[]) -> None:
        self.stage = stage
        self.icons = icons
        self.stage_added = stage_added
        

class TeamLoader(tk.Toplevel):
     
    def __init__(self, master = None, root = None, folder = ""):
         
        super().__init__(master = master)
        self.title(f"Select a Team")
        self.root = root
        # self.geometry('500x500')        
        # self.create_widgets()



        # Read the file and parse each line into a tuple
        with open( Path.joinpath(Path.home(), "Shuffle-Move", "config", "teamsData.txt"), "r") as file:
            lines = file.readlines()

        self.teams: list[TeamData] = []
        tmp_teams: list[TeamData] = []
        for line in lines:
            parts = line.strip().split()
            if not parts[0] == "TEAM":
                continue
            team_name = parts[1]
            if team_name not in stages_fixed_list:
                continue
            icons_str = parts[2]
            stage_added = []
            if len(parts) >= 6:
                stage_added_str = parts[5]
                stage_added = stage_added_str.split(",")
            for item in exception_list:
                icons_str = icons_str.replace(item, f"_{item}")
            icons = icons_str.split(",")
            #Append mega:
            try:
                mega_name = f"{constants.MEGA_PREFIX}{parts[4]}"
                icons.append(mega_name)
            except:
                pass
            # self.teams.append(TeamData(team_name, icons, stage_added))
            tmp_teams.append(TeamData(team_name, icons, stage_added))
            if team_name == "SP_084":
                # self.teams.append(TeamData("MEOWTH COIN MANIA", icons))
                tmp_teams.append(TeamData("MEOWTH COIN MANIA", icons))
            
        tmp_teams.sort(key=lambda x: stages_fixed_list.index(x.stage))
        for stage_name in stages_fixed_list:
            if not any([team for team in tmp_teams if stage_name == team.stage]):
                tmp_teams.append(TeamData(stage_name, ["_Wood","_Metal"], []))
        self.teams.extend(tmp_teams)
        # self.teams = sorted(self.teams, key=custom_sort)

        # Create the main Tkinter window
        # root.title("Team List")

        # Create a Tkinter list with the second element of each tuple
        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE)
        for team in self.teams:
            self.listbox.insert(tk.END, team.stage)

        scrollbar = tk.Scrollbar(self, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.grid(row=1, column=2, sticky='ns', padx=(0, 10), pady=(10,10))

        self.listbox.config(yscrollcommand=scrollbar.set)

        self.image_preview = tk.Label(self)
        self.image_preview.grid(row=1, column=3, padx=5, pady=5)

        self.listbox.bind("<Double-Button-1>", self.on_double_click)
        self.listbox.grid(row=1, column=1, sticky='ns')
        self.rowconfigure(1, weight=1)
        
        
        self.configure_initial_geometry()


    def configure_initial_geometry(self):
        self.update()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight() - ( 2 * custom_utils.get_taskbar_size())

        x = int(screen_width / 2)
        y = 0

        app_width = self.winfo_width()
        
        # Set window geometry
        self.geometry(f"{app_width}x{screen_height}+{x}+{y}")

    def on_double_click(self, event):
        self.withdraw()
        self.root.destroy_selected_pokemons()
        selected_index = self.listbox.curselection()
        if selected_index:
            current_run.current_stage = self.teams[selected_index[0]].stage
            if current_run.current_stage == constants.SURVIVAL_MODE_STAGE_NAME:
                new_pokemon_list = custom_utils.load_file_as_list(constants.SURVIVAL_MODE_TXT)
                self.teams[selected_index[0]].stage_added.extend(new_pokemon_list)
                self.teams[selected_index[0]].icons.extend(new_pokemon_list)
            if current_run.current_stage == "MEOWTH COIN MANIA":
                current_run.current_stage = "SP_084"
            if current_run.current_stage == "SP_084":
                current_run.current_strategy = constants.move_strategy.get(constants.GRADING_WEEKEND_MEOWTH, "")
            else:
                current_run.current_strategy = constants.move_strategy.get(constants.GRADING_TOTAL_SCORE, "")
            current_run.has_modifications = True
            selected_team: TeamData = self.teams[selected_index[0]]
            #First Append all Stage Added Pokemons
            for pokemon in selected_team.stage_added:
                self.root.insert_image_widget(f"{pokemon}.png", stage_added=True)
            #Then Append the others
            for pokemon in selected_team.icons:
                is_stage_added = pokemon in selected_team.stage_added
                if not is_stage_added:
                    self.root.insert_image_widget(f"{pokemon}.png", stage_added=False)
            self.update_idletasks()

        self.root.stage_combobox.set(current_run.current_stage)
        self.root.strategy_combobox.set(current_run.current_strategy)
        self.destroy()