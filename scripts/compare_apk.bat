@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set REPO=https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64
if not exist output mkdir output

for %%P in (curl bash boost1.82-libs) do (
  echo === %%P ===
  py src\main.py --package %%P --repo %REPO% --ascii-tree > output\our_%%P.txt
  docker run --rm alpine:3.20 sh -c "apk update >/dev/null && apk info -R %%P" > output\apk_info_%%P.txt
  docker run --rm alpine:3.20 sh -c "apk update >/dev/null && apk dot %%P" > output\apk_dot_%%P.txt
  docker run --rm alpine:3.20 sh -c "apk update >/dev/null && apk add --simulate %%P" > output\apk_add_%%P.txt
)
echo Done: files are in the output folder