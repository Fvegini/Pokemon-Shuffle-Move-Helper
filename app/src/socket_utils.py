import socket
from pathlib import Path

socket_port = None


def load_socker_port():
    global socket_port
    with open( Path.joinpath(Path.home(), "Shuffle-Move", "config", "preferences.txt"), "r") as file:
        lines = file.readlines()
    
    for line in lines:
        if "SOCKET_PORT" in line:
            socket_port = int(line.split()[-1])
            return
    return 54321
    

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
            return result
    except:
        return ""

def ping_shuffle_move():
    # Connect to the Java application
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect(('localhost', socket_port))  # Use the same port as in the Java application
        s.sendall(b'ping\n')

        result = s.recv(1024).decode('utf-8')
        print(result)