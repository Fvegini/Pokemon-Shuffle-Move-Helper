from packaging import version
import requests
import json
import customtkinter
from CTkMessagebox import CTkMessagebox

current_version = "1.2.6_adb"
latest_version = None

def verify_new_version():
    return
    # global latest_version
    # try:
    #     response = requests.get("https://api.github.com/repos/Fvegini/Pokemon-Shuffle-Move-Helper/releases/latest")
    #     latest_version = json.loads(response.text).get("name")
    #     if version.parse(current_version) < version.parse(latest_version):
    #         show_warning()
    # except:
    #     return


# def show_warning():
#     log.info("open")
#     msg = CTkMessagebox(title="Warning", message=f"New version found\nCurrent: {current_version}\nLatest: {latest_version}",
#                   icon="warning", option_1="Ok")