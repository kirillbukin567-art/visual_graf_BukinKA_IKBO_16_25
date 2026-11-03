"""Тесты точки входа: вывод зависимостей и коды завершения."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from apk_repo import RepoError
from main import EXIT_ERROR, EXIT_OK, main

URL = "https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64"
ARGS = ["--package", "nginx", "--repo", URL]


def run_main(argv, dependencies=None, repo_error=None):
    """Запускает main с подменой чтения репозитория.

    Возвращает код завершения, текст stdout и текст stderr.
    """
    out = io.StringIO()
    err = io.StringIO()
    fake = mock.Mock(return_value=dependencies, side_effect=repo_error)
    with mock.patch("main.get_direct_dependencies", fake):
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверки функции main."""

    def test_prints_dependencies(self):
        """Прямые зависимости выводятся списком, код 0."""
        code, out, _ = run_main(ARGS, dependencies=["musl", "pcre2"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Прямые зависимости пакета nginx: 2", out)
        self.assertIn("  musl", out)
        self.assertIn("  pcre2", out)

    def test_no_dependencies(self):
        """Пакет без зависимостей: выводится ноль."""
        code, out, _ = run_main(ARGS, dependencies=[])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("nginx: 0", out)

    def test_repo_error(self):
        """Ошибка репозитория: сообщение в stderr, код 1."""
        error = RepoError("пакет 'nginx' не найден в репозитории")
        code, out, err = run_main(ARGS, repo_error=error)
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка: пакет 'nginx' не найден", err)

    def test_parameter_error(self):
        """Ошибка параметров: сообщение в stderr, код 1."""
        code, _, err = run_main([])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка:", err)

    def test_test_mode_is_not_ready(self):
        """Тестовый режим на этом этапе сообщает, что не реализован."""
        argv = ["--package", "A", "--repo", __file__, "--test-mode"]
        code, _, err = run_main(argv)
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("этапе 3", err)


if __name__ == "__main__":
    unittest.main()