#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Jan 13 14:37:21 2022

@author: Nacriema

Refs:

"""
from functools import wraps
from pathlib import Path

from numpy.random import seed as np_seed
from numpy.random import get_state as np_get_state
from numpy.random import set_state as np_set_state
from random import seed as rand_seed
from random import getstate as rand_get_state
from random import setstate as rand_set_state
import torch
from torch import manual_seed as torch_seed
from torch import get_rng_state as torch_get_state
from torch import set_rng_state as torch_set_state


def coerce_to_path_and_check_exist(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError('{} does not exist'.format(path.absolute()))
    return path


def coerce_to_path_and_create_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_files_from_dir(dir_path, valid_extensions=None, name_filter=None, include_name_filter=True, recursive=False, sort=False):
    """ Get list of file in specific folder given by: file type, file name. This will give the recursive option or not as
    well as the result is sorted or not.

    Args:
        dir_path (str): Input path we want to find all files
        valid_extensions (str or list of str): Specify all file extensions we want to find
        name_filter (str): Specify part of name that interest
        include_name_filter (bool): Include or exclude the string name_filter
        recursive (bool): Find all the files recursively or not
        sort (bool): Sort the result or not

    Returns:
        List of file path, each in PosixPath format
    """
    path = coerce_to_path_and_check_exist(dir_path)
    if recursive:
        files = [f.absolute() for f in path.glob('**/*') if f.is_file()]
    else:
        files = [f.absolute() for f in path.glob('*') if f.is_file()]

    if valid_extensions is not None:
        valid_extensions = [valid_extensions] if isinstance(valid_extensions, str) else valid_extensions
        valid_extensions = ['.{}'.format(ext) if not ext.startswith('.') else ext for ext in valid_extensions]
        files = list(filter(lambda f: f.suffix in valid_extensions, files))

    if name_filter is not None:
        if include_name_filter:
            files = list(filter(lambda f: name_filter in f.name, files))
        else:
            files = list(filter(lambda f: name_filter not in f.name, files))
    return sorted(files) if sort else files


class use_seed:
    def __init__(self, seed=None):
        if seed is not None:
            assert isinstance(seed, int) and seed >= 0
        self.seed = seed

    def __enter__(self):
        if self.seed is not None:
            self.rand_state = rand_get_state()
            self.np_state = np_get_state()
            self.torch_state = torch_get_state()
            self.torch_cudnn_deterministic = torch.backends.cudnn.deterministic
            rand_seed(self.seed)
            np_seed(self.seed)
            torch_seed(self.seed)
            torch.backends.cudnn.deterministic = True
        return self

    def __exit__(self, typ, val, _traceback):
        if self.seed is not None:
            rand_set_state(self.rand_state)
            np_set_state(self.np_state)
            torch_set_state(self.torch_state)
            torch.backends.cudnn.deterministic = self.torch_cudnn_deterministic

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kw):
            seed = self.seed if self.seed is not None else kw.pop('seed', None)
            with use_seed(seed):
                return f(*args, **kw)

        return wrapper


if __name__ == '__main__':
    # TEST the function
    print((get_files_from_dir("../../datasets/TestDataset", valid_extensions=['png', 'jpg'], name_filter='seg', include_name_filter=False, recursive=True, sort=True)))

