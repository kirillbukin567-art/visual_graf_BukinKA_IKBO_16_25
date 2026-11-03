@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set REPO=https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64

echo === 1. Test mode: diamond, no cycles ===
py src\main.py --package A --repo data\graph_simple.txt --test-mode
echo === 2. Test mode: package without dependencies ===
py src\main.py --package D --repo data\graph_simple.txt --test-mode
echo === 3. Test mode: cycle A - B - C - A ===
py src\main.py --package A --repo data\graph_cycle.txt --test-mode
echo === 4. Test mode: two cycles (B-D and self-loop E) ===
py src\main.py --package A --repo data\graph_complex.txt --test-mode
echo === 5. Test mode: package depends only on itself ===
py src\main.py --package E --repo data\graph_complex.txt --test-mode
echo === 6. Error: package not in test repository ===
py src\main.py --package Z --repo data\graph_simple.txt --test-mode
echo === 7. Error: invalid test repository file ===
py src\main.py --package A --repo data\graph_bad.txt --test-mode
echo === 8. Real repository: curl ===
py src\main.py --package curl --repo %REPO%
echo === 9. Real repository: bash ===
py src\main.py --package bash --repo %REPO%
echo === 10. Error: package not in repository ===
py src\main.py --package no-such-package --repo %REPO%
echo === 11. Error: repository path does not exist (404) ===
py src\main.py --package curl --repo https://dl-cdn.alpinelinux.org/alpine/v3.20/main/nope
echo === 12. Error: host is unreachable ===
py src\main.py --package curl --repo https://no-such-host.invalid/alpine