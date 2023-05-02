import os
import sys
from git import Repo
from pathlib import Path
import re

cwd = os.getcwd()
CODE_ROOT_FOLDER = cwd + "/content/Zeeguu-API/"

Requirements_Folder = cwd + "/requirements.txt"

files_to_exclude = ['', 'test']
# If the file exists, it means we've already downloaded
if not os.path.exists(CODE_ROOT_FOLDER):
    Repo.clone_from("https://github.com/zeeguu/API", CODE_ROOT_FOLDER)


# helper function to get a file path w/o having to always provide the /content/Zeeguu-API/ prefix
def file_path(file_name):
    return CODE_ROOT_FOLDER + file_name


assert (file_path("zeeguu/core/model/user.py") == cwd + "/content/Zeeguu-API/zeeguu/core/model/user.py")

dependencies_to_ignore = []
with open(Requirements_Folder) as file:
    for line in file:
        dependencies_to_ignore.append(line.rstrip().lower())


def get_all_files_without_type(files_to_exclude):
    files = []
    for file in Path(CODE_ROOT_FOLDER).rglob("*.py"):
        if [x for x in files_to_exclude if x not in file.as_uri()]:
            files.append(file)
    return files


files = get_all_files_without_type(files_to_exclude)


def extract_import_from_line(line):
    # TODO: think about how to detect imports when
    # they are inside a function / method
    x = re.search("^import (\S+)", line)
    x = re.search("^from (\S+)", line)
    return x.group(1)


def imports(file_to_get_imports, dependencies):
    lines = [line for line in open(file_to_get_imports)]

    all_imports = []
    for line in lines:
        try:
            import_from_line = extract_import_from_line(line)
            if not [ele for ele in dependencies if (ele in import_from_line)]:
                all_imports.append(import_from_line)
        except:
            continue

    return all_imports


print(dependencies_to_ignore)
print(imports(file_path('zeeguu/core/model/user.py'), dependencies_to_ignore))
print(len(files))
