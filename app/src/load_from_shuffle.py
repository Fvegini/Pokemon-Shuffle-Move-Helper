from PIL import ImageTk, Image
import tkinter as tk
import os
from src import constants, custom_utils
from pathlib import Path
from src.execution_variables import execution_variables
exception_list = ["Empty", "Coin", "Metal", "Wood"]
stages_fixed_list = ['BUG', 'DARK', 'DRAGON', 'ELECTRIC', 'FAIRY', 'FIGHTING', 'FIRE', 'FLYING', 'GHOST', 'GRASS', 'GROUND', 'ICE', 'MEOWTH COIN MANIA', 'NONE', 'NORMAL', 'POISON', 'PSYCHIC', 'ROCK', 'STEEL', 'WATER', 'SP_084', 'MEOWTH COIN MANIA']
stages_set = set(stages_fixed_list)

class TeamData():
    
    def __init__(self, stage, icons) -> None:
        self.stage = stage
        self.icons = icons
        

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
        for line in lines:
            parts = line.strip().split()
            if not parts[0] == "TEAM":
                continue
            team_name = parts[1]
            if team_name not in stages_fixed_list:
                continue
            icons_str = parts[2]
            for item in exception_list:
                icons_str = icons_str.replace(item, f"_{item}")
            icons = icons_str.split(",")
            #Append mega:
            try:
                mega_name = f"Mega_{parts[4]}"
                icons.append(mega_name)
            except:
                pass
            self.teams.append(TeamData(team_name, icons))
            if team_name == "SP_084":
                self.teams.append(TeamData("MEOWTH COIN MANIA", icons))
            
        self.teams.sort(key=lambda x: stages_fixed_list.index(x.stage))

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


        # self.images_frame = customtkinter.CTkFrame(self)
        # self.images_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        self.image_preview = tk.Label(self)
        self.image_preview.grid(row=1, column=3, padx=5, pady=5)

        # Bind double-click event to print the third element of the selected tuple
        # self.listbox.bind("<<ListboxSelect>>", self.preview_team)
        self.listbox.bind("<Double-Button-1>", self.on_double_click)
        # Pack the listbox into the window
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


    def preview_team(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_team: TeamData = self.teams[selected_index[0]]
            img_list = []
            for icon_name in selected_team.icons:
                try:
                    image_path = os.path.join(constants.IMAGES_PATH, f"{icon_name}.png")
                    image = custom_utils.open_and_resize_np_image(image_path, (50,50))
                    img_list.append(image)
                except:
                    pass
            
            new_img = custom_utils.concatenate_list_images(img_list, blank_space=5)
            photo = ImageTk.PhotoImage(Image.fromarray(new_img))

            self.image_preview.config(image=photo)
            # self.image_preview.image = photo

    def on_double_click(self, event):
        self.root.destroy_selected_pokemons()
        selected_index = self.listbox.curselection()
        if selected_index:
            execution_variables.current_stage = self.teams[selected_index[0]].stage
            if execution_variables.current_stage == "MEOWTH COIN MANIA":
                execution_variables.current_stage = "SP_084"
            if execution_variables.current_stage == "SP_084":
                execution_variables.current_strategy = constants.move_strategy.get(constants.GRADING_WEEKEND_MEOWTH, "")
            else:
                execution_variables.current_strategy = constants.move_strategy.get(constants.GRADING_TOTAL_SCORE, "")
            execution_variables.has_modifications = True
            selected_team: TeamData = self.teams[selected_index[0]]
            print("Selected Team:", selected_team.icons)
            for pokemon in selected_team.icons:
                self.root.insert_image_widget(f"{pokemon}.png")
        
        self.root.stage_combobox.set(execution_variables.current_stage)
        self.root.strategy_combobox.set(execution_variables.current_strategy)
        
        self.destroy()