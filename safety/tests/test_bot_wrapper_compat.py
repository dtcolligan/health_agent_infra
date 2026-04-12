from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest import mock


class BotWrapperCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._orig_modules = {}
        for name, module in {
            "dotenv": cls._fake_dotenv_module(),
            "anthropic": cls._fake_anthropic_module(),
        }.items():
            cls._orig_modules[name] = sys.modules.get(name)
            sys.modules[name] = module

    @classmethod
    def tearDownClass(cls) -> None:
        for name, module in cls._orig_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    @staticmethod
    def _fake_dotenv_module() -> types.ModuleType:
        module = types.ModuleType("dotenv")
        module.load_dotenv = lambda *args, **kwargs: True
        return module

    @staticmethod
    def _fake_anthropic_module() -> types.ModuleType:
        module = types.ModuleType("anthropic")

        class _Anthropic:
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs

        module.Anthropic = _Anthropic
        return module

    def test_bot_wrapper_modules_import_and_expose_canonical_symbols(self) -> None:
        wrapper_to_canonical = {
            "bot.config": "merge_human_inputs.health_logger.config",
            "bot.db": "merge_human_inputs.health_logger.db",
            "bot.formatter": "merge_human_inputs.health_logger.formatter",
            "bot.parser": "merge_human_inputs.health_logger.parser",
            "bot.service": "merge_human_inputs.health_logger.service",
            "bot.main": "merge_human_inputs.health_logger.main",
        }

        for wrapper_name, canonical_name in wrapper_to_canonical.items():
            with self.subTest(wrapper=wrapper_name):
                wrapper = importlib.import_module(wrapper_name)
                canonical = importlib.import_module(canonical_name)
                self.assertEqual(wrapper.__name__, wrapper_name)
                self.assertEqual(canonical.__name__, canonical_name)

        config = importlib.import_module("bot.config")
        canonical_config = importlib.import_module("merge_human_inputs.health_logger.config")
        self.assertEqual(config.DB_PATH, canonical_config.DB_PATH)
        self.assertIs(config.get_user_date, canonical_config.get_user_date)

        db = importlib.import_module("bot.db")
        canonical_db = importlib.import_module("merge_human_inputs.health_logger.db")
        self.assertIs(db.init_db, canonical_db.init_db)
        self.assertIs(db.get_conn, canonical_db.get_conn)

        formatter = importlib.import_module("bot.formatter")
        canonical_formatter = importlib.import_module("merge_human_inputs.health_logger.formatter")
        self.assertIs(formatter.format_summary, canonical_formatter.format_summary)

        parser = importlib.import_module("bot.parser")
        canonical_parser = importlib.import_module("merge_human_inputs.health_logger.parser")
        self.assertIs(parser.parse_health_message, canonical_parser.parse_health_message)

        service = importlib.import_module("bot.service")
        canonical_service = importlib.import_module("merge_human_inputs.health_logger.service")
        self.assertIs(service.log_message, canonical_service.log_message)

        main = importlib.import_module("bot.main")
        canonical_main = importlib.import_module("merge_human_inputs.health_logger.main")
        self.assertIs(main.setup, canonical_main.setup)

    def test_bot_main_setup_remains_callable_via_wrapper(self) -> None:
        main = importlib.import_module("bot.main")
        canonical_main = importlib.import_module("merge_human_inputs.health_logger.main")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "health_log.db")
            with mock.patch.object(canonical_main, "ANTHROPIC_API_KEY", "test-key"), \
                    mock.patch.object(canonical_main, "DB_PATH", db_path), \
                    mock.patch.object(canonical_main, "init_db") as init_db:
                self.assertTrue(main.setup())
                init_db.assert_called_once_with()
                self.assertTrue(os.path.isdir(tmpdir))


if __name__ == "__main__":
    unittest.main()
