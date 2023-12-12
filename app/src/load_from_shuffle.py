from PIL import ImageTk, Image
import tkinter as tk
import os
from src import constants, custom_utils

exception_list = ["Empty", "Coin", "Metal", "Wood"]
custom_order = set(["NORMAL", "FIRE", "WATER", "GRASS", "ELECTRIC", "ICE", "FIGHTING", "POISON", "GROUND", "FLYING", "PSYCHIC", "BUG", "ROCK", "GHOST", "DRAGON", "DARK", "STEEL", "FAIRY", "NONE"])
class TeamLoader(tk.Toplevel):
     
    def __init__(self, master = None, root = None, folder = ""):
         
        super().__init__(master = master)
        self.title(f"Select a Team")
        self.root = root
        # self.create_widgets()



        # Read the file and parse each line into a tuple
        with open(r"C:\Users\jgsfe\Shuffle-Move\config\teamsData.txt", "r") as file:
            lines = file.readlines()

        self.teams = []
        for line in lines:
            parts = line.strip().split()
            if not parts[0] == "TEAM":
                continue
            team_name = parts[1]
            pokemons = parts[2]
            for item in exception_list:
                pokemons = pokemons.replace(item, f"_{item}")
            moves = parts[3]
            self.teams.append((team_name, (pokemons, moves)))
            
        self.teams = sorted(self.teams, key=custom_sort)

        # Create the main Tkinter window
        # root.title("Team List")

        # Create a Tkinter list with the second element of each tuple
        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE)
        for team in self.teams:
            self.listbox.insert(tk.END, team[0])


        self.images_frame = tk.Frame(self, background="lightblue")
        self.images_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        self.image_preview = tk.Label(self.images_frame)
        self.image_preview.grid(row=2, column=1, padx=5, pady=5)


        # Bind double-click event to print the third element of the selected tuple
        self.listbox.bind("<<ListboxSelect>>", self.preview_team)
        self.listbox.bind("<Double-Button-1>", self.on_double_click)

        # Pack the listbox into the window
        self.listbox.pack(expand=True, fill=tk.BOTH)


    def preview_team(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_team = self.teams[selected_index[0]][1][0]
            img_list = []
            for pokemon_name in selected_team.split(","):
                image_path = os.path.join(constants.IMAGES_PATH, f"{pokemon_name}.png")
                image = custom_utils.open_and_resize_np_image(image_path, (50,50))
                img_list.append(image)
            
            new_img = custom_utils.concatenate_list_images(img_list, blank_space=5)
            photo = ImageTk.PhotoImage(Image.fromarray(new_img))

            self.image_preview.config(image=photo)
            self.image_preview.image = photo

    def on_double_click(self, event):
        self.root.destroy_selected_pokemons()
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_tuple = self.teams[selected_index[0]][1]
            print("Selected Team:", selected_tuple[1])
            pokemons = selected_tuple[0].split(",")
            shortcuts = selected_tuple[1].split(",")
            for pokemon, shortcut in zip(pokemons, shortcuts):
                self.root.insert_image_widget(f"{pokemon}.png", shortcut)
        self.destroy()
        

def custom_sort(item):
    global custom_order
    if item[0] in custom_order:
        return (0, item[0])  # Assign a lower value (0) to items in the subset
    else:
        return (1, item[0])  # Assign a higher value (1) to other items


# if __name__ == "__main__":
#     root = tk.Tk()    
#     app = TeamLoader(root)
#     root.mainloop()