@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set REPO=https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64

echo === 1. Reverse: diamond, who depends on D ===
py src\main.py --package D --repo data\graph_simple.txt --test-mode --reverse
echo === 2. Reverse: nobody depends on A ===
py src\main.py --package A --repo data\graph_simple.txt --test-mode --reverse
echo === 3. Reverse: cycle A - B - C - A ===
py src\main.py --package A --repo data\graph_cycle.txt --test-mode --reverse
echo === 4. Reverse: cycle B-D in the middle of the graph ===
py src\main.py --package D --repo data\graph_complex.txt --test-mode --reverse
echo === 5. Reverse: the deepest package F ===
py src\main.py --package F --repo data\graph_complex.txt --test-mode --reverse
echo === 6. Reverse: self-loop E ===
py src\main.py --package E --repo data\graph_complex.txt --test-mode --reverse
echo === 7. Error: package not in test repository ===
py src\main.py --package Z --repo data\graph_simple.txt --test-mode --reverse
echo === 8. Real repository: who depends on libcurl ===
py src\main.py --package libcurl --repo %REPO% --reverse
echo === 9. Real repository: who depends on readline ===
py src\main.py --package readline --repo %REPO% --reverse
echo === 10. Error: package not in repository ===
py src\main.py --package no-such-package --repo %REPO% --reverse