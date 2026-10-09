@echo off
title Corrector Actividad 1 - PCI1119
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (set PY=python)

%PY% -c "import PIL, numpy, tkinter" >nul 2>nul
if errorlevel 1 (
  echo Faltan librerias. Instalando pillow y numpy...
  %PY% -m pip install --user --quiet pillow numpy
  if errorlevel 1 (
     echo.
     echo No se pudo instalar. Abre una consola y ejecuta:
     echo     python -m pip install --user pillow numpy
     echo.
     pause
     exit /b 1
  )
)

where pyw >nul 2>nul
if %errorlevel%==0 (
  start "" pyw -3 "%~dp0PegarYCorregir.pyw"
) else (
  start "" pythonw "%~dp0PegarYCorregir.pyw"
)
exit /b 0
