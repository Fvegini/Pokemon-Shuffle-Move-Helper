import socket
from pathlib import Path
from src import custom_utils

socket_port = None
PREFERENCES_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "preferences.txt")
custom_utils.verify_shuffle_file(PREFERENCES_PATH)

def load_socker_port():
    global socket_port
    try:
        with open(PREFERENCES_PATH, "r") as file:
            lines = file.readlines()
        
        for line in lines:
            if "SOCKET_PORT" in line:
                socket_port = int(line.split()[-1])
                return
    except:
        pass
    print(f"No SOCKET_PORT found in {PREFERENCES_PATH.as_posix()}")
    socket_port = 54321
    return
    

def loadNewBoard():
    global socket_port
    try:
        if not socket_port:
            load_socker_port()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(('localhost', socket_port))  # Use the same port as in the Java application
            s.sendall(b'loadNewBoard\n')
            result = s.recv(1024).decode('utf-8')
            if not result:
                print(f"Socket connected on port {socket_port} but without any response.")
            else:
                print(f"Shuffle Move Result: {result}")
            return result
    except:
        print(f"Cant connect to the socket on port {socket_port}, check if Shuffle Move is opened or if the port is being used by another program")
        return ""

def ping_shuffle_move():
    # Connect to the Java application
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect(('localhost', socket_port))  # Use the same port as in the Java application
        s.sendall(b'ping\n')

        result = s.recv(1024).decode('utf-8')
        print(result)