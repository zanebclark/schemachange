import logging
import sys
from pathlib import Path
from typing import Union, Optional

from schemachange.config.DeployConfig import DeployConfig
from schemachange.config.RenderConfig import RenderConfig
from schemachange.config.parse_cli_args import parse_cli_args
from schemachange.config.utils import load_yaml_config, validate_directory


def get_yaml_config_kwargs(config_file_path: Optional[Path]) -> dict:
    # TODO: I think the configuration key for oauthconfig should be oauth-config.
    #  This looks like a bug in the current state of the repo to me

    # load YAML inputs and convert kebabs to snakes
    kwargs = {
        k.replace("-", "_").replace("oauthconfig", "oauth_config"): v
        for (k, v) in load_yaml_config(config_file_path).items()
    }

    if "verbose" in kwargs:
        kwargs["log_level"] = logging.DEBUG
        kwargs.pop("verbose")

    if "vars" in kwargs:
        kwargs["config_vars"] = kwargs.pop("vars")

    return kwargs


def get_merged_config() -> Union[DeployConfig, RenderConfig]:
    cli_kwargs = parse_cli_args(sys.argv[1:])
    cli_config_vars = cli_kwargs.pop("config_vars", None)
    if cli_config_vars is None:
        cli_config_vars = {}

    config_folder = validate_directory(path=cli_kwargs.pop("config_folder", "."))
    config_file_path = Path(config_folder) / "schemachange-config.yml"

    yaml_kwargs = get_yaml_config_kwargs(
        config_file_path=config_file_path,
    )
    yaml_config_vars = yaml_kwargs.pop("config_vars", None)
    if yaml_config_vars is None:
        yaml_config_vars = {}

    config_vars = {
        **yaml_config_vars,
        **cli_config_vars,
    }

    # override the YAML config with the CLI configuration
    kwargs = {
        "config_file_path": config_file_path,
        "config_vars": config_vars,
        **{k: v for k, v in yaml_kwargs.items() if v is not None},
        **{k: v for k, v in cli_kwargs.items() if v is not None},
    }

    if cli_kwargs["subcommand"] == "deploy":
        return DeployConfig.factory(**kwargs)
    elif cli_kwargs["subcommand"] == "render":
        return RenderConfig.factory(**kwargs)
    else:
        raise Exception(f"unhandled subcommand: {cli_kwargs['subcommand'] }")
