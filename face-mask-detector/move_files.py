import os
from os import path
import shutil


src = ""
dest = "Image_Dataset"

tmp = "Tmp"

file_id = 0
if os.listdir(dest):
    file_id = int(max(os.listdir(dest)).split('.')[0]) + 1

dirs = [dir_ for dir_ in os.listdir(src) if path.isdir(path.join(src, dir_))]

for _dir in dirs:
    dir_path = path.join(src, _dir)
    files_in_dir = os.listdir(dir_path)

    for file in files_in_dir:
        filepath = path.join(dir_path, file)
        tmp_filepath = path.join(tmp, str(file_id)) + ".jpg"
        if path.isfile(filepath):
            shutil.copy(filepath, tmp)  # move to tmp to prevent overwriting a file with similar name
            os.rename(path.join(tmp, file), tmp_filepath)  # rename
            shutil.copy(tmp_filepath, dest)  # move to dest
            try:
                os.remove(tmp_filepath)
            except OSError:
                pass
            file_id += 1
