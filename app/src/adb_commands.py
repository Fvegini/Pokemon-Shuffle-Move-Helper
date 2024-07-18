from src import constants, custom_utils, screen_utils, log_utils
from src.execution_variables import current_run
import re
import subprocess

log = log_utils.get_logger()


def update_adb_connection(reconfigure_screen):
    pipe = adb_run_screen_size()
    output = str(pipe.stdout.read()) #type: ignore
    if output.startswith("b'Physical size"):
        log.info(output)
    else:
        pipe = subprocess.Popen("adb kill-server",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output = str(pipe.stdout.read()) #type: ignore
        pipe = subprocess.Popen("adb connect localhost:5555",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output = str(pipe.stdout.read()) #type: ignore
        current_run.adb_shell_command = "adb -s localhost:5555 shell"
        pipe = adb_run_screen_size()
        output = str(pipe.stdout.read()) #type: ignore
        log.info(output)
    if reconfigure_screen:
        configure_screen()


def adb_run_swipe(from_x, from_y, to_x, to_y, delay, skip_on_error=False, skip_extra_debug=False):
    try:
        log.debug(f"Swiping at: {from_x} {from_y} {to_x} {to_y} {delay}")
        subprocess.Popen(f"{current_run.adb_shell_command} input swipe {from_x} {from_y} {to_x} {to_y} {delay}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        if not skip_extra_debug and custom_utils.is_extra_debug_active():
            custom_utils.save_extra_debug_image([[from_x, from_y], [to_x, to_y]], "swipe")
    except:
        if skip_on_error:
            return
        update_adb_connection(reconfigure_screen=True)
        adb_run_swipe(from_x, from_y, to_x, to_y, delay, skip_on_error=True, skip_extra_debug=skip_extra_debug)


def adb_run_tap(x ,y, skip_on_error=False, skip_extra_debug=False):
    try:
        log.debug(f"Tapping at: {x}, {y}")
        subprocess.Popen(f"{current_run.adb_shell_command} input tap {x} {y}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        if not skip_extra_debug and custom_utils.is_extra_debug_active():
            custom_utils.save_extra_debug_image([[x, y]], "tap")
    except:
        if skip_on_error:
            return
        update_adb_connection(reconfigure_screen=True)
        adb_run_tap(x ,y, skip_on_error=True, skip_extra_debug=skip_extra_debug)


def adb_run_screenshot(skip_on_error=False):
    try:
        return subprocess.Popen(f"{current_run.adb_shell_command} screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except:
        if skip_on_error:
            return
        update_adb_connection(reconfigure_screen=True)
        adb_run_screenshot(skip_on_error=True)


def adb_run_screen_size(skip_on_error=False):
    try:
        return subprocess.Popen(f"{current_run.adb_shell_command} wm size",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except:
        if skip_on_error:
            log.debug("Couldn't find ADB active connection")
        update_adb_connection(reconfigure_screen=True)
        adb_run_screen_size(skip_on_error=True)


def configure_screen():
    try:
        pipe = subprocess.Popen(f"{current_run.adb_shell_command} wm size",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        response = str(pipe.stdout.read()).strip() #type: ignore
        resolution = re.findall(r"\b\d{2,4}\s*x\s*\d{2,4}\b", response)[0]
        screen_utils.update_screen(constants.RESOLUTIONS[resolution])
    except Exception as ex:
        log.error(f"Couldn't load screen resolution: {ex}")
        pass

update_adb_connection(reconfigure_screen=True)