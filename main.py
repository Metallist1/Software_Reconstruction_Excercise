import copy
import os
import sys
from git import Repo
from pathlib import Path
import re
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pylab import rcParams
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

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
            if not [ele for ele in dependencies if (ele in import_from_line)] and not check_if_identical(
                    import_from_line, ".") and not check_if_identical(import_from_line, ".."):
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
            all_files_with_imports.append(
                Dependency(module_name_from_file_path(str(file_being_checked)), code_size(file_being_checked),
                           imports(file_being_checked, dependencies_to_ignore)))
        except:
            continue

    return all_files_with_imports


def get_imports_for_files_no_smaller_files(files_to_check, dependencies_to_ignore):
    all_files_with_imports = []
    for file_being_checked in files_to_check:
        try:
            all_files_with_imports.append(
                Dependency(module_name_from_file_path(str(file_being_checked)), code_size(file_being_checked),
                           imports_alt(file_being_checked, dependencies_to_ignore)))
        except:
            continue

    return all_files_with_imports


def imports_alt(file_to_get_imports, dependencies):
    lines = [line for line in open(file_to_get_imports)]

    all_imports = []
    for line in lines:
        try:
            import_from_line = extract_import_from_line(line)
            if not [ele for ele in dependencies if (ele in import_from_line)] and not check_if_Starts(
                    import_from_line, "."):
                all_imports.append(import_from_line)
        except:
            continue

    return all_imports


def check_if_Starts(message_to_check, condition_to_check):
    return message_to_check.startswith(condition_to_check)


def check_if_identical(message_to_check, condition_to_check):
    return message_to_check == condition_to_check


def dependencies_digraph(list_of_dependencies, to_exclude):
    G = nx.DiGraph()

    for dependency in list_of_dependencies:
        if not [ele for ele in to_exclude if (ele in dependency.name)]:
            source_module = dependency.name

            if source_module not in G.nodes:
                G.add_node(source_module, size=dependency.lines_of_code * 10, color="lightblue")

    for dependency in list_of_dependencies:
        if not [ele for ele in to_exclude if (ele in dependency.name)]:
            source_module = dependency.name

            for depends_on in dependency.depends_on:
                if not [ele for ele in to_exclude if (ele in depends_on)]:
                    if depends_on not in G.nodes:
                        G.add_node(depends_on, size=10, color="lightblue")

                    if depends_on and depends_on != source_module and depends_on in G.nodes:
                        G.add_edge(depends_on, source_module, color='black')
                        # print(source_module + "=>" + target_module + ".")

    return G


def remove_singleEdges(G):
    print(list(nx.isolates(G)))
    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def draw_graph_with_labels(G, figsize=(10, 10), prog='twopi', name="test4.png"):
    plt.figure(figsize=figsize)

    sizes = nx.get_node_attributes(G, "size")

    colors = nx.get_node_attributes(G, "color")

    pos = graphviz_layout(G, prog=prog)

    nx.draw(G, pos=pos,
            node_color=list(colors.values()),
            node_size=list(sizes.values()),
            font_color="red",
            font_size="10",
            with_labels=True,
            arrows=True)
    plt.savefig(name)
    plt.show()


print(dependencies_to_ignore)
print(imports(file_path('zeeguu/core/model/user.py'), dependencies_to_ignore))
print(len(files))
processed_files = get_imports_for_files(files, dependencies_to_ignore)
DG = dependencies_digraph(processed_files, [])
DGWE = remove_singleEdges(DG)

draw_graph_with_labels(DGWE,  (60, 60), 'neato', "dependency_graph_1.png")

new_list = get_imports_for_files_no_smaller_files(files, dependencies_to_ignore)
DGW = dependencies_digraph(new_list, [])
DGWEe = remove_singleEdges(DGW)


draw_graph_with_labels(DGWEe,  (60, 60), 'neato', "dependency_graph_2.png")

def has_depth(module_name, currentDepth):
    if "." in module_name:
        components = module_name.split(".")
        return len(components) - 1 >= currentDepth
    else:
        return 1 >= currentDepth


def getLast(module_name):
    components = module_name.split(".")
    return components[len(components) - 1]


def get_level_module(module_name, depth):
    if "." in module_name:
        skip = 0
        if depth > 1:
            skip = depth-1

        components = module_name.split(".")
        result = components[skip]
        newComp = components[skip+1:]
        if len(newComp) == 0 or depth == 0:
            return result
        else:
            count = 1 + skip
            for ele in newComp:

                result = result + "." + ele

                if count == depth:
                    return result
                count = count + 1

    else:
        return module_name

def get_level_module_no_skip(module_name, depth):
    if "." in module_name:
        components = module_name.split(".")
        result = components[0]
        newComp = components[1:]
        if len(newComp) == 0 or depth == 0:
            return result
        else:
            count = 1
            for ele in newComp:

                result = result + "." + ele

                if count == depth:
                    return result
                count = count + 1

    else:
        return module_name

def calculate_how_many_connections(G, currentItem):
    sizes = nx.get_node_attributes(G, "size")
    mentions = 100
    for key, val in sizes.items():
        if currentItem in key and currentItem != key:
            mentions = mentions + 100

    return mentions


def calculate_total_amount_of_code(G, currentItem):
    sizes = nx.get_node_attributes(G, "size")
    totalCode = 100
    for key, val in sizes.items():
        if key == currentItem:
            totalCode = totalCode + val

    return totalCode


def abstraceted_to_top_level(G):
    aG = nx.DiGraph()
    newcopy = list(copy.deepcopy(G.nodes()))
    x = 0
    while len(newcopy) > 0:
        for item in newcopy:
            if has_depth(item, x):
                if get_level_module(item, x) not in aG.nodes and get_level_module(item, x) != "":
                    if x == 0:
                        aG.add_node(get_level_module(item, x), size=calculate_total_amount_of_code(G,get_level_module_no_skip(item, x)), color="orange")
                    else:
                        aG.add_node(get_level_module(item, x), size=calculate_total_amount_of_code(G,get_level_module_no_skip(item, x)), color="lightblue")
                    if x > 0 and get_level_module(item, x - 1) != "":
                        source = get_level_module(item, x - 1)
                        destination = get_level_module(item, x)
                        if source != destination:
                            aG.add_edge(destination, source, color='black')

        newcopy2 = copy.deepcopy(newcopy)
        for item in newcopy:
            if not has_depth(item, x):
                newcopy2.remove(item)
        newcopy = newcopy2
        x = x + 1

    return aG


def abstraceted_to_top_level_connection_version(G):
    aG = nx.DiGraph()
    newcopy = list(copy.deepcopy(G.nodes()))
    x = 0
    while len(newcopy) > 0:
        for item in newcopy:
            if has_depth(item, x):
                if get_level_module(item, x) not in aG.nodes and get_level_module(item, x) != "":
                    if x == 0:
                        aG.add_node(get_level_module(item, x), size=calculate_how_many_connections(G,get_level_module_no_skip(item, x)), color="orange")
                    else:
                        aG.add_node(get_level_module(item, x), size=calculate_how_many_connections(G,get_level_module_no_skip(item, x)), color="lightblue")
                    if x > 0 and get_level_module(item, x - 1) != "":
                        source = get_level_module(item, x - 1)
                        destination = get_level_module(item, x)
                        if source != destination:
                            aG.add_edge(destination, source, color='black')

        newcopy2 = copy.deepcopy(newcopy)
        for item in newcopy:
            if not has_depth(item, x):
                newcopy2.remove(item)
        newcopy = newcopy2
        x = x + 1

    return aG



aG = abstraceted_to_top_level(DGWEe)
draw_graph_with_labels(aG, (60, 60), 'circo', "code_size_graph_v1.png")
draw_graph_with_labels(aG, (60, 60), 'neato', "code_size_graph_v2.png")

aGE = abstraceted_to_top_level_connection_version(DGWEe)
draw_graph_with_labels(aGE, (60, 60), 'circo', "connection_graph_v1.png")
draw_graph_with_labels(aGE, (60, 60), 'neato', "connection_graph_v2.png")
# draw_graph_with_labels(aG, (60, 60))
# draw_graph_with_labels(aG, (60, 60), 'circo', "test6.png")
# for file_being_checked in processed_files:
# print(file_being_checked.name, file_being_checked.lines_of_code, file_being_checked.depends_on)
