#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This file contains various convenience data structures and functions, in
particular such that operate on nested dictionaries. This file also provides a
Configuration class, which can read nested configs from ini files.
"""

import copy
import argparse
import configparser
import ast


# NOTE: the functions and classes below were taken from amira_perception. Make
#       sure to keep in sync as long as we don't have a core library that is
#       restricted to such functionality
#
# NOTE: We do not use the logging classes in here


def flatten(lst):
    """Flatten a nested list lst"""
    return [i for subl in lst for i in subl]


def strbool(s: str):
    """Specify all strings we accept as boolean, raise error if not valid"""
    if s.lower() in ['true', 't', '1', 'yes', 'y']:
        return True
    elif s.lower() in ['false', 'f', '0', 'no', 'n']:
        return False
    else:
        raise ValueError(f"Boolean expected, but reiceived '{s}'")


def dict_put_nested(d, key, value, type=dict):
    """Put a (potentially nested) key to a dict-like.

    A nested key is of the format 'a.b.c', which will generated a dict of type
    `type` with three levels:

        >>> d = {}
        >>> dict_put_nested(d, 'a.b.c.', 1)
        >>> print(d)
        {'a': {'b': {'c': 1}}}

    """
    if '.' in key:
        k, rest = key.split('.', 1)
        if k not in d:
            d[k] = type()
        dict_put_nested(d[k], rest, value, type)
    else:
        d[key] = value

    return d


def dict_get_nested(d, key):
    """Get a (potentially nested) key from a dict-like."""
    if '.' in key:
        key, rest = key.split('.', 1)
        if key not in d:
            raise KeyError(key)
        return dict_get_nested(d[key], rest)
    else:
        if key not in d:
            raise KeyError(key)
        return d[key]


def dict_pop_nested(d, key):
    """Get a (potentially nested) key from a dict-like."""
    if '.' in key:
        key, rest = key.split('.', 1)
        if key not in d:
            raise KeyError(key)
        return dict_pop_nested(d[key], rest)
    else:
        if key not in d:
            raise KeyError(key)
        return d.pop(key)


def dict_to_cfg(d, prefix=None, length=0):
    s = ''
    n = 0
    ds = []

    for k in d:
        if isinstance(d[k], (dict, DynamicStruct)):
            ds.append((k, d[k]))
        elif isinstance(d[k], Configuration):
            ds.append((k, d[k]._dict))
        else:
            if (n == 0) and (prefix is not None):
                s += f'[{prefix}]\n'
            if n > 0:
                s += '\n'
            if isinstance(d[k], list):
                t = ''
                if len(d[k]) > 0:
                    t += f"{d[k][0]}"
                    for v in range(1, len(d[k])):
                        t += f", {d[k][v]}"
                s += f"{k} = {t}"
            else:
                s += f"{k} = {d[k]}"
            n += 1

    for d in ds:
        pre = d[0] if (prefix is None or length == 0) else prefix + '.' + d[0]
        s_tmp = dict_to_cfg(d[1], pre, length + 1)
        if (not s == '') and not (s_tmp == ''):
            s += '\n\n'
        s += s_tmp

    return s


class DynamicStruct:
    r"""This is a thin wrapper around dict to avoid typing d['foo'], but d.foo.

    Note that accessing attributes without setting them before will lead to a
    KeyError. Example:

        >>> d = DynamicStruct()
        >>> d.foo = 123
        >>> print(d.foo)          # this is fine, foo was set previously
        >>> print(d.bar)          # this throws a KeyError

    It is also possible to initialize a DynamicStruct from a dictionary. During
    initialization, a shallow copy of the passed in dict will be made to avoid
    side effects on the call site.

        >>> d = {'a': 1, 'b': 2}
        >>> dd = DynamicStruct(d)
        >>> print(dd.a, dd.b)     # this works fine
        >>> dd.c = 3              # this only affects dd
        >>> print(d)              # prints {'a': 1, 'b': 2}

    During construction, the behavior can be changed by setting the
    deep-argument to true if a deep copy of the passed-in dictionary is
    required.

    It is also possible to create nested dynamic structs:

        >>> d = DynamicStruct()
        >>> d['a.b.c'] = 123

    Afterwards, nested values can be accessed using attributes:

        >>> print(d.a.b.c)
        ... 123

    Note, however, that initialization via attributes and not via item
    assignment will yield a KeyError, if the nested structure was not create
    previously.

        >>> d.m.n.o = 7
        ... KeyError: 'n'

    """

    def __init__(self, d=None, deep=False):
        super(DynamicStruct, self).__init__()
        if not d:
            self._dict = dict()
        else:
            if not isinstance(d, dict):
                raise TypeError("Argument is not of type dict")

            if deep:
                self._dict = copy.deepcopy(d)
            else:
                self._dict = d.copy()

    def __setattr__(self, key, val):
        if key in ['_dict']:
            super(DynamicStruct, self).__setattr__(key, val)
        else:
            dict_put_nested(self._dict, key, val, type=DynamicStruct)

    def __getattr__(self, key):
        if key in ['_dict']:
            super(DynamicStruct, self).__getattr__(key)
        elif key == '_items':
            return self._dict.items
        else:
            return dict_get_nested(self._dict, key)

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, val):
        self.__setattr__(key, val)

    def __len__(self):
        return len(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        yield from self._dict

    def __repr__(self):
        return self._dict.__repr__()


class Configuration():
    """A generic configuration class.

    This class can be used to store configuration parameters. It supports
    parsing a configuration file and also update arguments from command line
    arguments. In addition, it supports nested key qualifiers.

    Note that only params that were added via `add_param` will be used/listed
    when using `parse_args`. Any additional options will not be parsed in that
    way. Also, parameters that are set in a configuration file, but not
    specified also via `add_param` will not be modified by command line argument
    parsing.

    Example:

        >>> c = Configuration()
        >>> c.add_param('section.param', True, 'Enable parameter')
        >>> c.add_param('another.nested.section.param', 1234, 'Some integer')
        >>> c['another.nested.section.param_without_argparse_support'] = 4321
        >>> c.parse_file('/path/to/file.cfg')
        >>> c.parse_args()

    It is also possible to nest configurations.

        >>> c = Configuration()
        >>> c.nested = Configuration('nested-name')
        >>> c.nested.value = 123

    Note that in the example above, the section-name will be 'nested' and not 'nested-name'!

        >>> print(c.to_cfg())
        ... [nested]
        ... value = 123

    When not specifying a name of a configuration and using `to_cfg()`, global
    parameters will be put into the 'default' namespace:

        >>> c = Configuration()
        >>> c.value = 123
        >>> print(c.to_cfg())
        ... [default]
        ... value = 123

    Be careful when using a named configuration, nested configurations, and
    values on the top level.

    1) When using `parse_file`, sections which have the same name as the
       configuration and everything in a section with name `default` will become a
       global parameter. Anything nested will become a nested un-named
       configuration.

    2) Adding nested sections with the same name as the configuration can lead to
       ill-formed configuration files when using `to_cfg()`.

        >>> c = Configuration('test')
        >>> c.foo = 123
        >>> c.parse_file('test.cfg') # will move things in [default] or [test] into global namespace
        >>> c['test.bar'] = 321
        >>> print(c.to_cfg())
        ... [test]
        ... foo = 123
        ... [test]
        ... bar = 321

        At the moment, Configuration does not detect these kinds of situations.
        The best solution is to use named configurations only for bottom level
        configurations, or entirely flat configurations.

    The Configuration allows to have fields that might be a list or a regular
    string. This is particularly useful when specifying multiple paths in one variable:

        >>> c = Configuration()
        >>> c.add_param("paths", "default_path", "some help", special='maybe_list')

    When the configuration encouters a string and the special flag is set to
    'maybe_list', it will try to split the string at commas and produce a list.
    If this succeeds, i.e. the length of the split is > 1, then a list with the
    elements will be stored.

    It is also possible to directly tell the configuration to expect a list:

        >>> c = Configuration()
        >>> c.add_param('list_of_paths', ['one', 'two'], 'A List of paths')

    When calling `to_cfg()`, this will be properly mapped to

        >>> list_of_paths = one, two

    """

    def __init__(self, name=None, parent=None):
        # name and parent of the configuration
        self._name = name
        self._parent = parent

        # dictionaries to contain data
        self._dict = {}
        self._typeinfo = {}
        self._special = {}
        self._help = {}

        # config and argument parsers
        self._cfgparse = configparser.ConfigParser()
        self._cfgparse.optionxform = str
        self._rebuild_argparser()

    def add_param(self, name: str, default, help: str, special: str = None):
        """Add a 'known' parameter to a Configuration.

        A known parameter will be presented as command line argument. Also, type
        casting will be performed only for known params during file parsing,
        because it is not possible to infer the type simply by reading the file.

        Example:

            >>> config = Configuration()
            >>> config.add_param('data.dataset_path', '$AMIRA_DATASETS/RenderedObjects/LetterB-100k', 'Path to dataset')
            >>> config.add_param('data.backgrounds_path', '$AMIRA_DATASETS/OpenImagesV4',
                'Path to background image dataset')
            >>> config.add_param('data.output_path', '$HDD/weights/dope-letterb.pth',
                'Filename to store final weights to')
            >>> config.add_param('training.network_type', 'dope', 'Network type to train')
            >>> config.add_param('training.epochs', 4, 'Number of epochs to train')
            >>> config.add_param('training.batch_size', 2, 'Batch size used during training')
            >>> config.add_param('logging.enabled', True, 'Enable/disable logging')
            >>> config.add_param('logging.path', '$HDD/tensorboard_log', 'Path to store tensorboard log')
            >>> config.parse_file('test.cfg')
            >>> config.parse_args()

        When calling `parse_args()` in the last line, all parameters that were
        specified will be recognized when presented on the command-line in the
        format `--name`, e.g. `python run-script --logging.path /some/path`.
        """

        # distinguish between flat and nested params
        if '.' in name:
            # recursive creation of subconfigurations
            subcfg_name, rest = name.split('.', 1)
            if (subcfg_name in self._dict):
                if not (self._typeinfo[subcfg_name] == Configuration):
                    print("WW: Possibly malformed configuration detected.")
            else:
                self._dict[subcfg_name] = Configuration(name=subcfg_name, parent=self)
                self._typeinfo[subcfg_name] = Configuration
                self._special[subcfg_name] = ''
                self._help[subcfg_name] = 'Sub-Configuration'

            self._dict[subcfg_name].add_param(rest, default, help, special)

        elif isinstance(default, Configuration):
            # this is a sub-configuration
            self._add_subconfig(name, default)

        else:
            # regular parameter
            self._dict[name] = default
            self._typeinfo[name] = type(default)
            self._special[name] = special
            self._help[name] = help

            # check if we need to handle a list and update the type info to
            # address the element-type. knowledge about having a list (or
            # maybe_list) will be stored in _special
            if isinstance(default, list):
                self._typeinfo[name] = str if len(default) == 0 else type(default[0])
                if not (self._special[name] == 'maybe_list'):
                    self._special[name] = 'list'

            # totally excessive, but this way it's fully automated
            self._add_argparse_argument(self._argparse_prefix, name)

    def _get_parent_prefix(self):
        # get parent prefix
        prefix = ''
        parent = self._parent
        while parent is not None:
            if parent._name is None or parent._name == '':
                break
            prefix = parent._name + '.' + prefix
            parent = parent._parent
        return prefix

    def _add_argparse_argument(self, prefix, k):

        # it is, so build the argument structure
        argname = '--' + prefix + k
        target_type = self._typeinfo[k]
        if target_type == bool:
            self._argparse.add_argument(argname, type=strbool, help=self._help[k])
        else:
            self._argparse.add_argument(argname, type=target_type, help=self._help[k])

    def _rebuild_argparser(self):
        """rebuild the argparser with all sub-configurations, private interface"""

        self._argparse = argparse.ArgumentParser(add_help=False)

        # determine prefix
        if (self._name is None or self._name == '') and (self._parent is not None):
            RuntimeError('Configuration error: _name is None or empty, but _parent is set')

        # compute the local prefix
        prefix = self._get_parent_prefix()
        if (self._name is not None) and not (self._name == ''):
            prefix = prefix + self._name + '.'

        # store the prefix, required during parsing
        self._argparse_prefix = prefix

        for k in self._dict:
            # recursive call to sub-configurations
            if type(self._dict[k]) == Configuration:
                self[k]._rebuild_argparser()
            else:
                # determine if this is a known argument or not
                if not (k in self._typeinfo):
                    continue

                # call to add the item to the argument parser
                self._add_argparse_argument(prefix, k)

    def parse_file(self, filename, only_section: str = ''):
        """Parse a configuration file.

        This properly handles nested sections. For instance, a section [a.b.c]
        will be mapped to a nested configuration.

        Args:
            filename(str): name of file to parse
            only_section(str, default=''): only parse the specified section
        """
        self._cfgparse.read(filename)

        # extract all full keys from the configuration and store their values
        for section in self._cfgparse.sections():
            for item in self._cfgparse[section]:
                # by default, prefix is the section name
                prefix = section + '.'

                # fix section name if default section and we have a
                # configuration name
                if section == 'default':
                    if self._name is not None:
                        prefix = self._name + '.'
                    else:
                        prefix = ''

                # build key, and ignore keys that are not contained in
                # only_section (if set)
                key = prefix + item
                if (only_section != '') and not (key.startswith(only_section)):
                    continue

                # set key, type cercion happens within __setitem__
                self[key] = self._cfgparse[section][item]

    def _parse_args(self, only_section: str, argv=None):
        # extract all known arguments for the local configuration
        args, args1 = self._argparse.parse_known_args(argv)

        for k in args.__dict__:
            if args.__dict__[k] is not None:
                # check if we have to restrict parsing
                if (only_section != '') and not (k.startswith(only_section)):
                    continue

                # remove any argparse prefix from the key
                local_k = k[len(self._argparse_prefix):]

                # special treatment for booleans is handled by setting up
                # strbool in add_param, and type coercion is performed in
                # __setitem__
                self._dict[local_k] = args.__dict__[k]

        # walk all subconfigurations and let them parse arguments
        for k in self._dict:
            if isinstance(self._dict[k], Configuration):
                self._dict[k]._parse_args(only_section, argv)

    def parse_args(self, only_section: str = '', argv=None):
        """Parse command line arguments and write to the configuration.

        The function uses `argparse.parse_known_args` to parse arguments.
        Thereby, it is possible to use it in a context where an additional
        parser needs to extract additional command line arguments.

        Args:
            only_section(str, default=''): Only parse a specificic section (may
                contain nested sub-section in dot-format).
        """
        # rebuild argparser to include possible sub-configurations
        # self._rebuild_argparser()
        self._parse_args(only_section, argv)

    def get_argparsers(self):
        """Return a list of all argparsers in the configuration tree."""
        argp_list = []
        argp_list.append(self._argparse)
        for k in self._dict:
            if isinstance(self._dict[k], Configuration):
                # recursive call into sub-configuration
                argp_list += self._dict[k].get_argparsers()
        return argp_list

    def __getattr__(self, key):
        if key in [
                '_dict', '_name', '_parent', '_argparse', '_argparse_prefix', '_cfgparse', '_typeinfo', '_special',
                '_help'
        ]:
            return super(Configuration, self).__getattr__(key)
        else:
            return self._dict[key]

    def __setattr__(self, key, value):
        if key in [
                '_dict', '_name', '_parent', '_argparse', '_argparse_prefix', '_cfgparse', '_typeinfo', '_special',
                '_help'
        ]:
            super(Configuration, self).__setattr__(key, value)
        else:
            self[key] = value

    def __len__(self):
        return len(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        yield from self._dict

    def _set_name(self, name: str):
        self._name = name

    def _set_parent(self, parent):
        self._parent = parent
        self._rebuild_argparser()

    def _add_subconfig(self, key, config):
        """Add a subconfiguration.

        This works by setting the configurations name to the (potentially)
        nested key, and setting the sub-configurations parent to this
        configuration.
        """

        # TODO: What if this sub-configuration is already there, shall we
        # overwrite it or do some left- or right-merge?
        # if key in self._dict:
        #     logger.warning("Implement merge of existing config?")

        # simply copy the configuration over
        self._dict[key] = config

        # update the sub-configuration's meta-data
        self._dict[key]._set_name(key)
        self._dict[key]._set_parent(self)

    def _coerce_type(self, key, value):
        """Coerce the type of a value.

        The value will be turned into the type that was specified during
        add_param. If the value is a list, then the contained elements will be
        coerced.

        Args:
            key (str): configuration-key similar to dict
            value (str): the value that was passed in the configuration or on the command line

        Returns:
            Coerced value
        """

        def __coerce(v, T):
            """Private helper to coerce standard and special types"""
            if T == bool:
                return strbool(v)
            else:
                return T(v)

        _value = value
        if key not in self._typeinfo:
            return _value

        # specific type coercion
        if (self._typeinfo[key] == bool) and not (self._special[key] in ['list', 'maybe_list']):
            if isinstance(value, bool):
                _value = value
            else:
                _value = strbool(value)
        # handle lists with forced type coercion
        elif self._special[key] == 'list':
            if isinstance(value, list):
                _value = [__coerce(v, self._typeinfo[key]) for v in value]
            else:
                vs = [v.strip() for v in value.split(',')]
                vs = [__coerce(v, self._typeinfo[key]) for v in vs]
                _value = vs
        # coerce to list if there is a list in the config, otherwise coerce to
        # type. In any case, force type coercion for all values in a possible
        # list to handle [int], [float], etc.
        elif (self._special[key] == 'maybe_list'):
            if isinstance(value, list):
                # force type coercion
                _value = [__coerce(v, self._typeinfo[key]) for v in value]
            else:
                vs = value.split(',')
                if len(vs) > 1:
                    vs = [v.strip() for v in vs]
                    vs = [__coerce(v, self._typeinfo[key]) for v in vs]
                    _value = vs
                else:
                    _value = self._typeinfo[key](vs[0])
        # handle dictionaries
        elif (self._typeinfo[key] == dict):
            if isinstance(value, dict):
                _value = value
            else:
                _value = self._typeinfo[key](ast.literal_eval(value))
        else:
            _value = self._typeinfo[key](value)

        return _value

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        """Set a specific value or sub-configuration"""
        if isinstance(value, Configuration):
            self._add_subconfig(key, value)
        else:
            # if we are in dotted notation, descend into the keys and generate
            # sub-configurations on the fly. Because of type coercion, we cannot
            # easily use dict_put_nested here
            if '.' in key:
                sub, rest = key.split('.', 1)
                if sub not in self._dict:
                    self._dict[sub] = Configuration('sub')
                else:
                    if not isinstance(self._dict[sub], (Configuration)):
                        print("WW: Malformed configuration detected")
                self._dict[sub][rest] = value
            else:
                self._dict[key] = self._coerce_type(key, value)

    def __repr__(self):
        """use the dict for representation"""
        return self._dict.__repr__()

    def to_cfg(self):
        """Pretty-print the configuration similar to configuration files"""
        return dict_to_cfg(self._dict, self._name if self._name is not None else 'default')

    def get(self, key, default=None):
        """Overload default dict.get() for handling KeyError"""
        try:
            return dict_get_nested(self, key)
        except KeyError:
            return default

    def pop(self, key, *args):
        """Overload default dict.pop()
        Args:
            *default value in case key is missing
        """
        if '.' in key:
            key, rest = key.split('.', 1)
            if key not in self:
                if args:
                    return args[0]
                raise KeyError(key)
            return self[key].pop(rest, *args)
        else:
            if key not in self:
                if args:
                    return args[0]
                raise KeyError(key)
            return self._dict.pop(key)

    def right_merge(self, right):
        """Merge two configurations using a right-merge.

        Right merge will overwrite values on the left (self) with values from
        the configuration on the right. It will also add all values that are in
        right, but not in left.

        Note that this function is _not_ side effect free.

        Args:
            self (Configuration): Target configuration
            right (Configuration): Source configuration

        Returns:
            The merged configuration
        """
        for i, k in enumerate(right):
            # descend into sub-configuration if necessary
            if isinstance(right[k], Configuration):
                if (k in self) and isinstance(self[k], Configuration):
                    self[k].right_merge(right[k])
                else:
                    self[k] = right[k]
            else:
                self[k] = right[k]
        return self


class Filter:
    """Discard all elements of a sample except some specified ones."""

    def __init__(self, keys: list, dict_type=dict):
        """Initialize a DiscardExcept.

        The keys must be either direct accessor to a sample dictionary, or if the sample
        is a nested dict of the form 'a.b.c'.

        Args:
            keys (list): list of keys to keep
            dict_type (type): dictionary type to create when filtering (default: dict)
        """
        self.keys = keys
        self.dict_type = dict_type

    def __call__(self, sample):
        new_sample = self.dict_type()
        for key in self.keys:
            dict_put_nested(new_sample, key, dict_get_nested(sample, key), type=self.dict_type)
        return new_sample


def filter_state_keys(data, retain_keys: list = None):
    """Filter state dict keys from list"""
    if retain_keys is None:
        retain_keys = []
    if len(retain_keys) != 0:
        filter_results = Filter(retain_keys)
        return filter_results(data)
    return data
