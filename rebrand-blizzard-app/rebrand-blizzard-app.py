import os
import re
import sys
import time
import yaml
import psutil
import winreg
import tkinter
import subprocess
import logging.config

from shutil import copy
from pathlib import Path
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showinfo, askyesno

reg_key_path = r'SOFTWARE\WOW6432Node\Blizzard Entertainment\Battle.net\Capabilities'
reg_key_value_name = 'ApplicationIcon'

log = None


def setup_logging():
    log_config_file = 'logs/log_config.yaml'
    if os.path.exists(log_config_file):
        with open(log_config_file, 'r') as infile:
            config = yaml.safe_load(infile)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.warning('Log config could not be loaded, falling back to logging.basicConfig().')


def get_registry_key_value(key_path, value_name):
    """Checks registry for Battle.net install directory.

    The registry has multiple views (32 and 64 bit) that are accessed
    by using the different access keys (winreg.KEY_WOW64_32KEY and winreg.KEY_WOW64_32KEY).
    """
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path,
                            access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as regkey:
            raw_value = winreg.QueryValueEx(regkey, value_name)
            log.debug('Registry key raw value: {}'.format(raw_value))
            value_data, _ = raw_value
            return value_data
    except WindowsError:
        log.error('Could not find Battle.net registry entry.')
        return None


def create_path_object(value_data):
    """Registry value has extra bits we don't need, strip them and make a pathlib path."""
    log.debug('value_data: {}'.format(value_data))
    bnet_exe_path = value_data.split(',')[0]
    if bnet_exe_path.startswith('"') and bnet_exe_path.endswith('"'):
        bnet_exe_path = bnet_exe_path[1:-1]
    return Path(bnet_exe_path)


def ask_base_install_dir(initial_dir):
    """Ask user to confirm install location."""
    return askdirectory(
        initialdir=initial_dir,
        mustexist=True,
        title='Please select the install location of Battle.net.'
    )


def check_selected_base_path(path_object):
    """Confirm the install path by verifying certain files."""
    files_to_check = ['Battle.net.exe', 'Battle.net Launcher.exe', 'BlizzardError.exe']
    for file_name in files_to_check:
        path_to_check = path_object / file_name
        if not path_to_check.exists():
            msg = (
                'The following path does not seem to be the base install '
                'of Battle.net because it does not have the file: {} in it. '
                'Path: {}'.format(file_name, path_object.as_posix())
            )
            log.error(msg)
            sys.exit('Exiting...')


def check_selected_app_path(path_object):
    """Confirm the app path by verifying certain files."""
    files_to_check = ['Battle.net.mpq', 'Battle.net.exe', 'Battle.net Helper.exe']
    for file_name in files_to_check:
        path_to_check = path_object / file_name
        if not path_to_check.exists():
            msg = (
                'The following path does not seem to be an app install of '
                'Battle.net because it does not have the file: {} in it. '
                'Path: {}'.format(file_name, path_object.as_posix())
            )
            log.error(msg)
            sys.exit('Exiting...')


def get_registry_path():
    """Checks registry for Battle.net install directory."""
    reg_path_string = get_registry_key_value(reg_key_path, reg_key_value_name)
    if reg_path_string is not None:
        reg_likely_path = create_path_object(reg_path_string).parent
        if reg_likely_path.exists():
            return reg_likely_path
        else:
            msg = 'Path does not exist: {}'.format(reg_likely_path.as_posix())
            log.error(msg)
            sys.exit('Exiting...')
    else:
        return None


def get_user_path(initial_dir):
    """Ask user for install location to confirm."""
    user_dir = ask_base_install_dir(initial_dir)
    log.debug('user_dir: {}'.format(user_dir))
    if not user_dir:
        msg = 'User canceled the ask directory dialog.'
        log.debug(msg)
        sys.exit('Exiting...')
    user_path = Path(user_dir)
    if not user_path.exists():
        msg = 'Path does not exist: {}'.format(user_path.as_posix())
        log.error(msg)
        sys.exit('Exiting...')
    return user_path


def get_install_path():
    """Use registry and asking the user to better determine the install directory."""
    reg_likely_path = get_registry_path()
    if reg_likely_path:
        user_path = get_user_path(initial_dir=reg_likely_path.as_posix())
    else:
        user_path = get_user_path(initial_dir=r'C:/Program Files (x86)/')

    if reg_likely_path != user_path:
        msg = (
            'Registry path and user defined path do not match. '
            'reg_likely_path: {} != user_path: {}'.format(reg_likely_path, user_path)
        )
        log.error(msg)
        sys.exit('Exiting...')

    check_selected_base_path(user_path)

    return user_path


def get_latest_app_install(install_path):
    """Locate the most up to date Battle.net install.

    Blizzard keeps multiple installs of Battle.net in the install folder
    in the form of Battle.net.0000. Use regex to match that plus an optional
    digit to still work when the version number hits 5 digits.
    """
    child_dirs = [child for child in install_path.iterdir() if child.is_dir()]
    app_installs = []
    for item in child_dirs:
        # Match Battle.net.8554 with an optional extra digit.
        if re.fullmatch(r'^Battle\.net\.\d{4}(\d)?$', item.name):
            app_installs.append(item)
    return max(app_installs)


def backup_mpq_file(latest_app_path):
    """Make sure a backup exists, but don't overwrite it."""
    mpq_file = latest_app_path / 'Battle.net.mpq'
    mpq_backup = latest_app_path / 'Battle.net.mpq.backup'
    if not mpq_backup.exists():
        copy(mpq_file.as_posix(), mpq_backup.as_posix())


def confirm_patch(latest_app_path):
    """Confirm that the user wants to patch the MPQ file."""
    mpq_file = latest_app_path / 'Battle.net.mpq'
    result = askyesno(
        'Confirm Patch',
        "Patch Archive: {}?".format(mpq_file)
    )
    return result


def patch_mpq_archive(latest_app_path):
    """Patch the MPQ archive using http://www.zezula.net/en/mpq/download.html"""
    mpq_file = latest_app_path / 'Battle.net.mpq'
    original_size = mpq_file.stat().st_size
    # MPQEditor.exe add Battle.net.mpq resources/* resources /r
    subprocess.run(['MPQEditor.exe', 'add', mpq_file.as_posix(),
                    'resources/*', 'resources', '/r'], check=True)
    end_size = mpq_file.stat().st_size
    log.debug('MPQ original size: {}'.format(original_size))
    log.debug('MPQ end size: {}'.format(end_size))
    if end_size == original_size:
        msg = (
            'The patch operation was run, but the original and current size '
            'of the MPQ file is the same. This probably means that Battle.net '
            'is still running and is accessing Battle.net.mpq, which is '
            'preventing this program fromm opening the file. '
            'Make sure Battle.net is completely closed (from tray).'
        )
        log.error(msg)
        sys.exit('Exiting...')


def battle_net_is_closed():
    """The MPQ archive can't be patched if Battle.net is still running. Check if it is."""
    names_to_check = ['Battle.net.exe', 'Battle.net Launcher.exe', 'Battle.net Helper.exe']
    for process in psutil.process_iter():
        try:
            if process.name() in names_to_check:
                return False
        except psutil.NoSuchProcess:
            log.exception('Tried to access a process that does not exist.')
    return True


def close_battle_net():
    """Terminate the process using the equivalent of SIGTERM."""
    for process in psutil.process_iter():
        try:
            if process.name() == 'Battle.net.exe':
                process.terminate()
                process.wait(timeout=2)
        except psutil.NoSuchProcess:
            log.exception('Tried to access a process that does not exist.')


def main():
    setup_logging()
    global log
    log = logging.getLogger(__name__)
    log.debug('Program start.')

    # Hide GUI root window.
    root = tkinter.Tk()
    root.withdraw()

    if not battle_net_is_closed():
        result = askyesno('Close Battle.net', 'Battle.net is still running, do you want to force close it?')
        if result:
            close_battle_net()
            time.sleep(1)
    if not battle_net_is_closed():
        log.error('Battle.net is not closed. Can not access MPQ file.')
        sys.exit('Exiting...')

    install_path = get_install_path()
    latest_app_path = get_latest_app_install(install_path)
    # Will raise an exception if path doesn't have necessary files.
    check_selected_app_path(latest_app_path)
    backup_mpq_file(latest_app_path)
    if confirm_patch(latest_app_path):
        patch_mpq_archive(latest_app_path)
        showinfo('Finished', 'The Blizzard App should now be Battle.net again.')
    log.debug('Program finish.')


if __name__ == "__main__":
    main()
