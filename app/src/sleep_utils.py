import time
from src import dropbox_utils, log_utils, custom_utils, config_utils, adb_commands
import os
from datetime import datetime, timedelta
from src.execution_variables import current_run

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
        verify_keep_or_stop_loop()
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
            
            print(f"File: {filename}, Line: {lineno}, Function: {name}")
        
        tb = tb.tb_next
        sleep_remaining_time(must_wait_until_time)

def verify_keep_or_stop_loop():
    should_pause = dropbox_utils.read_file_from_dropbox(dropbox_utils.PAUSE_EXECUTION_PATH)
    dropbox_utils.clear_file_in_dropbox(dropbox_utils.PAUSE_EXECUTION_PATH)
    if should_pause:
        log.info("Activating Disable Loop Variable Test")
        current_run.disable_loop = True
    should_disable_sleep = dropbox_utils.read_file_from_dropbox(dropbox_utils.PAUSE_SLEEP_PATH)
    dropbox_utils.clear_file_in_dropbox(dropbox_utils.PAUSE_SLEEP_PATH)
    if should_disable_sleep:
        log.info("Activating Disable Sleep Test")
        config_utils.update_config("sleep_machine", False) 
    return

def sleep_remaining_time(must_wait_until_time):
    remaining_time = must_wait_until_time - datetime.now()
    difference_in_seconds = remaining_time.total_seconds()
    log.info(f"Sleeping for more {difference_in_seconds / 60} minutes")
    time.sleep(difference_in_seconds)

def schedule_wakeup(seconds):
    log.debug("Entered on schedule_wakeup function")
    wakeup_time = datetime.now() + timedelta(seconds=seconds)
    wakeup_time_str = wakeup_time.strftime("%H:%M:%S")
    wakeup_date_str = wakeup_time.strftime("%d/%m/%Y")
    wosb_wakeup_str = str(timedelta(seconds=seconds))
    
    dropbox_utils.update_file_with_new_content(dropbox_utils.NEXT_AWAKE_TIME_PATH, f"Next Awake Time: {wakeup_date_str} {wakeup_time_str}")

    # https://dennisbabkin.com/wosb/

    command = f"wosb /closeall"
    log.info(f"Running '{command}'")
    os.system(command)

    command = f'START wosb /run /ami /systray tm="+{wosb_wakeup_str}" file="cmd.exe" params="/c exit"'
    # command = f'START wosb /run /ami /systray tm="+{wosb_wakeup_str}" file="Notepad" /screenon /keepscreenon'
    log.info(f"Running '{command}'")
    os.system(command)


def sleep_computer():
    # Run at Admin CMD "powercfg -hibernate off" ## This one altered the hibernate/sleep functions
    # Run at Admin CMD "bcdedit /set useplatformclock true" ## This will activate High Precision Timer Event - There's something BIOS related i'm not sure
    # But running this two commands into a new Windows 11 installation made things work (Since it is working i won't touch it anymore)
    log.info("Starting Sleep Command") 
    os.system(f"wosb /standby")
    time.sleep(2)
    current_run.awakened_from_sleep = True
    log.info("Sleep Timeout Ended") 