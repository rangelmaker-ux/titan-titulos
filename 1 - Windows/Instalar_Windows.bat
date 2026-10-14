@echo off
chcp 65001 >nul
title Titan Titles Studio
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Instalar_Titan.ps1"
if errorlevel 1 pause
