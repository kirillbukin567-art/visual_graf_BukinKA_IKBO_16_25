@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set REPO=https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64

echo === 1. Parameter errors: no parameters ===
py src\main.py
echo === 2. No --repo ===
py src\main.py --package curl
echo === 3. No --package ===
py src\main.py --repo %REPO%
echo === 4. Empty package name ===
py src\main.py --package "" --repo %REPO%
echo === 5. Invalid package name ===
py src\main.py --package "bad name!" --repo %REPO%
echo === 6. Invalid URL scheme ===
py src\main.py --package curl --repo ftp://x
echo === 7. Empty --repo ===
py src\main.py --package curl --repo ""
echo === 8. Test mode: file not found ===
py src\main.py --package A --repo data\nope.txt --test-mode
echo === 9. Test mode: directory instead of file ===
py src\main.py --package A --repo data --test-mode
echo === 10. Unknown option ===
py src\main.py --foo
echo === 11. Option without value ===
py src\main.py --package