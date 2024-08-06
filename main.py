import hashlib
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
import shutil
from shutil import copy, copytree, rmtree
from time import sleep
import dirhash
from pip._internal.resolution.resolvelib import found_candidates

SOURCE_FOLDER = "/usr/home/maxfx/source"
BACKUP_FOLDER = "/usr/home/maxfx/backup"
WORKERS = 4


def hash_file(filename):
    """Returns the SHA-256 hash of the file."""
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def compare_folders(dir1, dir2):
    if dir1 == dir2:
        if dirhash.dirhash(os.path.join(SOURCE_FOLDER, dir1),"sha256", empty_dirs=True) == (dirhash.dirhash(os.path.join(BACKUP_FOLDER, dir2),"sha256", empty_dirs=True)):
            return True
        else:
            return False
    else:
        return True

def copy_files(src_paths, dest_dir):
    for src_path in src_paths:
        try:

            ensure_directory_exists(dest_dir)
            dest_path = shutil.copy2(src_path, dest_dir)
            print(f'.copied {src_path} to {dest_path}', flush=True)
        except OSError as exc:
            print("catch exception: " ,exc)
def copy_dir(src_paths, dest_dir):
    try:
        for src_path in src_paths:
            dest_path = shutil.copytree(src_path, os.path.join(dest_dir, os.path.basename(src_path)), dirs_exist_ok=True)
            print(f'.copied dir {src_path} to {dest_path}', flush=True)
    except OSError as exc:
           print("Catch exception: ", exc)


def copyFiles(src_files, dest_dir):
    with ProcessPoolExecutor(WORKERS) as exe:
        # split the copy operations into chunks
        for i in range(0, len(src_files), math.ceil(len(src_files) / WORKERS)):
            # select a chunk of filenames
            filenames = src_files[i:(i + (math.ceil(len(src_files) / WORKERS)))]
            # submit the batch copy task
            _ = exe.submit(copy_files, filenames, dest_dir)


def copyDirs(src_files, dest_dir):
    with ProcessPoolExecutor(WORKERS) as exe:
        # split the copy operations into chunks
        for i in range(0, len(src_files), math.ceil(len(src_files) / WORKERS)):
            # select a chunk of dirnames
            dirnames = src_files[i:(i + (math.ceil(len(src_files) / WORKERS)))]
            # submit the batch copy task
            _ = exe.submit(copy_dir, dirnames, dest_dir)

def delete_extra_files(source_folder, backup_folder):
    for root, dirs, files in os.walk(backup_folder, topdown=False):
        for name in files:
            path_backup = os.path.join(root, name)
            rel_path = os.path.relpath(path_backup, backup_folder)
            path_source = os.path.join(source_folder, rel_path)

            if not os.path.exists(path_source):
                os.remove(path_backup)
                print(f"Deleted {path_backup}")

def delete_extra_directories(source_folder, backup_folder):
    for root, dirs, files in os.walk(backup_folder, topdown=False):
        for name in dirs:
            path_backup = os.path.join(root, name)
            rel_path = os.path.relpath(path_backup, backup_folder)
            path_source = os.path.join(source_folder, rel_path)

            if not os.path.exists(path_source):
                shutil.rmtree(path_backup)
                print(f"Deleted directory {path_backup}")

def copy_empty_directories(source_folder, backup_folder):
    for root, dirs, files in os.walk(source_folder, topdown=True):
        for dir_name in dirs:
            source_dir = os.path.join(root, dir_name)
            if not os.listdir(source_dir):  # Check if the directory is empty
                rel_path = os.path.relpath(source_dir, source_folder)
                backup_dir = os.path.join(backup_folder, rel_path)

                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                    print(f"Created empty directory {backup_dir}")
def ensure_directory_exists(file_path):
    """Ensure the directory for the file_path exists."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == '__main__':

    # main loop
    while True:
        start_time = time.time()

        if not os.path.exists(SOURCE_FOLDER):
            print("Directory '%s' created" % SOURCE_FOLDER)
            os.makedirs(SOURCE_FOLDER, exist_ok=True)
        else:
            print("Folder %s already exists" % SOURCE_FOLDER)

        if not os.path.exists(BACKUP_FOLDER):
            print("Directory '%s' created" % BACKUP_FOLDER)
            os.makedirs(BACKUP_FOLDER, exist_ok=True)
        else:
            print("Folder %s already exists" % BACKUP_FOLDER)

        found_new_files = []

        found_new_files = []
        backup_path = ""
        for root, dirs, files in os.walk(SOURCE_FOLDER, topdown=False):
            files.sort()
            for name in files:
                path1 = os.path.join(root, name)
                rel_path = os.path.relpath(path1, SOURCE_FOLDER)
                path2 = os.path.join(BACKUP_FOLDER, rel_path)

                print("rel_path: ", rel_path)
                print("path1: ", path1)
                print("path2:", path2)

                #backup_path = path2

                if os.path.exists(path2):
                    ctime1 = os.path.getmtime(path1)
                    ctime2 = os.path.getmtime(path2)

                    if ctime1 != ctime2:
                        #if(os.path.samefile(path1, path2)):
                            print(f"{path1} and {path2} have different modification timestamps.")
                            found_new_files.append(path1)
                            copyFiles(found_new_files, path2)
                            found_new_files.clear()
                else:
                    print(f"{path2} does not exist in the second directory.")
                    # not exist in backup folder, all copy to backup folder
                    found_new_files.append(path1)
                    copyFiles(found_new_files, path2)
                    found_new_files.clear()


            delete_extra_files(SOURCE_FOLDER, BACKUP_FOLDER)
            delete_extra_directories(SOURCE_FOLDER, BACKUP_FOLDER)
            copy_empty_directories(SOURCE_FOLDER, BACKUP_FOLDER)

        #if len(found_new_files) > 0:
        #   copyFiles(found_new_files, backup_path)

            #for name in files:
            #    print(os.path.join(root, name))
            #for name in dirs:
            #   print(os.path.join(root, name))




        # source_content = os.listdir(SOURCE_FOLDER)
        # backup_content = os.listdir(BACKUP_FOLDER)
        #
        # source_content.sort()
        # backup_content.sort()
        #
        # files = []
        # dirs_path = []
        # files_from_dir = []
        # for file in source_content:
        #     if os.path.isfile(os.path.join(SOURCE_FOLDER, file)):
        #         for bak in backup_content:
        #             if not bak in source_content:
        #                 if os.path.isfile(os.path.join(BACKUP_FOLDER, bak)):
        #                     os.remove(os.path.join(BACKUP_FOLDER, bak))
        #                     backup_content.remove(bak)
        #
        #         if file in backup_content:
        #             if compare_files(os.path.join(SOURCE_FOLDER, file), os.path.join(BACKUP_FOLDER, file)):
        #                 print("same")
        #             else:
        #                 files.append(os.path.join(SOURCE_FOLDER, file))
        #         else:
        #             # backup folder is empty
        #             print(os.path.join(SOURCE_FOLDER, file))
        #             files.append(os.path.join(SOURCE_FOLDER, file))
        #
        #     elif os.path.isdir(os.path.join(SOURCE_FOLDER, file)):
        #         for bak in backup_content:
        #             if not bak in source_content:
        #                 if os.path.isdir(os.path.join(BACKUP_FOLDER, bak)):
        #                     shutil.rmtree(os.path.join(BACKUP_FOLDER, bak))
        #                     backup_content.remove(bak)
        #
        #         if os.path.isdir(os.path.join(SOURCE_FOLDER, file)):
        #             for bak in backup_content:
        #                 if os.path.isdir(os.path.join(BACKUP_FOLDER, bak)):
        #                     if not compare_folders(file, bak):
        #                         print("checkum folder is same")
        #                         print("file: ",os.path.join(SOURCE_FOLDER, file))
        #                         dirs_path.append(os.path.join(SOURCE_FOLDER, file))
        #
        #     if not file in backup_content:
        #         # backup folder is empty
        #         if os.path.isdir(os.path.join(SOURCE_FOLDER, file)):
        #                 dirs_path.append(os.path.join(SOURCE_FOLDER, file))
        #
        # if len(files) > 0:
        #     copyFiles(files, BACKUP_FOLDER)
        #     files.clear()
        # if len(dirs_path) > 0:
        #     copyDirs(dirs_path, BACKUP_FOLDER)
        #     dirs_path.clear()
        #
        # for bak in backup_content:
        #     if not bak in source_content:
        #         if os.path.isfile(os.path.join(BACKUP_FOLDER, bak)):
        #             os.remove(os.path.join(BACKUP_FOLDER, bak))
        #             backup_content.remove(bak)
        #         elif os.path.isdir(os.path.join(BACKUP_FOLDER, bak)):
        #             shutil.rmtree(os.path.join(BACKUP_FOLDER, bak))
        #             backup_content.remove(bak)


        print('Done')

        end_time = time.time()
        print("Total time taken:", end_time - start_time)
        sleep(5)
