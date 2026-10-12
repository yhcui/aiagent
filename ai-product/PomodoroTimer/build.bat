@echo off
rem ============================================
rem  Build Pomodoro Timer with the built-in
rem  .NET Framework compiler (csc.exe).
rem  No development environment required.
rem ============================================
setlocal
set "CSC64=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
set "CSC32=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if exist "%CSC64%" (set "CSC=%CSC64%") else (set "CSC=%CSC32%")
if not exist "%CSC%" (
  echo [ERROR] csc.exe not found.
  exit /b 1
)
"%CSC%" /nologo /target:winexe /codepage:65001 /optimize+ /out:"%~dp0Pomodoro.exe" /r:System.Windows.Forms.dll /r:System.Drawing.dll "%~dp0Pomodoro.cs"
if errorlevel 1 (
  echo [ERROR] Build failed.
  exit /b 1
)
echo [OK] Built %~dp0Pomodoro.exe
endlocal
