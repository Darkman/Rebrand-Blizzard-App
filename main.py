import re
import psutil
import winreg
import logging
import tkinter
import subprocess

from shutil import copy
from pathlib import Path
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showinfo, askyesno

reg_key_path = r'SOFTWARE\WOW6432Node\Blizzard Entertainment\Battle.net\Capabilities'
reg_key_value_name = 'ApplicationIcon'


def get_registry_key_value(key_path, value_name):
    """Checks registry for Battle.net install directory.

    The registry has multiple views (32 and 64 bit) that are accessed
    by using the different access keys (winreg.KEY_WOW64_32KEY and winreg.KEY_WOW64_32KEY).
    """
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path,
                            access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as regkey:
            raw_value = winreg.QueryValueEx(regkey, value_name)
            value_data, _ = raw_value
            return value_data
    except WindowsError as e:
        print(e)
        return None


def create_path_object(value_data):
    """Registry value has extra bits we don't need, strip them and make a pathlib path."""
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
            return False
    return True


def check_selected_app_path(path_object):
    """Confirm the app path by verifying certain files."""
    files_to_check = ['Battle.net.mpq', 'Battle.net.exe', 'Battle.net Helper.exe']
    for file_name in files_to_check:
        path_to_check = path_object / file_name
        if not path_to_check.exists():
            return False
    return True


def get_registry_path():
    """Checks registry for Battle.net install directory."""
    reg_path_string = get_registry_key_value(reg_key_path, reg_key_value_name)
    if reg_path_string is not None:
        reg_likely_path = create_path_object(reg_path_string).parent
        if reg_likely_path.exists():
            return reg_likely_path
        else:
            raise Exception('Path does not exist.')
    else:
        return None


def get_user_path(initial_dir):
    """Ask user for install location to confirm."""
    user_dir = ask_base_install_dir(initial_dir)
    if not user_dir:
        raise Exception('User canceled file dialog.')
    user_path = Path(user_dir)
    if not user_path.exists():
        raise Exception('Path does not exist')
    return user_path


def get_install_path():
    """Use registry and asking the user to better determine the install directory."""
    reg_likely_path = get_registry_path()
    if reg_likely_path:
        user_path = get_user_path(initial_dir=reg_likely_path.as_posix())
    else:
        user_path = get_user_path(initial_dir=r'C:/Program Files (x86)/')

    if reg_likely_path != user_path:
        raise Exception('reg_likely_path and user_dir do not match.')

    if not check_selected_base_path(user_path):
        raise Exception('Incorrect install path.')

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
    subprocess.run(['MPQEditor.exe', 'add', mpq_file.as_posix(), 'resources/*', 'resources', '/r'], check=True)
    end_size = mpq_file.stat().st_size
    if end_size == original_size:
        raise Exception('Could not access mpq file. Is Battle.net completely closed (from tray)?')


def battle_net_is_closed():
    names_to_check = ['Battle.net.exe', 'Battle.net Launcher.exe', 'Battle.net Helper.exe']
    for proc in psutil.process_iter():
        try:
            if proc.name() in names_to_check:
                return False
        except psutil.NoSuchProcess:
            pass
    return True


def main():
    # Hide GUI root window.
    root = tkinter.Tk()
    root.withdraw()

    if not battle_net_is_closed():
        raise Exception('Battle.net is not closed. Can not access MPQ file.')
    install_path = get_install_path()
    latest_app_path = get_latest_app_install(install_path)
    if not check_selected_app_path(latest_app_path):
        raise Exception('App path does not meet requirements.')
    backup_mpq_file(latest_app_path)
    if confirm_patch(latest_app_path):
        patch_mpq_archive(latest_app_path)
        showinfo('Finished', 'The Blizzard App should now be Battle.net again.')


if __name__ == "__main__":
    main()
