import unittest
import unittest.mock as mock
import pytest
import os
import sys
import shutil
import tempfile
import gettext
import contextlib

import click
from click.testing import CliRunner

import opsdroid.__main__
import opsdroid.cli
import opsdroid.cli.version
from opsdroid.cli.start import configure_lang
from opsdroid.const import __version__
from opsdroid.core import OpsDroid
from opsdroid.helper import del_rw


class TestCLI(unittest.TestCase):
    """Test the opsdroid CLI."""

    def setUp(self):
        self._tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
        with contextlib.suppress(FileExistsError):
            os.makedirs(self._tmp_dir, mode=0o777)
        configure_lang({})

    def tearDown(self):
        with contextlib.suppress(PermissionError):
            shutil.rmtree(self._tmp_dir, onerror=del_rw)

    def test_init_runs(self):
        with mock.patch.object(opsdroid.cli, "cli") as mainfunc:
            with mock.patch.object(opsdroid.__main__, "__name__", "__main__"):
                opsdroid.__main__.init()
                self.assertTrue(mainfunc.called)

    def test_init_doesnt_run(self):
        with mock.patch.object(opsdroid.cli, "cli") as mainfunc:
            with mock.patch.object(opsdroid.__main__, "__name__", "opsdroid"):
                opsdroid.__main__.init()
                self.assertFalse(mainfunc.called)

    def test_configure_no_lang(self):
        with mock.patch.object(gettext, "translation") as translation:
            from opsdroid.cli.start import configure_lang

            configure_lang({})
            self.assertFalse(translation.return_value.install.called)

    def test_configure_lang(self):
        with mock.patch.object(gettext, "translation") as translation:
            from opsdroid.cli.utils import configure_lang

            configure_lang({"lang": "es"})
            self.assertTrue(translation.return_value.install.called)

    def test_welcome_message(self):
        config = {"welcome-message": True}
        from opsdroid.cli.utils import welcome_message

        welcome_message(config)
        self.assertLogs("_LOGGER", "info")

    def test_welcome_exception(self):
        config = {}
        from opsdroid.cli.utils import welcome_message

        response = welcome_message(config)
        self.assertIsNone(response)

    def test_check_version_27(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 2
            version_info.minor = 7
            with self.assertRaises(SystemExit):
                from opsdroid.cli.utils import check_dependencies

                check_dependencies()

    def test_check_version_34(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 4
            with self.assertRaises(SystemExit):
                from opsdroid.cli.utils import check_dependencies

                check_dependencies()

    def test_check_version_35(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 5
            with self.assertRaises(SystemExit):
                from opsdroid.cli.utils import check_dependencies

                check_dependencies()

    def test_check_version_36(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 6
            try:
                from opsdroid.cli.utils import check_dependencies

                check_dependencies()
            except SystemExit:
                self.fail("check_dependencies() exited unexpectedly!")

    def test_check_version_37(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 7
            try:
                from opsdroid.cli.start import check_dependencies

                check_dependencies()
            except SystemExit:
                self.fail("check_dependencies() exited unexpectedly!")

    def test_gen_config(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "opsdroid.core.OpsDroid.load"
        ) as opsdroid_load:
            runner = CliRunner()
            from opsdroid.cli.config import gen

            result = runner.invoke(gen, [])
            self.assertTrue(click_echo.called)
            self.assertFalse(opsdroid_load.called)
            self.assertEqual(result.exit_code, 0)

    def test_deprecated_gen_config(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "opsdroid.core.OpsDroid.load"
        ) as opsdroid_load:
            runner = CliRunner()
            with pytest.warns(DeprecationWarning, match=".*opsdroid config gen.*"):
                result = runner.invoke(opsdroid.cli.cli, ["--gen-config"])
            self.assertTrue(click_echo.called)
            self.assertFalse(opsdroid_load.called)
            self.assertEqual(result.exit_code, 0)

    def test_print_version(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "opsdroid.core.OpsDroid.load"
        ) as opsdroid_load:
            runner = CliRunner()
            from opsdroid.cli.version import version

            result = runner.invoke(version, [])
            self.assertTrue(click_echo.called)
            self.assertFalse(opsdroid_load.called)
            self.assertTrue(__version__ in click_echo.call_args[0][0])
            self.assertEqual(result.exit_code, 0)

    def test_deprecated_print_version(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "opsdroid.core.OpsDroid.load"
        ) as opsdroid_load:
            runner = CliRunner()
            with pytest.warns(DeprecationWarning, match=".*opsdroid version.*"):
                result = runner.invoke(opsdroid.cli.cli, ["--version"])
            self.assertTrue(click_echo.called)
            self.assertFalse(opsdroid_load.called)
            self.assertTrue(__version__ in click_echo.call_args[0][0])
            self.assertEqual(result.exit_code, 0)

    def test_edit_files_config(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "subprocess.run"
        ) as editor:
            runner = CliRunner()
            from opsdroid.cli.config import edit

            result = runner.invoke(edit, [], input="y")
            self.assertTrue(click_echo.called)
            self.assertTrue(editor.called)
            self.assertEqual(result.exit_code, 0)

    def test_deprecated_edit_files_config(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "subprocess.run"
        ) as editor:
            runner = CliRunner()
            with pytest.warns(DeprecationWarning, match=".*opsdroid config edit.*"):
                result = runner.invoke(opsdroid.cli.cli, ["--edit-config"], input="y")
            self.assertTrue(click_echo.called)
            self.assertTrue(editor.called)
            self.assertEqual(result.exit_code, 0)

    def test_edit_files_log(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "subprocess.run"
        ) as editor:
            runner = CliRunner()
            from opsdroid.cli.logs import logs

            result = runner.invoke(logs, [])
            self.assertTrue(click_echo.called)
            self.assertTrue(editor.called)
            self.assertEqual(result.exit_code, 0)

    def test_deprecated_edit_files_log(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "subprocess.run"
        ) as editor:
            runner = CliRunner()
            with pytest.warns(DeprecationWarning, match=".*opsdroid logs.*"):
                result = runner.invoke(opsdroid.cli.cli, ["--view-log"])
            self.assertTrue(click_echo.called)
            self.assertTrue(editor.called)
            self.assertEqual(result.exit_code, 0)

    def test_main(self):
        with pytest.warns(DeprecationWarning, match=".*opsdroid start.*"):
            runner = CliRunner()
            with mock.patch.object(OpsDroid, "run") as mock_run:
                runner.invoke(opsdroid.cli.cli, [])
                assert mock_run.called

    def test_config_validate(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "opsdroid.configuration.load_config_file"
        ) as opsdroid_load:
            runner = CliRunner()
            from opsdroid.cli.config import lint

            result = runner.invoke(lint, [])
            self.assertTrue(click_echo.called)
            self.assertFalse(opsdroid_load.called)
            self.assertEqual(result.exit_code, 0)
