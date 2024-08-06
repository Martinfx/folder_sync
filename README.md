# Folder Synchronization Tool
## Overview

The Folder Synchronization Tool is a Python-based application that synchronizes two directories by copying new or modified files from a source directory to a backup directory. It also allows for the deletion of files and directories that are no longer present in the source directory. The tool can run continuously at a specified interval, making it ideal for keeping backup copies up-to-date.

## Features

   - Synchronizes Files: Copies new and modified files from the source directory to the backup directory.
   - Checksum Verification: Optionally verifies file integrity using SHA-256 checksums.
   - Empty Directory Handling: Creates empty directories in the backup if they exist in the source.
   - Automatic Cleanup: Deletes files and directories from the backup that are no longer present in the source.
   - Configurable Sync Interval: Allows the user to specify how often the synchronization should occur.
   - Logging: Provides detailed logging of actions performed, both in the console and in a log file.

Requirements

    Python 3.6 or higher
    Required libraries:
        argparse (for command-line argument parsing)

Usage

To run the application, use the following command:

bash

python sync_folders.py -s <source-path> -b <backup-path> [-w <workers>] [-c] [-i <sync-interval>]

Command Line Arguments

    -s, --source-path: Required. Path to the source directory that you want to back up.
    -b, --backup-path: Required. Path to the backup directory where files will be copied.
    -w, --workers: Optional. Number of worker processes to use for copying files. Default is 4.
    -c, --checksum: Optional. Use SHA-256 checksum for file comparison instead of modification time.
    -i, --sync-interval: Optional. Sync interval in seconds (default is 5 seconds).

Example

bash

python sync_folders.py -s /path/to/source -b /path/to/backup -w 4 -c -i 10

This command will synchronize the specified source and backup directories, using 4 worker processes, verifying files with checksums, and running every 10 seconds.
Logging

The application logs its operations to both the console and a file named sync_folders.log. You can find detailed information about copied files, created directories, and any errors encountered during synchronization in this log file.
