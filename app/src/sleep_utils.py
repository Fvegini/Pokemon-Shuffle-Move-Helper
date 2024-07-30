import time
from src import dropbox_utils, log_utils, custom_utils, config_utils, adb_commands
import os
from datetime import datetime, timedelta
from src.execution_variables import current_run
from src.telegram_utils import current_bot

log = log_utils.get_logger()

def make_it_sleep(sleep_seconds):
    must_wait_until_time = datetime.now() + timedelta(seconds=sleep_seconds)
    try:
        if sleep_seconds < 180 or not custom_utils.is_sleep_machine_enabled():
            time.sleep(sleep_seconds)
        else:
            schedule_wakeup(sleep_seconds)
            sleep_computer()
            if datetime.now() > must_wait_until_time:
                log.debug("Wake from Sleep went OK")
            else:
                log.error("Waked Early from sleep, sleeping the rest of the time")
                sleep_remaining_time(must_wait_until_time)
    except Exception as ex:
        log.error(ex)
        # Extract the last traceback object
        tb = ex.__traceback__
        
        # Iterate through the traceback to get details
        while tb is not None:
            frame = tb.tb_frame
            lineno = tb.tb_lineno
            filename = frame.f_code.co_filename
            name = frame.f_code.co_name
            log.debug(f"File: {filename}, Line: {lineno}, Function: {name}")
            tb = tb.tb_next
        sleep_remaining_time(must_wait_until_time)

def sleep_remaining_time(must_wait_until_time):
    remaining_time = must_wait_until_time - datetime.now()
    difference_in_seconds = remaining_time.total_seconds()
    log.info(f"Sleeping for more {difference_in_seconds / 60} minutes")
    time.sleep(difference_in_seconds)

def schedule_wakeup(seconds):
    log.debug("Entered on schedule_wakeup function")
    wakeup_time_str = (datetime.now() + timedelta(seconds=seconds)).strftime("%H:%M:%S")
    send_telegram_message(f"Next Awake Time: {wakeup_time_str}")

    # https://dennisbabkin.com/wosb/
    command = f"wosb /closeall"
    log.info(f"Running '{command}'")
    os.system(command)

    for extra_time in [0, 60, 120]:
        command = f'START wosb /run /ami /systray tm="+{str(timedelta(seconds=(seconds + extra_time)))}" file="cmd.exe" params="/c exit"'
        log.info(f"Running '{command}'")
        os.system(command)
    return

def send_telegram_message(text):
    try:
        log.debug("Sending message to telegram")
        current_bot.send_message(text)
        log.debug("Sent")
    except Exception as ex:
        log.error(f"Error on sending telegram message - {ex}")


def sleep_computer():
    # Run at Admin CMD "powercfg -hibernate off" ## This one altered the hibernate/sleep functions
    # Run at Admin CMD "bcdedit /set useplatformclock true" ## This will activate High Precision Timer Event - There's something BIOS related i'm not sure
    # But running this two commands into a new Windows 11 installation made things work (Since it is working i won't touch it anymore)
    log.info("Starting Sleep Command") 
    os.system(f"wosb /standby")
    time.sleep(2)
    current_run.awakened_from_sleep = True
    log.info("Sleep Timeout Ended") 