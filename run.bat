@echo off
echo 银河麒麟运维管理工具启动器
echo ========================

set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

if "%1"=="server" goto server
if "%1"=="client" goto client
goto usage

:server
echo 启动服务端...
python server\__main__.py %2 %3
goto end

:client
echo 启动客户端...
python client\__main__.py %2 %3
goto end

:usage
echo 用法: run.bat [server^|client] [host] [port]
echo.
echo 示例:
echo   run.bat server           - 启动服务端(默认端口29876)
echo   run.bat client           - 启动客户端(连接localhost:29876)
echo   run.bat client localhost 29876 - 启动客户端并连接指定服务器

:end
pause
