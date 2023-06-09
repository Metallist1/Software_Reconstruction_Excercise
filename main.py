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

files_to_exclude = []


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
        if not [ele for ele in files_to_exclude if (ele in file.as_uri())]:
            files.append(file)
    return files


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

    colors_of_edge = nx.get_edge_attributes(G, 'color')

    pos = graphviz_layout(G, prog=prog)

    nx.draw(G, pos=pos,
            node_color=list(colors.values()),
            node_size=list(sizes.values()),
            edge_color=list(colors_of_edge.values()),
            font_color="red",
            font_size="18",
            with_labels=True,
            arrows=True)
    plt.savefig(name)
    # plt.show()
    plt.close()


# files = get_all_files_without_type(files_to_exclude)
# processed_files = get_imports_for_files(files, dependencies_to_ignore)
# DG = dependencies_digraph(processed_files, ["test", "model", "tools", "util"])
# DGWE = remove_singleEdges(DG)
# draw_graph_with_labels(DGWE, (60, 60), 'neato', "dependency_graph_v1.png")
# draw_graph_with_labels(DGWE, (60, 60), 'circo', "dependency_graph_v2.png")

# new_list = get_imports_for_files_no_smaller_files(files, dependencies_to_ignore)
# DGW = dependencies_digraph(new_list, ["test", "model", "tools", "util"])
# DGWEe = remove_singleEdges(DGW)


# draw_graph_with_labels(DGWEe, (60, 60), 'neato', "dependency_graph_v3.png")
# draw_graph_with_labels(DGWEe, (60, 60), 'circo', "dependency_graph_v4.png")


def has_depth(module_name, current_depth, depth_cap):
    if "." in module_name:
        components = module_name.split(".")
        if depth_cap > 0:
            return len(components) - 1 >= current_depth and depth_cap >= current_depth
        else:
            return len(components) - 1 >= current_depth
    else:
        return 1 >= current_depth


def getLast(module_name):
    components = module_name.split(".")
    return components[len(components) - 1]


def get_level_name(module_name, depth):
    if "." in module_name:
        skip = 0
        if depth > 1:
            skip = depth - 1

        components = module_name.split(".")
        result = components[skip]
        newComp = components[skip + 1:]
        if len(newComp) == 0 or depth == 0:
            return result
        else:
            count = 1 + skip
            for ele in newComp:

                result = ele

                if count == depth:
                    return result
                count = count + 1

    else:
        return module_name


def get_level_module(module_name, depth):
    if "." in module_name:
        skip = 0
        if depth > 1:
            skip = depth - 1

        components = module_name.split(".")
        result = components[skip]
        newComp = components[skip + 1:]
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
    mentions = 10
    for key, val in sizes.items():
        if currentItem in key and currentItem != key:
            # Limit size to 50 for readabily.
            if mentions < 50:
                mentions = mentions + 1

    return mentions


def calculate_total_amount_of_code(G, currentItem):
    sizes = nx.get_node_attributes(G, "size")
    totalCode = 10 # Initial node size
    for key, val in sizes.items():
        if key == currentItem:
            totalCode = totalCode + val
            # Reduce code size by certain % as the node size becomes extremely large.
            if totalCode > 50:
                totalCode = totalCode / 10

    return totalCode


def abstraceted_to_top_level(G, depth_cap=-1):
    aG = nx.DiGraph()
    newcopy = list(copy.deepcopy(G.nodes()))
    x = 0
    while len(newcopy) > 0:
        for item in newcopy:
            if has_depth(item, x, depth_cap):
                if get_level_module(item, x) not in aG.nodes and get_level_module(item, x) != "":
                    if x == 0:
                        aG.add_node(get_level_module(item, x),
                                    label=get_level_name(item, x),
                                    size=calculate_total_amount_of_code(G, get_level_module_no_skip(item, x)) + 50,
                                    color="orange")
                    else:
                        aG.add_node(get_level_module(item, x),
                                    label=get_level_name(item, x),
                                    size=calculate_total_amount_of_code(G, get_level_module_no_skip(item, x)),
                                    color="lightblue")
                    if x > 0 and get_level_module(item, x - 1) != "":
                        source = get_level_module(item, x - 1)
                        destination = get_level_module(item, x)
                        if source != destination:
                            aG.add_edge(destination, source, color='black')

        newcopy2 = copy.deepcopy(newcopy)
        for item in newcopy:
            if not has_depth(item, x, depth_cap):
                newcopy2.remove(item)
        newcopy = newcopy2
        x = x + 1

    return aG


def abstraceted_to_top_level_connection_version(G, depth_cap=-1):
    aG = nx.DiGraph()
    newcopy = list(copy.deepcopy(G.nodes()))
    x = 0
    while len(newcopy) > 0:
        for item in newcopy:
            if has_depth(item, x, depth_cap):
                if get_level_module(item, x) not in aG.nodes and get_level_module(item, x) != "":
                    if x == 0:
                        aG.add_node(get_level_module(item, x),
                                    label=get_level_name(item, x),
                                    size=calculate_how_many_connections(G, get_level_module_no_skip(item, x)),
                                    color="orange")
                    else:
                        aG.add_node(get_level_module(item, x),
                                    label=get_level_name(item, x),
                                    size=calculate_how_many_connections(G, get_level_module_no_skip(item, x)),
                                    color="lightblue")
                    if x > 0 and get_level_module(item, x - 1) != "":
                        source = get_level_module(item, x - 1)
                        destination = get_level_module(item, x)
                        if source != destination:
                            aG.add_edge(destination, source, color='black')

        newcopy2 = copy.deepcopy(newcopy)
        for item in newcopy:
            if not has_depth(item, x, depth_cap):
                newcopy2.remove(item)
        newcopy = newcopy2
        x = x + 1

    return aG


def get_biggest_reference(aG, target, depth_cap):
    if depth_cap < 0:
        depth_cap = 100
    isFound = False
    valueToGet = ""
    current_cap = depth_cap
    while not isFound:
        for node in aG.nodes():
            if has_depth(target, current_cap, depth_cap):
                if node == get_level_module(target, current_cap):
                    isFound = True
                    valueToGet = node
                    break
        current_cap = current_cap - 1
        if current_cap < 0:
            isFound = True
            break

    return valueToGet


def add_dependency_edges(G, aG, depth_cap=-1, ignore_edges=[]):
    for each in G.edges():
        if not [ele for ele in ignore_edges if (ele in each[0])] and not [ele for ele in ignore_edges if
                                                                          (ele in each[1])]:
            source = get_biggest_reference(aG, each[0], depth_cap)
            destination = get_biggest_reference(aG, each[1], depth_cap)
            if source != destination and aG.has_node(source) and aG.has_node(destination) and not aG.has_edge(
                    destination, source):
                aG.add_edge(destination, source, color='orange')
            # aG.add_edge(source, destination)
    return aG


def draw_graph3(networkx_graph, notebook=True, output_filename='graph.html', show_buttons=True,
                only_physics_buttons=False):
    """
    This function accepts a networkx graph object,
    converts it to a pyvis network object preserving its node and edge attributes,
    and both returns and saves a dynamic network visualization.

    Valid node attributes include:
        "size", "value", "title", "x", "y", "label", "color".

        (For more info: https://pyvis.readthedocs.io/en/latest/documentation.html#pyvis.network.Network.add_node)

    Valid edge attributes include:
        "arrowStrikethrough", "hidden", "physics", "title", "value", "width"

        (For more info: https://pyvis.readthedocs.io/en/latest/documentation.html#pyvis.network.Network.add_edge)


    Args:
        networkx_graph: The graph to convert and display
        notebook: Display in Jupyter?
        output_filename: Where to save the converted network
        show_buttons: Show buttons in saved version of network?
        only_physics_buttons: Show only buttons controlling physics of network?
    """

    # import
    from pyvis import network as net

    # make a pyvis network
    pyvis_graph = net.Network(notebook=notebook)

    # for each node and its attributes in the networkx graph
    for node, node_attrs in networkx_graph.nodes(data=True):
        pyvis_graph.add_node(str(node), **node_attrs)

    # for each edge and its attributes in the networkx graph
    for source, target, edge_attrs in networkx_graph.edges(data=True):
        # if value/width not specified directly, and weight is specified, set 'value' to 'weight'
        if not 'value' in edge_attrs and not 'width' in edge_attrs and 'weight' in edge_attrs:
            # place at key 'value' the weight of the edge
            edge_attrs['value'] = edge_attrs['weight']
        # add the edge
        pyvis_graph.add_edge(str(source), str(target), **edge_attrs)

    # turn buttons on
    if show_buttons:
        if only_physics_buttons:
            pyvis_graph.show_buttons(filter_=['physics'])
        else:
            pyvis_graph.show_buttons()

    # return and also save
    return pyvis_graph.show(output_filename)


for n in range(5):
    if n != 0:
        # Add "tools", "test", "model", "apimux", "wordstats", "setuptools", "python", "util" to exclude individual files
        # from analysis
        files_to_exclude = []
        files = get_all_files_without_type(files_to_exclude)
        new_list = get_imports_for_files_no_smaller_files(files, dependencies_to_ignore)

        # Add options to remove files from being added into the graph
        DGW = dependencies_digraph(new_list,
                                   [])
        DGWEe = remove_singleEdges(DGW)

        aG = abstraceted_to_top_level(DGWEe, n)
        removed_aG = remove_singleEdges(aG)
        # Add variables to ignore adding dependencies to
        addedEdges_code = add_dependency_edges(DGWEe, removed_aG, n,
                                               [])

        aGE = abstraceted_to_top_level_connection_version(DGWEe, n)
        removed_aGE = remove_singleEdges(aGE)
        # Add variables to ignore adding dependencies to
        addedEdges = add_dependency_edges(DGWEe, removed_aGE, n,
                                          [])

        draw_graph3(addedEdges_code, True, 'graph_code_depth' + str(n) + '.html')
        draw_graph3(addedEdges, True, 'graph_depth' + str(n) + '.html')
