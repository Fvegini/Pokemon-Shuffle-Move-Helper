import pygetwindow as gw

def get_focused_window_name():
    try:
        name = gw.getActiveWindowTitle()
        if not name:
            return ""
        return name
    except:
        return ""

def get_window_name_at_coordinate(x, y):
    try:
        name = gw.getWindowsAt(x, y)[0].title
        if not name:
            return ""
        return name
    except:
        return ""