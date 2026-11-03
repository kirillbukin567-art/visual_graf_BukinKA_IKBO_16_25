@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set REPO=https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64

echo === 1. Direct dependencies of curl ===
py src\main.py --package curl --repo %REPO%
echo === 2. Direct dependencies of bash ===
py src\main.py --package bash --repo %REPO%
echo === 3. Direct dependencies of busybox ===
py src\main.py --package busybox --repo %REPO%
echo === 4. Error: package not in repository ===
py src\main.py --package no-such-package --repo %REPO%
echo === 5. Error: repository path does not exist (404) ===
py src\main.py --package curl --repo https://dl-cdn.alpinelinux.org/alpine/v3.20/main/nope
echo === 6. Error: host is unreachable ===
py src\main.py --package curl --repo https://no-such-host.invalid/alpine
echo === 7. Test mode is not implemented yet ===
py src\main.py --package A --repo data\graph_simple.txt --test-mode