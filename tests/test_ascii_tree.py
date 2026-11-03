"""Тесты построения ASCII-дерева зависимостей."""

import unittest

from ascii_tree import ascii_tree

DEPTH = 3000


class AsciiTreeTest(unittest.TestCase):
    """Проверки функции ascii_tree."""

    def test_no_dependencies(self):
        """Пакет без зависимостей даёт одну строку."""
        self.assertEqual(ascii_tree({"A": []}, "A"), ["A"])

    def test_unknown_start(self):
        """Пакет, которого нет в графе, даёт одну строку."""
        self.assertEqual(ascii_tree({}, "X"), ["X"])

    def test_chain(self):
        """Цепочка рисуется с отступами."""
        graph = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(
            ascii_tree(graph, "A"),
            ["A", "└── B", "    └── C"],
        )

    def test_branches_use_pipe(self):
        """Не последняя ветка рисуется с вертикальной чертой."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        self.assertEqual(
            ascii_tree(graph, "A"),
            ["A", "├── B", "│   └── D", "└── C"],
        )

    def test_shared_leaf_is_repeated_without_note(self):
        """Общий пакет без зависимостей повторяется без пометки."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        lines = ascii_tree(graph, "A")
        self.assertEqual(lines.count("│   └── D"), 1)
        self.assertIn("    └── D", lines)
        self.assertFalse(any("(см. выше)" in line for line in lines))

    def test_shared_subtree_is_marked(self):
        """Повторный пакет с зависимостями не раскрывается заново."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"],
                 "D": ["E"], "E": []}
        self.assertEqual(ascii_tree(graph, "A"), [
            "A",
            "├── B",
            "│   └── D",
            "│       └── E",
            "└── C",
            "    └── D (см. выше)",
        ])

    def test_cycle_is_marked(self):
        """Возврат на пакет текущего пути помечается как цикл."""
        graph = {"A": ["B"], "B": ["A"]}
        self.assertEqual(
            ascii_tree(graph, "A"),
            ["A", "└── B", "    └── A (цикл)"],
        )

    def test_self_loop(self):
        """Самозависимость помечается как цикл."""
        self.assertEqual(
            ascii_tree({"A": ["A"]}, "A"), ["A", "└── A (цикл)"]
        )

    def test_deep_chain_without_recursion(self):
        """Очень глубокое дерево не вызывает переполнения стека."""
        graph = {str(i): [str(i + 1)] for i in range(DEPTH)}
        graph[str(DEPTH)] = []
        self.assertEqual(len(ascii_tree(graph, "0")), DEPTH + 1)

    def test_graph_is_not_changed(self):
        """Построение дерева не меняет граф."""
        graph = {"A": ["B"], "B": []}
        ascii_tree(graph, "A")
        self.assertEqual(graph, {"A": ["B"], "B": []})


if __name__ == "__main__":
    unittest.main()