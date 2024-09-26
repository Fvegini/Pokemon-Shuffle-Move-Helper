from src import constants, custom_utils, screen_utils, log_utils
from src.execution_variables import current_run
import re
import adbutils
import time

log = log_utils.get_logger()

def update_adb_connection(reconfigure_screen):

    current_run.adb_device = None
    # Initialize the ADB client
    adb = adbutils.AdbClient(host="127.0.0.1", port=5037)

    # Kill the ADB server (optional, but sometimes helps)
    adb.server_kill()

    # List connected devices
    devices = adb.device_list()
    time.sleep(5)
    devices = adb.device_list()

    try:
        devices.append(adb.device())
    except Exception as ex:
        pass

    # Try to connect to each device and run a test command
    for device in devices:
        try:
            # Connect to the device
            adb.connect(device.serial)

            # Test command: run a simple command (e.g., checking the screen size)
            output = device.shell("wm size")
            log.info(f"Connected and ran command on device {device.serial}: {str(output)}")
            current_run.adb_device = device
            break
        except Exception as e:
            print(f"Failed to connect or run command on device {device.serial}: {e}")
    if not current_run.adb_device:
        log.info("No devices were successfully connected.")
        return
    elif reconfigure_screen:
        configure_screen()
    return


def adb_run_swipe(from_x, from_y, to_x, to_y, delay, source, skip_on_error=False, skip_extra_debug=False):
    try:
        if source == "loop" and not current_run.is_loop_active:
            log.info("Skipping Swipe Because Loop Was Deactivated")
            return
        log.debug(f"Swiping at: {from_x} {from_y} {to_x} {to_y} {delay}")
        current_run.adb_device.shell(f"input swipe {from_x} {from_y} {to_x} {to_y} {delay}")
        if not skip_extra_debug and custom_utils.is_extra_debug_active():
            custom_utils.save_extra_debug_image([[from_x, from_y], [to_x, to_y]], "swipe")
    except:
        if skip_on_error:
            return
        update_adb_connection(reconfigure_screen=True)
        adb_run_swipe(from_x, from_y, to_x, to_y, delay, source, skip_on_error=True, skip_extra_debug=skip_extra_debug)


def adb_run_tap(x ,y, source, skip_on_error=False, skip_extra_debug=False):
    try:
        if source == "loop" and not current_run.is_loop_active:
            log.info("Skipping Tap Because Loop Was Deactivated")
            return
        log.debug(f"Tapping at: {x}, {y}")
        current_run.adb_device.shell(f"input tap {x} {y}")
        if not skip_extra_debug and custom_utils.is_extra_debug_active():
            custom_utils.save_extra_debug_image([[x, y]], "tap")
    except:
        if skip_on_error:
            return
        update_adb_connection(reconfigure_screen=True)
        adb_run_tap(x ,y, source, skip_on_error=True, skip_extra_debug=skip_extra_debug)


def adb_run_screenshot(skip_on_error=False):
    try:
        return current_run.adb_device.screenshot()
    except:
        if skip_on_error:
            return
        update_adb_connection(reconfigure_screen=True)
        adb_run_screenshot(skip_on_error=True)


def adb_run_screen_size(skip_on_error=False):
    try:
        return current_run.adb_device.shell("wm size")
    except:
        if skip_on_error:
            log.debug("Couldn't find ADB active connection")
        update_adb_connection(reconfigure_screen=True)
        adb_run_screen_size(skip_on_error=True)


def configure_screen():
    try:
        response = current_run.adb_device.shell("wm size")
        # response = str(pipe.stdout.read()).strip() #type: ignore
        resolution = re.findall(r"\b\d{2,4}\s*x\s*\d{2,4}\b", response)[0]
        screen_utils.update_screen(constants.RESOLUTIONS[resolution])
    except Exception as ex:
        log.error(f"Couldn't load screen resolution: {ex}")
        pass

update_adb_connection(reconfigure_screen=True)