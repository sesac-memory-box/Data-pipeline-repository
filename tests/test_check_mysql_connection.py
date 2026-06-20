import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_mysql_connection.py"
SPEC = importlib.util.spec_from_file_location("check_mysql_connection", SCRIPT_PATH)
check_mysql_connection = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = check_mysql_connection
SPEC.loader.exec_module(check_mysql_connection)


class CheckMySQLConnectionTest(unittest.TestCase):
    def test_missing_required_env_reports_key_names(self):
        missing = check_mysql_connection.missing_required_env(
            {
                "DB_HOST": "",
                "DB_NAME": "memorybox",
                "DB_USER": None,
                "DB_PASSWORD": "secret",
            }
        )

        self.assertEqual(missing, ["DB_HOST", "DB_USER"])

    def test_explain_access_denied_without_password_value(self):
        message = check_mysql_connection.explain_failure(Exception("Access denied for user"))

        self.assertIn("DB_USER", message)
        self.assertIn("DB_PASSWORD", message)


if __name__ == "__main__":
    unittest.main()
