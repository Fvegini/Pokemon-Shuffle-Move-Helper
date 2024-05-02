import configparser
import ast
def create_default_config():
    config = configparser.ConfigParser()
    config['SETTINGS'] = {
    "board_top_left": "(210, 484)",
    "board_bottom_right": "(752, 1030)",
    "has_barrier": False, #type: ignore
    "adb_board": False, #type: ignore
    "adb_move": False, #type: ignore
    }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    config_converted = {}
    for key in config.options('SETTINGS'):
        try:
            config_converted[key] = ast.literal_eval(config['SETTINGS'].get(key))
        except:
            config_converted[key] = config['SETTINGS'].get(key)
    return config_converted

def update_config(variable, new_value):
    global config_values
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Update the specified variable
    config['SETTINGS'][variable] = str(new_value)

    # Save the updated configuration back to the file
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        
    config_values = read_config()

# Create a default configuration file if it doesn't exist
try:
    with open('config.ini', 'r'):
        pass
except FileNotFoundError:
    create_default_config()

# Read the configuration
config_values = read_config()