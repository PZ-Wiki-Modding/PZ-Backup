import sys, shutil, os, datetime, re, threading
from enum import Enum
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import sv_ttk

## ARGS

home = Path.home()

# if windows
# if sys.platform.startswith("win"):
if sys.platform.startswith("linux"):
    DEFAULT_BACKUP_DIR = home / "PZ_Backups"
    DEFAULT_PZ_PATH = home / ".steam/steam/steamapps/common/ProjectZomboid/projectzomboid"
    DEFAULT_PZ_CACHE = home / "Zomboid"
else:
    # default to windows path, since it's more common
    DEFAULT_BACKUP_DIR = home / "PZ_Backups"
    DEFAULT_PZ_PATH = "C:/Program Files (x86)/Steam/steamapps/common/ProjectZomboid"
    DEFAULT_PZ_CACHE = home / "Zomboid"
DEFAULT_BACKUP_NAME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


class FolderType(Enum):
    INSTALL = "install"
    CACHE = "cache"
    BACKUP = "backup"


## INIT

pz_install_path = Path(DEFAULT_PZ_PATH).expanduser()
pz_cache_path = Path(DEFAULT_PZ_CACHE).expanduser()
pz_backup_path = Path(DEFAULT_BACKUP_DIR).expanduser()
pz_backup_name_entry = None
log_text = None


## METHODS

def log(message: str):
    """
    Write a message to the log panel
    """
    global log_text
    if log_text is not None:
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, message + "\n")
        log_text.see(tk.END)  # auto-scroll to bottom
        log_text.config(state=tk.DISABLED)
    print(message)

def validate_folder(path: Path, type: FolderType) -> bool:
    """
    Validate the various folders based on their type. Conditions depends on the type of the folder.
    """
    # validate the folder
    if type == FolderType.INSTALL:
        # the install folder should contain:
        # - a folder "media"
        # - a file "ProjectZomboid32.json"
        # - a file "ProjectZomboid64.json"
        # - and is in steamapps/common
        if ((path / "media").is_dir() 
            and (path / "ProjectZomboid32.json").is_file()
            and (path / "ProjectZomboid64.json").is_file()):
            # verify the path contains "steamapps/common"
            if "steamapps/common" not in str(path).replace("\\", "/"):
                return False
            return True  # valid folder
        else:
            return False

    elif type == FolderType.CACHE:
        # the cache folder should contain:
        # - a folder "mods"
        # - a folder "Saves"
        # - a file "options.ini"
        if ((path / "mods").is_dir() 
            and (path / "Saves").is_dir() 
            and (path / "options.ini").is_file()):
            return True  # valid folder
        else:
            return False
    elif type == FolderType.BACKUP:
        # for backup folder, we just check if it's a valid directory (it can be empty or not exist yet)
        if path.is_dir() or not path.exists():
            return True
        else:
            return False
    else:
        raise ValueError("Unknown folder type")
        
def get_wrong_folder_message(type: FolderType) -> str:
    """
    Retrieve the error message to display when the user selects an invalid folder based on the type of the folder.
    """
    if type == FolderType.INSTALL:
        return "Invalid installation folder. Please select the correct Project Zomboid installation folder."
    elif type == FolderType.CACHE:
        return "Invalid cache folder. Please select the correct Project Zomboid cache folder (saves, mods, etc)."
    elif type == FolderType.BACKUP:
        return "Invalid backup folder. Please select a valid backup folder."
    else:
        raise ValueError("Unknown folder type")

def select_folder(type: FolderType, entry: ttk.Entry):
    """
    Used to ask the user to select a folder, which we then validate and update the corresponding entry field. The type parameter is used to know which folder we are selecting (install, cache or backup), so we can validate it properly and update the correct global variable.
    """
    global pz_install_path, pz_cache_path, pz_backup_path
    while True:
        if type == FolderType.INSTALL:
            initialdir = pz_install_path
        elif type == FolderType.CACHE:
            initialdir = pz_cache_path
        elif type == FolderType.BACKUP:
            initialdir = pz_backup_path
        else:
            raise ValueError("Unknown folder type")
        folder = filedialog.askdirectory(title="Select your Project Zomboid installation folder", initialdir=initialdir)
        if folder:  # user didn't cancel
            folder = Path(folder).resolve()
            # validate the folder
            if validate_folder(folder, type):
                # update the entry field
                if type == FolderType.INSTALL:
                    pz_install_path = folder
                elif type == FolderType.CACHE:
                    pz_cache_path = folder
                elif type == FolderType.BACKUP:
                    pz_backup_path = folder
                entry.delete(0, tk.END)
                entry.insert(0, str(folder))
                break  # exit loop
            else:
                mess = get_wrong_folder_message(type)
                messagebox.showerror("Invalid folder", mess)
        else:
            # user cancelled, exit loop
            break

def parse_default_mods(cache_path: Path) -> list[str]:
    """
    Parse the cache/mods/default.txt file to find the currently loaded mods.
    """
    mod_ids = []

    PATERN = re.compile(r"\s*mod\s*=\s*(?P<mod_id>[\S\s]+?),")

    with open(cache_path / "mods" / "default.txt", "r") as f:
        m = PATERN.findall(f.read())
        if m:
            mod_ids = m
    return mod_ids

def parse_workshop_mods(path: Path, mod_ids) -> dict[str, Path]:
    """
    We want to parse the workshop mods for their mod.info files, and check if those contain a mod ID in the list of currently loaded mods. If they do, we store the path in a list to copy later the folder `workshop_path/workshop_id/mods` content into the cache folder mods folder. That way, we have a local copy of the mods.
    """
    # retrieve every mod.info files in the workshop folder
    mod_info_files = list(path.glob("**/mod.info"))
    mod_id_to_name = {}
    for mod_info_file in mod_info_files:
        try:
            with open(mod_info_file, "r") as f:
                # find first match for "id=mod_id"
                m = re.search(r"id\s*=\s*(?P<mod_id>[^\n]+)", f.read())
                if m:
                    mod_id = m.group("mod_id").strip()
                    if mod_id in mod_ids:
                        # we found a mod that is currently loaded, find its mods path
                        while re.search(r"108600/\d+/mods$", str(mod_info_file)) is None:
                            mod_info_file = mod_info_file.parent
                        mod_id_to_name[mod_id] = mod_info_file
        except Exception as e:
            log("Error parsing mod info file {}: {}".format(mod_info_file, e))
    return mod_id_to_name

def run():
    """
    Run the backup of the select installation.
    """
    global pz_install_path, pz_cache_path, pz_backup_path, pz_backup_name_entry, log_text
    assert pz_backup_name_entry is not None, "Backup name entry field is not initialized"
    pz_backup_name = pz_backup_name_entry.get().strip()

    log("Starting backup with installation folder: {}, cache folder: {}, backup folder: {}, backup name: {}".format(
        pz_install_path, pz_cache_path, pz_backup_path, pz_backup_name))

    # verify the provided folders are correct
    if not validate_folder(pz_install_path, FolderType.INSTALL):
        messagebox.showerror("Invalid folder", 
                             get_wrong_folder_message(FolderType.INSTALL))
        return
    if not validate_folder(pz_cache_path, FolderType.CACHE):
        messagebox.showerror("Invalid folder", 
                             get_wrong_folder_message(FolderType.CACHE))
        return
    if not validate_folder(pz_backup_path, FolderType.BACKUP):
        messagebox.showerror("Invalid folder", 
                             get_wrong_folder_message(FolderType.BACKUP))
        return

    # from the PZ install path, we retrieve the workshop path
    # steamapps/workshop/content/108600
    pz_workshop_path = pz_install_path
    while pz_workshop_path.name != "steamapps":
        pz_workshop_path = pz_workshop_path.parent
        if pz_workshop_path == pz_workshop_path.parent:
            messagebox.showerror("Error", "Could not find steamapps folder in the installation path")
            return
    pz_workshop_path = pz_workshop_path / "workshop" / "content" / "108600"

    # init the backup folder
    pz_backup_path = pz_backup_path / pz_backup_name
    os.makedirs(pz_backup_path, exist_ok=True)

    # copy the install folder
    log("Copying installation folder...")
    to_copy_install = pz_install_path
    if sys.platform.startswith("linux"):
        # on linux we need to copy the parent folder, bcs it contains the launch script
        to_copy_install = pz_install_path.parent
    shutil.copytree(to_copy_install, pz_backup_path / "install", dirs_exist_ok=True)
    log("Copied installation folder from {} to {}".format(to_copy_install, pz_backup_path / "install"))

    # copy the cache folder
    log("Copying cache folder...")
    shutil.copytree(pz_cache_path, pz_backup_path / "cache", dirs_exist_ok=True)
    log("Copied cache folder from {} to {}".format(pz_cache_path, pz_backup_path / "cache"))

    # load and find mods 
    mod_ids = parse_default_mods(pz_cache_path)
    mod_id_to_name = parse_workshop_mods(pz_workshop_path, mod_ids)

    # copy the mods folders of the loaded workshop mods to the cache folder mods folder
    for mod_id, mod_info_file in mod_id_to_name.items():
        log("Copying mod {} with id {}".format(mod_info_file, mod_id))
        shutil.copytree(mod_info_file, pz_backup_path / "cache" / "mods", dirs_exist_ok=True)

    # create the launch script for Linux and Windows to launch the game
    # in no Steam mode and linking to the backup cache folder
    if sys.platform.startswith("linux"):
        shutil.move(pz_backup_path / "install" / "projectzomboid.sh", pz_backup_path / "install" / "old_projectzomboid.sh")
        launch_script_path = pz_backup_path / "projectzomboid.sh"
        with open(launch_script_path, "w") as f:
            f.write(f"""#!/bin/bash
./install/old_projectzomboid.sh -cachedir="{pz_backup_path / "cache"}" -nosteam "$@"
""")
        os.chmod(launch_script_path, 0o755)
        log("Created launch script for Linux at {}".format(launch_script_path))
    else:
        # 32-bit
        shutil.move(pz_backup_path / "install" / "ProjectZomboid32.exe", pz_backup_path / "install" / "old_ProjectZomboid32.exe")
        launch_script_path_32 = pz_backup_path / "ProjectZomboid32.bat"
        with open(launch_script_path_32, "w") as f:
            f.write(f"""@echo off
install\\old_ProjectZomboid32.exe -cachedir="{pz_backup_path / "cache"}" -nosteam %*
""")
        log("Created launch script for Windows at {}".format(launch_script_path_32))

        # 64-bit
        shutil.move(pz_backup_path / "install" / "ProjectZomboid64.exe", pz_backup_path / "install" / "old_ProjectZomboid64.exe")
        launch_script_path_64 = pz_backup_path / "ProjectZomboid64.bat"
        with open(launch_script_path_64, "w") as f:
            f.write(f"""@echo off
install\\old_ProjectZomboid64.exe -cachedir="{pz_backup_path / "cache"}" -nosteam %*
""")
        log("Created launch script for Windows at {}".format(launch_script_path_64))

    log("Backup completed successfully!")
    messagebox.showinfo("Success", "Backup completed successfully!")
    log("")


## MAIN

def main():
    global pz_install_path, pz_cache_path, pz_backup_path, pz_backup_name_entry, log_text

    root = tk.Tk()
    root.title("Project Zomboid Backup Tool")
    # root.geometry("400x300")
    ttk.Label(root, text="Project Zomboid Backup Tool", font=("Arial", 16, "bold")).pack(pady=10)

    frame = ttk.Frame(root)
    frame.pack(expand=True)

    # PZ install dir
    pz_install_label = ttk.Label(frame, text="Select your Project Zomboid installation folder:")
    pz_install_label.grid(row=0, column=0, padx=5, pady=5)

    pz_install_dir = ttk.Entry(frame, width=50)
    pz_install_dir.grid(row=1, column=0, padx=5)
    pz_install_dir.insert(0, str(pz_install_path))  # default path

    pz_install_button = ttk.Button(frame, text="...", command=lambda: select_folder(FolderType.INSTALL, pz_install_dir))
    pz_install_button.grid(row=1, column=1, padx=5)

    # PZ cache dir
    pz_cache_label = ttk.Label(frame, text="Select your Project Zomboid cache folder (saves, settings, etc):")
    pz_cache_label.grid(row=2, column=0, padx=5, pady=5)

    pz_cache_dir = ttk.Entry(frame, width=50)
    pz_cache_dir.grid(row=3, column=0, padx=5)
    pz_cache_dir.insert(0, str(pz_cache_path))  # default path

    pz_cache_button = ttk.Button(frame, text="...", command=lambda: select_folder(FolderType.CACHE, pz_cache_dir))
    pz_cache_button.grid(row=3, column=1, padx=5)

    # backup dir
    pz_backup_label = ttk.Label(frame, text="Select your backup folder:")
    pz_backup_label.grid(row=4, column=0, padx=5, pady=5)

    pz_backup_dir = ttk.Entry(frame, width=50)
    pz_backup_dir.grid(row=5, column=0, padx=5)
    pz_backup_dir.insert(0, str(pz_backup_path))  # default path

    pz_backup_button = ttk.Button(frame, text="...", command=lambda: select_folder(FolderType.BACKUP, pz_backup_dir))
    pz_backup_button.grid(row=5, column=1, padx=5)

    # backup name
    pz_backup_name_label = ttk.Label(frame, text="Backup name (optional):")
    pz_backup_name_label.grid(row=6, column=0, padx=5, pady=5)

    pz_backup_name_entry = ttk.Entry(frame, width=50)
    pz_backup_name_entry.grid(row=7, column=0, padx=5)
    pz_backup_name_entry.insert(0, DEFAULT_BACKUP_NAME)  # default name

    # run button, we make it run in a separate thread to avoid freezing the UI
    # since the backup can take some time and we want to be able to display logs in real time
    run_button = ttk.Button(root, text="Run Backup", command=lambda: threading.Thread(target=run, daemon=True).start())
    run_button.pack(pady=10)

    # log panel which takes the whole right part of the window, with a scrollbar
    log_frame = ttk.Frame(root)
    log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    ttk.Label(log_frame, text="Logs:").pack(anchor=tk.W)
    log_text = tk.Text(log_frame, state=tk.DISABLED)
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=log_scrollbar.set)



    # set theme based on system preference
    # tho it doesn't even properly detect dark mode on my distro ...
    # sv_ttk.set_theme(darkdetect.theme())
    # sv_ttk.set_theme("dark")
    sv_ttk.use_dark_theme()


    root.mainloop()
    
    sys.exit(0)



if __name__ == "__main__":
    main()