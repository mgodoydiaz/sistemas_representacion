@echo off
setlocal enabledelayedexpansion
title Visor de entregas - Sistemas de Representacion

rem Este script levanta el servidor propio del proyecto (servidor.py) sobre
rem la carpeta del proyecto y abre el visor en el navegador predeterminado.
rem servidor.py sirve los mismos archivos que antes (solo lectura) y ademas
rem atiende el guardado del escaner manual de laminas (visor/escaner.html).
rem No requiere instalar nada mas alla de Python (y, para la capa de trazo
rem del escaner manual, OpenCV -- si no esta instalado el escaner sigue
rem funcionando igual, solo sin esa capa; ver visor/LEEME_ESCANER.md).

set "PUERTO=8000"
set "RAIZ=%~dp0"
cd /d "%RAIZ%"

rem --- Verifica que Python este disponible ---
set "PY_CMD="
where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>nul
    if !ERRORLEVEL!==0 (
        set "PY_CMD=py"
    )
)

if "%PY_CMD%"=="" (
    echo.
    echo No se encontro Python instalado en este computador.
    echo.
    echo El visor necesita Python para levantar un servidor web local
    echo que sirva los archivos ^(la pagina no funciona bien si se abre
    echo directamente como archivo desde el disco^).
    echo.
    echo Instale Python desde https://www.python.org/downloads/ marcando
    echo la opcion "Add Python to PATH" durante la instalacion, y vuelva
    echo a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

echo.
echo Carpeta del proyecto: %RAIZ%
echo Verificando carpeta de datos (salida\)...
if not exist "%RAIZ%salida\manifest.json" (
    echo.
    echo AVISO: no se encontro "%RAIZ%salida\manifest.json".
    echo El visor abrira igual, pero mostrara un mensaje de error hasta
    echo que el proceso de recortes genere la carpeta salida\.
    echo.
    echo ^(Para probar el visor mientras tanto, puede abrirlo con datos de
    echo prueba usando la URL: http://localhost:%PUERTO%/visor/index.html?datos=../salida_demo^)
    echo.
)

if not exist "%RAIZ%servidor.py" (
    echo.
    echo No se encontro "%RAIZ%servidor.py". Se usara el servidor generico
    echo de Python en su lugar ^(el escaner manual de laminas no va a
    echo funcionar sin servidor.py: solo el visor de solo lectura^).
    echo.
    start "" "http://localhost:%PUERTO%/visor/index.html"
    %PY_CMD% -m http.server %PUERTO%
    goto :fin
)

echo Iniciando servidor local en el puerto %PUERTO% (servidor.py) ...
echo No cierre esta ventana mientras use el visor o el escaner manual.
echo.

start "" "http://localhost:%PUERTO%/visor/index.html"

%PY_CMD% "%RAIZ%servidor.py" %PUERTO%

:fin
echo.
echo El servidor se detuvo.
pause
