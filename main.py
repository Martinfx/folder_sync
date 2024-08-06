import hashlib
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
import shutil
from shutil import copy, copytree, rmtree
from time import sleep
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("sync_folders.log"),
    logging.StreamHandler()
])
def hash_file(filename):
    """Returns the SHA-256 hash of the file."""
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def copy_files(src_paths, dest_dir):
    for src_path in src_paths:
        try:
            ensure_directory_exists(dest_dir)
            dest_path = shutil.copy2(src_path, dest_dir)
            logging.info(f'.copied {src_path} to {dest_path}', flush=True)
        except OSError as exc:
            logging.info("catch exception: " ,exc)
def copy_dir(src_paths, dest_dir):
    try:
        for src_path in src_paths:
            dest_path = shutil.copytree(src_path, os.path.join(dest_dir, os.path.basename(src_path)), dirs_exist_ok=True)
            logging.info(f'.copied dir {src_path} to {dest_path}', flush=True)
    except OSError as exc:
           logging.info("Catch exception: ", exc)


def copy_files_in_parallel(src_files, dest_dir):
    with ProcessPoolExecutor(WORKERS) as exe:
        # split the copy operations into chunks
        for i in range(0, len(src_files), math.ceil(len(src_files) / WORKERS)):
            # select a chunk of filenames
            filenames = src_files[i:(i + (math.ceil(len(src_files) / WORKERS)))]
            # submit the batch copy task
            _ = exe.submit(copy_files, filenames, dest_dir)


def copy_dirs_in_parallel(src_files, dest_dir):
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
                logging.info(f"Deleted {path_backup}")

def delete_extra_directories(source_folder, backup_folder):
    for root, dirs, files in os.walk(backup_folder, topdown=False):
        for name in dirs:
            path_backup = os.path.join(root, name)
            rel_path = os.path.relpath(path_backup, backup_folder)
            path_source = os.path.join(source_folder, rel_path)

            if not os.path.exists(path_source):
                shutil.rmtree(path_backup)
                logging.info(f"Deleted directory {path_backup}")

def copy_empty_directories(source_folder, backup_folder):
    for root, dirs, files in os.walk(source_folder, topdown=True):
        for dir_name in dirs:
            source_dir = os.path.join(root, dir_name)
            if not os.listdir(source_dir):  # Check if the directory is empty
                rel_path = os.path.relpath(source_dir, source_folder)
                backup_dir = os.path.join(backup_folder, rel_path)

                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                    logging.info(f"Created empty directory {backup_dir}")
def ensure_directory_exists(file_path):
    """Ensure the directory for the file_path exists."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sync two folders")
    parser.add_argument("-s", "--source-path", required=True, help="Path to source directory")
    parser.add_argument("-b", "--backup-path", required=True, help="Path to backup directory")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Number of worker processes")
    parser.add_argument("-c", "--checksum", action="store_true", help="Use SHA-256 checksum for file comparison, default is mtime comparison")
    parser.add_argument("-i", "--sync-interval", type=int, default=5,help="Sync interval in seconds (default: 5 seconds)")

    args = parser.parse_args()

    SOURCE_FOLDER = args.source_path
    BACKUP_FOLDER = args.backup_path
    WORKERS = args.workers
    USE_CHECKSUM = args.checksum
    SYNC_INTERVAL = args.sync_interval

    while True:
        start_time = time.time()

        if not os.path.exists(SOURCE_FOLDER):
            logging.info("Directory '%s' created" % SOURCE_FOLDER)
            os.makedirs(SOURCE_FOLDER, exist_ok=True)
        else:
            logging.info("Folder %s already exists" % SOURCE_FOLDER)

        if not os.path.exists(BACKUP_FOLDER):
            logging.info("Directory '%s' created" % BACKUP_FOLDER)
            os.makedirs(BACKUP_FOLDER, exist_ok=True)
        else:
            logging.info("Folder %s already exists" % BACKUP_FOLDER)

        found_new_files = []
        for root, dirs, files in os.walk(SOURCE_FOLDER, topdown=False):
            files.sort()
            for name in files:
                path1 = os.path.join(root, name)
                rel_path = os.path.relpath(path1, SOURCE_FOLDER)
                path2 = os.path.join(BACKUP_FOLDER, rel_path)

                if os.path.exists(path2):
                    if USE_CHECKSUM:
                        hash1 = hash_file(path1)
                        hash2 = hash_file(path2)
                        if hash1 != hash2:
                            logging.info(f"{path1} and {path2} have different checksums.")
                            found_new_files.append(path1)
                            copy_files_in_parallel(found_new_files, BACKUP_FOLDER)
                            found_new_files.clear()
                    else:
                        mtime1 = os.path.getmtime(path1)
                        mtime2 = os.path.getmtime(path2)
                        if mtime1 != mtime2:
                            logging.info(f"{path1} and {path2} have different modification timestamps.")
                            found_new_files.append(path1)
                            copy_files_in_parallel(found_new_files, BACKUP_FOLDER)
                            found_new_files.clear()
                else:
                    logging.info(f"{path2} does not exist in the second directory.")
                    # not exist in backup folder, all copy to backup folder
                    found_new_files.append(path1)
                    copy_files_in_parallel(found_new_files, path2)
                    found_new_files.clear()


            delete_extra_files(SOURCE_FOLDER, BACKUP_FOLDER)
            delete_extra_directories(SOURCE_FOLDER, BACKUP_FOLDER)
            copy_empty_directories(SOURCE_FOLDER, BACKUP_FOLDER)

        logging.info('Synchronization cycle completed.')

        end_time = time.time()
        logging.info("Total time taken: %.2f seconds", end_time - start_time)
        sleep(SYNC_INTERVAL)
