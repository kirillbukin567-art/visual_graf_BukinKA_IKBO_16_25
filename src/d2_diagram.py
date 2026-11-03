"""Диаграмма зависимостей на языке D2: текст, сохранение и показ."""

import subprocess
import webbrowser
from pathlib import Path

START_COLOR = "#ffe699"
D2_COMMAND = "d2"
RENDER_TIMEOUT = 120


class DiagramError(Exception):
    """Ошибка построения, сохранения или показа диаграммы."""


def quote(name):
    """Возвращает имя пакета в кавычках D2 (точки и двоеточия безопасны)."""
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


def edges_between(graph, nodes):
    """Возвращает рёбра (пакет, зависимость) графа между заданными узлами."""
    allowed = set(nodes)
    edges = []
    for name in nodes:
        for dependency in graph.get(name, []):
            if dependency in allowed:
                edges.append((name, dependency))
    return edges


def build_d2(start, nodes, edges):
    """Собирает текст диаграммы D2: стартовый пакет, остальные и стрелки.

    Стрелка «A -> B» означает «A зависит от B».
    """
    lines = ["direction: right", "", f"{quote(start)}: {{"]
    lines.append(f'  style.fill: "{START_COLOR}"')
    lines.append("}")
    lines.extend(quote(name) for name in nodes if name != start)
    lines.extend(f"{quote(a)} -> {quote(b)}" for a, b in edges)
    return "\n".join(lines) + "\n"


def save_text(text, path):
    """Сохраняет текст диаграммы в файл, создавая каталог при нужде."""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    except OSError as error:
        raise DiagramError(f"не удалось сохранить '{path}': {error}") from error


def render_svg(d2_path, svg_path):
    """Рисует SVG-изображение из файла D2 программой d2."""
    command = [D2_COMMAND, str(d2_path), str(svg_path)]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=RENDER_TIMEOUT,
        )
    except FileNotFoundError as error:
        raise DiagramError(
            "программа d2 не найдена (Windows: winget install "
            "terrastruct.d2, затем откройте новое окно терминала)"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise DiagramError("d2 не уложилась во время ожидания") from error
    if result.returncode:
        raise DiagramError(f"d2 завершилась с ошибкой: {result.stderr.strip()}")


def show_image(path):
    """Открывает изображение в программе просмотра по умолчанию (браузер)."""
    if not webbrowser.open(Path(path).resolve().as_uri()):
        raise DiagramError(f"не удалось открыть изображение '{path}'")


def draw(text, directory, name):
    """Сохраняет D2-текст, рисует SVG и показывает его на экране.

    Возвращает пути к файлам .d2 и .svg.
    """
    d2_path = Path(directory) / f"{name}.d2"
    svg_path = Path(directory) / f"{name}.svg"
    save_text(text, d2_path)
    render_svg(d2_path, svg_path)
    show_image(svg_path)
    return d2_path, svg_path