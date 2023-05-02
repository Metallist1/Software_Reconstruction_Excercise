import os
import sys
from git import Repo
from pathlib import Path
import re

cwd = os.getcwd()
CODE_ROOT_FOLDER = cwd + "/content/Zeeguu-API/"

Requirements_Folder = cwd + "/requirements.txt"

files_to_exclude = ['', 'test']


class Dependency:
    def __init__(self, name, lines_of_code, depends_on):
        self.name = name
        self.lines_of_code = lines_of_code
        self.depends_on = depends_on


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
def code_size(file):
    return sum([1 for line in open(file)])

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
            if not [ele for ele in dependencies if (ele in import_from_line)] and not check_if_Starts(import_from_line,"."):
                all_imports.append(import_from_line)
        except:
            continue

    return all_imports


# extracting a module name from a file name
def module_name_from_file_path(full_path):
    # e.g. ../core/model/user.py -> zeeguu.core.model.user

    file_name = full_path[len(CODE_ROOT_FOLDER):]
    file_name = file_name.replace("/__init__", "")
    file_name = file_name.replace("\__init__", "")
    file_name = file_name.replace("/__main__", "")
    file_name = file_name.replace("\__main__", "")
    file_name = file_name.replace("/", ".")
    file_name = file_name.replace("\\", ".")
    file_name = file_name.replace(".py", "")
    return file_name


def get_imports_for_files(files_to_check, dependencies_to_ignore):
    all_files_with_imports = []
    for file_being_checked in files_to_check:
        try:
            all_files_with_imports.append(Dependency(module_name_from_file_path(str(file_being_checked)), code_size(file_being_checked),
                                                     imports(file_being_checked, dependencies_to_ignore)))
        except:
            continue

    return all_files_with_imports


def check_if_Starts(message_to_check, condition_to_check):
    return message_to_check.startswith(condition_to_check)

assert 'zeeguu.core.model.user' == module_name_from_file_path(file_path('zeeguu/core/model/user.py'))
print(dependencies_to_ignore)
print(imports(file_path('zeeguu/core/model/user.py'), dependencies_to_ignore))
print(len(files))
processed_files = get_imports_for_files(files, dependencies_to_ignore)
for file_being_checked in processed_files:
    print(file_being_checked.name, file_being_checked.lines_of_code, file_being_checked.depends_on)
