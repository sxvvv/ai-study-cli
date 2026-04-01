@echo off
REM AI Study CLI - Windows快捷启动脚本
REM 把这个文件放到你的PATH目录下，就可以直接用 study today 等命令
REM 或者修改下面的路径为你的实际安装路径

python "%~dp0study.py" %*
