@echo off
pyinstaller --onefile --windowed --name FlagTool --icon ico.ico FlagTool.py

REM Caminho final do executável
set exe_dir=dist

REM Copiar arquivos extras para pasta do executável
copy "interface.ini" "%exe_dir%"
copy "flags.ini" "%exe_dir%"
copy "color.ini" "%exe_dir%"
copy "font.ini" "%exe_dir%"

pause
