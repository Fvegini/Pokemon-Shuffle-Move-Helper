from PIL import ImageTk, Image
import tkinter as tk
import os
from src import constants, custom_utils
from pathlib import Path

exception_list = ["Empty", "Coin", "Metal", "Wood"]
custom_order = set(["SP_084", "NORMAL", "FIRE", "WATER", "GRASS", "ELECTRIC", "ICE", "FIGHTING", "POISON", "GROUND", "FLYING", "PSYCHIC", "BUG", "ROCK", "GHOST", "DRAGON", "DARK", "STEEL", "FAIRY", "NONE"])

class TeamData():
    
    def __init__(self, stage, icons, moves) -> None:
        self.stage = stage
        self.icons = icons
        self.moves = moves
        

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
            icons = parts[2]
            for item in exception_list:
                icons = icons.replace(item, f"_{item}")
            icons = icons.split(",")
            moves = parts[3].split(",")
            #Append mega:
            try:
                mega_name = f"Mega_{parts[4]}"
                mega_move = moves[icons.index(parts[4])]
                icons.append(mega_name)
                moves.append(mega_move)
            except:
                pass
            self.teams.append(TeamData(team_name, icons, moves))
            
        self.teams = sorted(self.teams, key=custom_sort)

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
        screen_height = self.winfo_screenheight() - custom_utils.get_taskbar_size()

        width = int(screen_width / 2)
        height = int(screen_height / 2)

        # Calculate window position at the bottom-right corner
        x = screen_width - width
        y = screen_height - height

        app_width = self.winfo_width()
        app_height = self.winfo_height()

        # Set window geometry
        self.geometry(f"{app_width}x{height}+{x}+{y}")
        # self.update()
        # if self.winfo_width() != width:
        #     scale_factor = self.winfo_width() / width
        #     self.geometry(f"{int(width*scale_factor)}x{int(height*scale_factor)}+{x}+{y}")


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
            self.image_preview.image = photo

    def on_double_click(self, event):
        self.root.destroy_selected_pokemons()
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_team: TeamData = self.teams[selected_index[0]]
            print("Selected Team:", selected_team.icons)
            for pokemon, shortcut in zip(selected_team.icons, selected_team.moves):
                self.root.insert_image_widget(f"{pokemon}.png", shortcut)
        self.destroy()
    
def custom_sort(item: TeamData):
    global custom_order
    if item.stage in custom_order:
        return (0, item.stage)  # Assign a lower value (0) to items in the subset
    else:
        return (1, item.stage)  # Assign a higher value (1) to other items


# if __name__ == "__main__":
#     root = tk.Tk()    
#     app = TeamLoader(root)
#     root.mainloop()