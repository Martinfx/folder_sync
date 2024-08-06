import hashlib
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from shutil import copy, copytree
from time import sleep
import dirhash

SOURCE_FOLDER = "/usr/home/maxfx/source"
BACKUP_FOLDER = "/usr/home/maxfx/backup"
WORKERS = 4


def compare_files(file1, file2):
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            if hashlib.md5(f1.read()).hexdigest() == hashlib.md5(f2.read()).hexdigest():
                return True
            else:
                return False

    except OSError as e:
        f1.close()
        f2.close()
        print("Could not read file:", file, "or", file2)
        return False

def compare_folders(dir1, dir2):
    if dir1 == dir2:
        if dirhash.dirhash(os.path.join(SOURCE_FOLDER, dir1),"md5", empty_dirs=True) == (dirhash.dirhash(os.path.join(BACKUP_FOLDER, dir2),"md5", empty_dirs=True)):
            return True
        else:
            return False
    else:
        return True

def copy_files(src_paths, dest_dir):
    for src_path in src_paths:
        dest_path = copy(src_path, dest_dir)
        print(f'.copied {src_path} to {dest_path}', flush=True)

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

        source_content = os.listdir(SOURCE_FOLDER)
        backup_content = os.listdir(BACKUP_FOLDER)

        source_content.sort()
        backup_content.sort()

        files = []
        dirs_path = []
        files_from_dir = []
        for file in source_content:
            if os.path.isfile(os.path.join(SOURCE_FOLDER, file)):
                for bak in backup_content:
                    if not bak in source_content:
                        if os.path.isfile(os.path.join(BACKUP_FOLDER, bak)):
                            os.remove(os.path.join(BACKUP_FOLDER, bak))
                            backup_content.remove(bak)

                if file in backup_content:
                    if compare_files(os.path.join(SOURCE_FOLDER, file), os.path.join(BACKUP_FOLDER, file)):
                        print("same")
                    else:
                        files.append(os.path.join(SOURCE_FOLDER, file))
                else:
                    # backup folder is empty
                    print(os.path.join(SOURCE_FOLDER, file))
                    files.append(os.path.join(SOURCE_FOLDER, file))

            elif os.path.isdir(os.path.join(SOURCE_FOLDER, file)):
                for bak in backup_content:
                    if not bak in source_content:
                        if os.path.isdir(os.path.join(BACKUP_FOLDER, bak)):
                            shutil.rmtree(os.path.join(BACKUP_FOLDER, bak))
                            backup_content.remove(bak)

                if os.path.isdir(os.path.join(SOURCE_FOLDER, file)):
                    for bak in backup_content:
                        if os.path.isdir(os.path.join(BACKUP_FOLDER, bak)):
                            if not compare_folders(file, bak):
                                print("checkum folder is same")
                                print("file: ",os.path.join(SOURCE_FOLDER, file))
                                dirs_path.append(os.path.join(SOURCE_FOLDER, file))

            if not file in backup_content:
                if os.path.isdir(os.path.join(SOURCE_FOLDER, file)):
                    if len(dirs_path) > 0:
                        dirs_path.append(os.path.join(SOURCE_FOLDER, file))

            if len(files) > 0:
                copyFiles(files, BACKUP_FOLDER)
                files.clear()
            if len(dirs_path) > 0:
                copyDirs(dirs_path, BACKUP_FOLDER)
                dirs_path.clear()

        print('Done')

        end_time = time.time()
        print("Total time taken:", end_time - start_time)
        sleep(5)
