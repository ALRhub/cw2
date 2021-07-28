import os
from typing import List, Dict, Any

from cw2.cw_config import cw_conf_keys as KEY


def normalize_expanded_paths(expanded_config_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """normalizes path key after expansion operation

    Args:
        expanded_config_list (List[Dict[str, Any]]): list fo expanded experiment configs

    Returns:
        List[Dict[str, Any]]: noramlized expanded experiment configs
    """
    # Set Path and LogPath Args depending on the name
    for _config in expanded_config_list:
        _config[KEY.PATH] = os.path.join(_config[KEY.i_BASIC_PATH],
                                         _config[KEY.i_NEST_DIR], _config[KEY.i_EXP_NAME])
        _config[KEY.LOG_PATH] = os.path.join(_config[KEY.PATH], 'log')
    return expanded_config_list


def make_rel_paths(config: Dict[str, Any], base_path: str) -> Dict[str, Any]:
    """converts relevant paths of the config into relative paths

    Args:
        config (Dict[str, Any]): experiment config
        base_path (str): base path

    Returns:
        Dict[str, Any]: experiment config with paths relative to base_path
    """
    c = config.copy()
    _basic_path = base_path
    c[KEY.LOG_PATH] = os.path.join(".",
                                   os.path.relpath(c[KEY.LOG_PATH], _basic_path))
    c[KEY.i_REP_LOG_PATH] = os.path.join(".",
                                         os.path.relpath(c[KEY.i_REP_LOG_PATH], _basic_path))
    c[KEY.PATH] = os.path.join(".",
                               os.path.relpath(c[KEY.PATH], _basic_path))
    c[KEY.i_BASIC_PATH] = os.path.join(".",
                                       os.path.relpath(c[KEY.i_BASIC_PATH], _basic_path))
    return c
