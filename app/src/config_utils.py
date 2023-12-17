import configparser
import ast
def create_default_config():
    config = configparser.ConfigParser()
    config['SETTINGS'] = {
    "shuffle_move_first_square_position": "(1500, 90)",
    "mouse_after_shuffle_position": "(1420, 560)",
    "board_top_left": "(11, 466)",
    "board_bottom_right": "(573, 1027)"
    }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    config_converted = {}
    for key in config.options('SETTINGS'):
        config_converted[key] = ast.literal_eval(config['SETTINGS'].get(key))
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