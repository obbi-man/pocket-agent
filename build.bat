@echo off
setlocal
cd /d "%~dp0"

echo === Pocket Agent build ===
where py >nul 2>&1 && set PY=py -3 || set PY=python

echo [1/3] deps...
%PY% -m pip install -q -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1

echo [2/3] PyInstaller...
%PY% -m PyInstaller --noconfirm PocketAgent.spec
if errorlevel 1 exit /b 1
if not exist "dist\PocketAgent\PocketAgent.exe" (
  echo PocketAgent.exe not found
  exit /b 1
)

echo [3/3] Inno Setup...
set ISCC=
for %%I in (
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
  "C:\Program Files\Inno Setup 6\ISCC.exe"
) do if exist %%I set ISCC=%%~I
if not defined ISCC (
  echo ISCC.exe not found — folder build is ready: dist\PocketAgent\
  exit /b 0
)
"%ISCC%" Setup.iss
if errorlevel 1 exit /b 1

echo.
echo DONE
echo   App      : dist\PocketAgent\PocketAgent.exe
echo   Installer: dist\PocketAgentSetup-0.2.0.exe
endlocal
