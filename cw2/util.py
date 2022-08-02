import datetime
import os
import re

try:
    from collections.abc import MutableMapping, Mapping, MutableSequence  # noqa
except ImportError:
    from collections import MutableMapping, Mapping, MutableSequence  # noqa


def deep_update(base_dict: dict, update_dict: dict) -> dict:
    """Updates the base dictionary with corresponding values from the update dictionary, including nested collections.
       Not updated values are kept as is.

    Arguments:
        base_dict {dict} -- dictionary to be updated
        update_dict {dict} -- dictianry holding update values

    Returns:
        dict -- dictanry with updated values
    """
    for key, value in update_dict.items():
        # Update Recursively
        if isinstance(value, Mapping):
            branch = deep_update(base_dict.get(key, {}), value)
            base_dict[key] = branch
        else:
            base_dict[key] = update_dict[key]
    return base_dict


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, MutableSequence):
            keys = map(lambda i: new_key + "_" + str(i), range(len(v)))
            items.extend(zip(keys, v))
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_dict_to_tuple_keys(d: MutableMapping):
    flat_dict = {}
    for k, v in d.items():
        if isinstance(v, MutableMapping):
            sub_dict = flatten_dict_to_tuple_keys(v)
            flat_dict.update({(k, *sk): sv for sk, sv in sub_dict.items()})

        elif isinstance(v, MutableSequence):
            flat_dict[(k,)] = v

    return flat_dict


def insert_deep_dictionary(d: MutableMapping, t: tuple, value):
    if type(t) is tuple:
        if len(t) == 1:  # tuple contains only one key
            d[t[0]] = value
        else:  # tuple contains more than one key
            if t[0] not in d:
                d[t[0]] = dict()
            insert_deep_dictionary(d[t[0]], t[1:], value)
    else:
        d[t] = value


def append_deep_dictionary(d: MutableMapping, t: tuple, value):
    if type(t) is tuple:
        if len(t) == 1:  # tuple contains only one key
            if t[0] not in d:
                d[t[0]] = []
            d[t[0]].append(value)
        else:  # tuple contains more than one key
            if t[0] not in d:
                d[t[0]] = dict()
            append_deep_dictionary(d[t[0]], t[1:], value)
    else:
        d[t] = value


def format_time(time_in_secs: float) -> str:
    return str(datetime.timedelta(seconds=time_in_secs))


def shorten_param(_param_name):
    name_parts = _param_name.split('.')
    shortened_parts = '.'.join(map(lambda s: s[:3], name_parts[:-1]))
    shortened_leaf = ''.join(map(lambda s: s[0], name_parts[-1].split('_')))
    if shortened_parts:
        return shortened_parts + '.' + shortened_leaf
    else:
        return shortened_leaf


def get_size(start_path: str):
    """recursively compute size of a directory

    Args:
        start_path (str): directory path

    Returns:
        size in MByte
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / 1000000.0


def check_subdir(parent: str, child: str) -> bool:
    """Check if the child is a subdirectory of the parent.

    Args:
        parent (str): Path of the suspected parent dir
        child (str): path of the suspected child dir

    Returns:
        bool: True if child is subdir of parent
    """
    parent_path = os.path.abspath(parent)
    child_path = os.path.abspath(child)

    return os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])


def convert_param_names(_param_names: list, values: list) -> str:
    """create new shorthand name derived from parameter and value association
    Arguments:
        _param_names (list): parameter names for the experiment
        values (list): concrete values for each parameter

    Returns:
        str: shorthand name
    """

    _converted_name = '_'.join("{}{}".format(
        shorten_param(k), v) for k, v in zip(_param_names, values))
    # _converted_name = re.sub("[' \[\],()]", '', _converted_name)
    _converted_name = re.sub("[' ]", '', _converted_name)
    _converted_name = re.sub('["]', '', _converted_name)
    _converted_name = re.sub("[(\[]", '_', _converted_name)
    _converted_name = re.sub("[)\]]", '', _converted_name)
    _converted_name = re.sub("[,]", '_', _converted_name)
    return _converted_name


def get_file_names_in_directory(directory: str) -> [str]:
    """
    Get file names in given directory
    Args:
        directory: directory where you want to explore

    Returns:
        file names in a list

    """
    file_names = None
    try:
        (_, _, file_names) = next(os.walk(directory))
        if len(file_names) == 0:
            file_names = None
    except StopIteration as e:
        print("Cannot read files from directory: ", directory)
    return file_names
