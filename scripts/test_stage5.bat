@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set REPO=https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64

echo === 1. ASCII tree: diamond ===
py src\main.py --package A --repo data\graph_simple.txt --test-mode --ascii-tree
echo === 2. ASCII tree: cycle ===
py src\main.py --package A --repo data\graph_cycle.txt --test-mode --ascii-tree
echo === 3. ASCII tree: two cycles, shared subtree ===
py src\main.py --package A --repo data\graph_complex.txt --test-mode --ascii-tree
echo === 4. ASCII tree: reverse dependencies ===
py src\main.py --package D --repo data\graph_complex.txt --test-mode --ascii-tree --reverse
echo === 5. Diagram: test repository with cycles ===
py src\main.py --package A --repo data\graph_complex.txt --test-mode --visualize
echo === 6. Real package 1: curl ===
py src\main.py --package curl --repo %REPO% --ascii-tree --visualize
echo === 7. Real package 2: bash ===
py src\main.py --package bash --repo %REPO% --ascii-tree --visualize
echo === 8. Real package 3: boost1.82-libs (many cycles) ===
py src\main.py --package boost1.82-libs --repo %REPO% --ascii-tree --visualize
echo === 9. Error: --output-dir is a file ===
py src\main.py --package A --repo data\graph_simple.txt --test-mode --visualize --output-dir README.md
echo === 10. Error: empty --output-dir ===
py src\main.py --package A --repo data\graph_simple.txt --test-mode --visualize --output-dir ""