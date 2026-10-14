@echo off
chcp 65001 >nul
title Instalador - Titan Titles Studio v1.0
color 0B
echo.
echo ============================================================
echo         TITAN TITLES STUDIO v1.0 - @rangelmaker_
echo           Instalador Automatico para DaVinci Resolve
echo ============================================================
echo.
set "TARGET=%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Edit"
echo [*] Verificando pasta de scripts do DaVinci Resolve...
if not exist "%TARGET%" mkdir "%TARGET%"
if not exist "%TARGET%\icons" mkdir "%TARGET%\icons"
echo [*] Copiando Titan Titles Studio.py...
copy /Y "%~dp0Arquivos\Titan Titles Studio.py" "%TARGET%\" >nul
echo [*] Copiando icones e tema azul titanico...
xcopy /E /I /Y "%~dp0Arquivos\icons" "%TARGET%\icons" >nul
echo.
echo ============================================================
echo  [OK] Titan Titles Studio instalado com sucesso no Windows!
echo  Menu: Workspace > Scripts > Edit > Titan Titles Studio
echo ============================================================
echo.
pause