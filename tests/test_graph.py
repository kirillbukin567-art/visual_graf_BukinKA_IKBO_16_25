"""Тесты обхода графа в глубину без рекурсии."""

import unittest

from graph import reverse_graph, traverse

DEPTH = 3000


class TraverseTest(unittest.TestCase):
    """Проверки функции traverse."""

    def test_chain(self):
        """Цепочка обходится по порядку, циклов нет."""
        graph = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(traverse(graph, "A"), (["A", "B", "C"], []))

    def test_diamond(self):
        """Общая зависимость посещается один раз."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        order, cycles = traverse(graph, "A")
        self.assertEqual(order, ["A", "B", "D", "C"])
        self.assertEqual(cycles, [])

    def test_no_dependencies(self):
        """Пакет без зависимостей даёт только себя."""
        self.assertEqual(traverse({"A": []}, "A"), (["A"], []))

    def test_unknown_start(self):
        """Пакет, которого нет в графе, считается пакетом без зависимостей."""
        self.assertEqual(traverse({}, "X"), (["X"], []))

    def test_cycle_through_start(self):
        """Цикл через стартовый пакет найден и обход завершился."""
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        order, cycles = traverse(graph, "A")
        self.assertEqual(order, ["A", "B", "C"])
        self.assertEqual(cycles, [["A", "B", "C", "A"]])

    def test_self_loop(self):
        """Зависимость пакета от самого себя — это цикл."""
        self.assertEqual(traverse({"A": ["A"]}, "A"), (["A"], [["A", "A"]]))

    def test_cycle_not_through_start(self):
        """Цикл, до которого дошли от стартового пакета."""
        graph = {"A": ["B"], "B": ["C"], "C": ["B"]}
        order, cycles = traverse(graph, "A")
        self.assertEqual(order, ["A", "B", "C"])
        self.assertEqual(cycles, [["B", "C", "B"]])

    def test_two_cycles(self):
        """Несколько циклов находятся все."""
        graph = {"A": ["B", "C"], "B": ["A"], "C": ["A"]}
        _, cycles = traverse(graph, "A")
        self.assertEqual(cycles, [["A", "B", "A"], ["A", "C", "A"]])

    def test_only_reachable(self):
        """Недостижимые от старта пакеты не обходятся."""
        graph = {"A": ["B"], "B": [], "X": ["A"]}
        self.assertEqual(traverse(graph, "A")[0], ["A", "B"])

    def test_deep_chain_without_recursion(self):
        """Очень длинная цепочка не вызывает переполнение стека."""
        graph = {str(i): [str(i + 1)] for i in range(DEPTH)}
        graph[str(DEPTH)] = []
        order, cycles = traverse(graph, "0")
        self.assertEqual(len(order), DEPTH + 1)
        self.assertEqual(cycles, [])

    def test_graph_is_not_changed(self):
        """Обход не меняет исходный граф."""
        graph = {"A": ["B"], "B": ["A"]}
        traverse(graph, "A")
        self.assertEqual(graph, {"A": ["B"], "B": ["A"]})


class ReverseGraphTest(unittest.TestCase):
    """Проверки функции reverse_graph."""

    def test_edges_are_reversed(self):
        """Рёбра разворачиваются, порядок как в исходном графе."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        self.assertEqual(
            reverse_graph(graph),
            {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]},
        )

    def test_empty_graph(self):
        """Пустой граф остаётся пустым."""
        self.assertEqual(reverse_graph({}), {})

    def test_node_only_in_dependencies(self):
        """Пакет, которого нет среди ключей, всё равно попадает в граф."""
        self.assertEqual(reverse_graph({"A": ["B"]}), {"A": [], "B": ["A"]})

    def test_self_loop_and_cycle_are_kept(self):
        """Самозависимость и цикл остаются после разворота."""
        self.assertEqual(reverse_graph({"A": ["A"]}), {"A": ["A"]})
        graph = {"A": ["B"], "B": ["A"]}
        self.assertEqual(reverse_graph(graph), {"A": ["B"], "B": ["A"]})

    def test_source_is_not_changed(self):
        """Исходный граф не меняется."""
        graph = {"A": ["B"], "B": []}
        reverse_graph(graph)
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_find_dependents_with_traverse(self):
        """Обход обратного графа находит все пакеты, зависящие от D."""
        graph = {"A": ["B"], "B": ["C"], "C": ["D"], "D": [], "X": []}
        order, cycles = traverse(reverse_graph(graph), "D")
        self.assertEqual(order, ["D", "C", "B", "A"])
        self.assertEqual(cycles, [])


if __name__ == "__main__":
    unittest.main()