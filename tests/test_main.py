from __future__ import annotations

import logging
import os
import tempfile
import unittest.mock as mock
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent

import pytest
from schemachange.config.ChangeHistoryTable import ChangeHistoryTable

import schemachange.cli as cli

default_base_config = {
    # Shared configuration options
    "config_file_path": Path(".") / "schemachange-config.yml",
    "root_folder": Path("."),
    "modules_folder": None,
    "config_vars": {},
}

default_deploy_config = {
    **default_base_config,
    # Deploy configuration options
    "snowflake_account": None,
    "snowflake_user": None,
    "snowflake_role": None,
    "snowflake_warehouse": None,
    "snowflake_database": None,
    "snowflake_schema": None,
    "change_history_table": ChangeHistoryTable(
        table_name="CHANGE_HISTORY",
        schema_name="SCHEMACHANGE",
        database_name="METADATA",
    ),
    "create_change_history_table": False,
    "autocommit": False,
    "dry_run": False,
    "query_tag": None,
    "oauth_config": None,
}

required_args = [
    "--snowflake-account",
    "account",
    "--snowflake-user",
    "user",
    "--snowflake-warehouse",
    "warehouse",
    "--snowflake-role",
    "role",
]

required_config = {
    "snowflake_account": "account",
    "snowflake_user": "user",
    "snowflake_warehouse": "warehouse",
    "snowflake_role": "role",
}
script_path = Path(__file__).parent.parent / "demo" / "basics_demo" / "A__basic001.sql"


@pytest.mark.parametrize(
    "to_mock, cli_args, expected_config, expected_script_path",
    [
        (
            "schemachange.cli.deploy",
            ["schemachange", *required_args],
            {**default_deploy_config, **required_config},
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args],
            {**default_deploy_config, **required_config},
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", "-f", ".", *required_args],
            {**default_deploy_config, **required_config, "root_folder": Path(".")},
            None,
        ),
        (
            "schemachange.cli.deploy",
            [
                "schemachange",
                "deploy",
                *required_args,
                "--snowflake-database",
                "database",
            ],
            {
                **default_deploy_config,
                **required_config,
                "snowflake_database": "database",
            },
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--snowflake-schema", "schema"],
            {**default_deploy_config, **required_config, "snowflake_schema": "schema"},
            None,
        ),
        (
            "schemachange.cli.deploy",
            [
                "schemachange",
                "deploy",
                *required_args,
                "--change-history-table",
                "db.schema.table",
            ],
            {
                **default_deploy_config,
                **required_config,
                "change_history_table": ChangeHistoryTable(
                    database_name="db", schema_name="schema", table_name="table"
                ),
            },
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--vars", '{"var1": "val"}'],
            {
                **default_deploy_config,
                **required_config,
                "config_vars": {"var1": "val"},
            },
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--create-change-history-table"],
            {
                **default_deploy_config,
                **required_config,
                "create_change_history_table": True,
            },
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--autocommit"],
            {**default_deploy_config, **required_config, "autocommit": True},
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--verbose"],
            {**default_deploy_config, **required_config, "log_level": logging.DEBUG},
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--dry-run"],
            {**default_deploy_config, **required_config, "dry_run": True},
            None,
        ),
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--query-tag", "querytag"],
            {**default_deploy_config, **required_config, "query_tag": "querytag"},
            None,
        ),
        (
            "schemachange.cli.deploy",
            [
                "schemachange",
                "deploy",
                *required_args,
                "--oauth-config",
                '{"token-provider-url": "https//..."}',
            ],
            {
                **default_deploy_config,
                **required_config,
                "oauth_config": {"token-provider-url": "https//..."},
            },
            None,
        ),
        (
            "schemachange.cli.deploy",
            [
                "schemachange",
                "deploy",
                *required_args,
            ],
            {
                **default_deploy_config,
                **required_config,
                "log_level": 20,
            },
            None,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                str(script_path),
            ],
            {**default_base_config},
            script_path,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                "--root-folder",
                ".",
                str(script_path),
            ],
            {**default_base_config, "root_folder": Path(".")},
            script_path,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                "--vars",
                '{"var1": "val"}',
                str(script_path),
            ],
            {**default_base_config, "config_vars": {"var1": "val"}},
            script_path,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                "--verbose",
                str(script_path),
            ],
            {**default_base_config, "log_level": logging.DEBUG},
            script_path,
        ),
    ],
)
@mock.patch("schemachange.session.SnowflakeSession.snowflake.connector.connect")
def test_main_deploy_subcommand_given_arguments_make_sure_arguments_set_on_call(
    _,
    to_mock: str,
    cli_args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    with mock.patch.dict(os.environ, {"SNOWFLAKE_PASSWORD": "password"}, clear=True):
        with mock.patch("sys.argv", cli_args):
            with mock.patch(to_mock) as mock_command:
                cli.main()
                mock_command.assert_called_once()
                _, call_kwargs = mock_command.call_args
                for expected_arg, expected_value in expected_config.items():
                    actual_value = getattr(call_kwargs["config"], expected_arg)
                    if hasattr(actual_value, "table_name"):
                        assert asdict(actual_value) == asdict(expected_value)
                    else:
                        assert actual_value == expected_value
                if expected_script_path is not None:
                    assert call_kwargs["script_path"] == expected_script_path


@pytest.mark.parametrize(
    "to_mock, args,  expected_config, expected_script_path",
    [
        (
            "schemachange.cli.deploy",
            [
                "schemachange",
                "deploy",
                "--config-folder",
                "DUMMY",
            ],
            {
                **default_deploy_config,
                "snowflake_user": "user",
                "snowflake_warehouse": "warehouse",
                "snowflake_role": "role",
                "snowflake_account": "account",
            },
            None,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                str(script_path),
                "--config-folder",
                "DUMMY",
            ],
            default_base_config,
            script_path,
        ),
    ],
)
@mock.patch("schemachange.session.SnowflakeSession.snowflake.connector.connect")
def test_main_deploy_config_folder(
    _,
    to_mock: str,
    args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    with mock.patch.dict(os.environ, {"SNOWFLAKE_PASSWORD": "password"}, clear=True):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "schemachange-config.yml"), "w") as f:
                f.write(
                    dedent(
                        """
                        snowflake_account: account
                        snowflake_user: user
                        snowflake_warehouse: warehouse
                        snowflake_role: role
                        """
                    )
                )

            args[args.index("DUMMY")] = d
            expected_config["config_file_path"] = Path(d) / "schemachange-config.yml"

            with mock.patch(to_mock) as mock_command:
                with mock.patch("sys.argv", args):
                    cli.main()
                    mock_command.assert_called_once()
                    _, call_kwargs = mock_command.call_args
                    for expected_arg, expected_value in expected_config.items():
                        actual_value = getattr(call_kwargs["config"], expected_arg)
                        if hasattr(actual_value, "table_name"):
                            assert asdict(actual_value) == asdict(expected_value)
                        else:
                            assert actual_value == expected_value
                    if expected_script_path is not None:
                        assert call_kwargs["script_path"] == expected_script_path


@pytest.mark.parametrize(
    "to_mock, args, expected_config, expected_script_path",
    [
        (
            "schemachange.cli.deploy",
            ["schemachange", "deploy", *required_args, "--modules-folder", "DUMMY"],
            {**default_deploy_config, **required_config, "modules_folder": "DUMMY"},
            None,
        ),
        (
            "schemachange.cli.render",
            [
                "schemachange",
                "render",
                str(script_path),
                "--modules-folder",
                "DUMMY",
            ],
            {**default_base_config, "modules_folder": "DUMMY"},
            script_path,
        ),
    ],
)
@mock.patch("schemachange.session.SnowflakeSession.snowflake.connector.connect")
def test_main_deploy_modules_folder(
    _,
    to_mock: str,
    args: list[str],
    expected_config: dict,
    expected_script_path: Path | None,
):
    with mock.patch.dict(os.environ, {"SNOWFLAKE_PASSWORD": "password"}, clear=True):
        with tempfile.TemporaryDirectory() as d:
            args[args.index("DUMMY")] = d
            expected_config["modules_folder"] = Path(d)

            with mock.patch(to_mock) as mock_command:
                with mock.patch("sys.argv", args):
                    cli.main()
                    mock_command.assert_called_once()
                    _, call_kwargs = mock_command.call_args
                    for expected_arg, expected_value in expected_config.items():
                        actual_value = getattr(call_kwargs["config"], expected_arg)
                        if hasattr(actual_value, "table_name"):
                            assert asdict(actual_value) == asdict(expected_value)
                        else:
                            assert actual_value == expected_value
                    if expected_script_path is not None:
                        assert call_kwargs["script_path"] == expected_script_path
