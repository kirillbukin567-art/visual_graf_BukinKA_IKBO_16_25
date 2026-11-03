@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo === 1. Real mode: all parameters ===
py src\main.py --package nginx --repo https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64 --ascii-tree

echo.
echo === 2. Test mode: file instead of URL ===
py src\main.py --package A --repo data\graph_simple.txt --test-mode

echo.
echo === 3. Error: no parameters ===
py src\main.py

echo.
echo === 4. Error: no repository ===
py src\main.py --package nginx

echo.
echo === 5. Error: bad package name ===
py src\main.py --package "ng inx" --repo https://example.org/repo

echo.
echo === 6. Error: empty package name ===
py src\main.py --package "" --repo https://example.org/repo

echo.
echo === 7. Error: bad URL ===
py src\main.py --package nginx --repo not-a-url

echo.
echo === 8. Error: test mode, file not found ===
py src\main.py --package A --repo data\nope.txt --test-mode

echo.
echo === 9. Error: test mode, directory instead of file ===
py src\main.py --package A --repo src --test-mode

echo.
echo === 10. Error: unknown option ===
py src\main.py --package nginx --repo https://example.org/repo --bogus

echo.
echo === 11. Error: flag with a value (--ascii-tree) ===
py src\main.py --package nginx --repo https://example.org/repo --ascii-tree=yes

echo.
echo === 12. Error: parameter without a value (--package) ===
py src\main.py --package