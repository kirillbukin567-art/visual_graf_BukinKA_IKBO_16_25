"""Тесты чтения тестового репозитория (файла с графом)."""

import os
import tempfile
import unittest

from apk_repo import RepoError
from graph_file import parse_graph, read_graph_file


class ParseGraphTest(unittest.TestCase):
    """Проверки разбора текста файла."""

    def test_simple(self):
        """Строки 'A: B C' разбираются в граф."""
        graph = parse_graph("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(
            graph, {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        )

    def test_comments_and_blank_lines(self):
        """Комментарии и пустые строки пропускаются."""
        graph = parse_graph("# заголовок\n\nA: B  # комментарий\n")
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_undefined_dependency_becomes_package(self):
        """Пакет, описанный только как зависимость, есть в графе."""
        self.assertEqual(parse_graph("A: B C"), {"A": ["B", "C"],
                                                 "B": [], "C": []})

    def test_repeated_dependency_removed(self):
        """Повторы зависимостей удаляются."""
        self.assertEqual(parse_graph("A: B B")["A"], ["B"])

    def test_empty_text(self):
        """Пустой файл даёт пустой граф."""
        self.assertEqual(parse_graph(""), {})

    def test_no_colon(self):
        """Строка без двоеточия — ошибка с номером строки."""
        with self.assertRaisesRegex(RepoError, "строка 2: ожидается"):
            parse_graph("A: B\nC D\n")

    def test_lowercase_name(self):
        """Имя в нижнем регистре недопустимо."""
        with self.assertRaisesRegex(RepoError, "'b'"):
            parse_graph("A: b")

    def test_digit_in_name(self):
        """Цифры в имени недопустимы."""
        with self.assertRaisesRegex(RepoError, "'A1'"):
            parse_graph("A1: B")

    def test_empty_name(self):
        """Пустое имя пакета недопустимо."""
        with self.assertRaisesRegex(RepoError, "строка 1"):
            parse_graph(": B")

    def test_duplicate_definition(self):
        """Повторное описание пакета — ошибка."""
        with self.assertRaisesRegex(RepoError, "строка 2.*повторно"):
            parse_graph("A: B\nA: C\n")


class ReadGraphFileTest(unittest.TestCase):
    """Проверки чтения файла с диска."""

    def make_file(self, data):
        """Создаёт временный файл с данными и возвращает путь к нему."""
        handle, path = tempfile.mkstemp()
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "wb") as file:
            file.write(data)
        return path

    def test_read(self):
        """Файл читается в граф."""
        path = self.make_file("A: B\n".encode())
        self.assertEqual(read_graph_file(path), {"A": ["B"], "B": []})

    def test_bom_is_ignored(self):
        """Метка BOM (Блокнот Windows) в начале файла не мешает."""
        path = self.make_file("\ufeffA: B\n".encode("utf-8"))
        self.assertEqual(read_graph_file(path)["A"], ["B"])

    def test_missing_file(self):
        """Отсутствующий файл вызывает RepoError."""
        with self.assertRaisesRegex(RepoError, "не удалось прочитать"):
            read_graph_file("no_such_file.txt")

    def test_not_text(self):
        """Файл не в кодировке UTF-8 вызывает RepoError."""
        path = self.make_file(b"\xff\xfe\x00A")
        with self.assertRaises(RepoError):
            read_graph_file(path)


if __name__ == "__main__":
    unittest.main()