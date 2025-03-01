"""Load configuration from yaml file."""

import os
import shutil
import sys
import re
import logging
import yaml

from opsdroid.const import DEFAULT_CONFIG_PATH, ENV_VAR_REGEX, EXAMPLE_CONFIG_FILE
from opsdroid.configuration.validation import validate_configuration, BASE_SCHEMA
from opsdroid.helper import update_pre_0_17_config_format


_LOGGER = logging.getLogger(__name__)


def create_default_config(config_path):
    """Create a default config file based on the example config file.

    If we can't find any configuration.yaml, we will pull the whole
    example_configuration.yaml and use this file as the configuration.

    Args:
        config_path: String containing the path to configuration.yaml
            default install location

    Returns:
        str: path to configuration.yaml default install location

    """
    _LOGGER.info("Creating %s.", config_path)
    config_dir, _ = os.path.split(config_path)
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)
    shutil.copyfile(EXAMPLE_CONFIG_FILE, config_path)
    return config_path


def get_config_path(config_paths):
    """Get the path to configuration.yaml.

    Opsdroid configuration.yaml can be located in different paths.
    With this function, we will go through all of the possible paths and
    return the correct path.

    If we don't have any configuration.yaml we will just create one using
    the example configuration file.

    Args:
        config_paths: List containing all the possible config paths.

    Returns:
        str: Path to the configuration file.

    """
    config_path = ""
    for possible_path in config_paths:
        if not os.path.isfile(possible_path):
            _LOGGER.debug(_("Config file %s not found."), possible_path)
        else:
            config_path = possible_path
            break

    if not config_path:
        _LOGGER.info(
            _("No configuration files found. Creating %s"), DEFAULT_CONFIG_PATH
        )
        config_path = create_default_config(DEFAULT_CONFIG_PATH)

    return config_path


env_var_pattern = re.compile(ENV_VAR_REGEX)


def envvar_constructor(loader, node):
    """Yaml parser for env vars."""
    value = loader.construct_scalar(node)
    [env_var] = env_var_pattern.match(value).groups()
    return os.environ[env_var]


def load_config_file(config_paths):
    """Load a yaml config file from path.

    We get a path for the configuration file and then use the yaml
    library to load this file - the configuration will be shown as a
    dict.  Here we also add constructors to our yaml loader and handle
    different exceptions that could be raised when trying to load or
    validate the file.

    Args:
        config_paths: List of paths to configuration.yaml files

    Returns:
        dict: Dict containing config fields

    """

    config_path = get_config_path(config_paths)

    yaml.SafeLoader.add_implicit_resolver("!envvar", env_var_pattern, first="$")
    yaml.SafeLoader.add_constructor("!envvar", envvar_constructor)

    try:
        with open(config_path, "r") as stream:
            _LOGGER.info(_("Loaded config from %s."), config_path)

            data = yaml.load(stream, Loader=yaml.SafeLoader)
            configuration = update_pre_0_17_config_format(data)
            validate_configuration(configuration, BASE_SCHEMA)

            return configuration

    except yaml.YAMLError as error:
        _LOGGER.critical(error)
        sys.exit(1)

    except FileNotFoundError as error:
        _LOGGER.critical(error)
        sys.exit(1)
