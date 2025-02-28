import json
import os

from utils import run_shell_command

class InvalidFolderNameProvided(Exception): pass

def query_done_poet_paths(args):
    mandatory_provided_folder_names = ['spacemesh_post_1', 'spacemesh_post_2']

    if args['target_folder_name'] not in mandatory_provided_folder_names:
        raise InvalidFolderNameProvided(f"Provided folder name must be these values '{mandatory_provided_folder_names}'.")

    def find_folders(root_dir, target_names):
        found_folders = []

        for dirpath, dirnames, filenames in os.walk(root_dir):
            for dirname in dirnames:
                if dirname in target_names:
                    found_folders.append(os.path.join(dirpath, dirname))

        return found_folders

    # Define the root directory and target folder names
    root_directory = '/mnt/'

    # Find the folders
    found_folders = find_folders(root_directory, args['target_folder_name'])

    final_folders = []
    if found_folders:
        for folder in found_folders:
            try:
                with open(f"{folder}/postdata_metadata.json") as post_metadata:
                    data = json.loads(post_metadata.read())
            except FileNotFoundError:
                continue
            files_count = int(run_shell_command(f"ls -1 {folder} | wc -l").split('\n')[0])
            if files_count == data['NumUnits'] * 32 + 2:
                folder_number = folder.split("/")[2].split("_")[1]
                final_folders.append((folder_number, data['NumUnits']))
                pass
        else:
            print(final_folders)
            return final_folders
    else:
        print("No matching folders found.")
