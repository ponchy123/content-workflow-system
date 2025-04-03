@echo off
echo 正在启动 Loophole 前端服务(HTTP模式)...
echo 请不要关闭此窗口

:: 设置路径 - 已修改为实际路径
cd /d D:\common_software\loophole

:: 设置正确的loophole路径
set LOOPHOLE=D:\common_software\loophole\loophole\loophole.exe

:: 前端服务（运行在端口5176，HTTP模式）
echo 正在启动前端隧道，连接到端口5176...
"%LOOPHOLE%" http 5176 --hostname freight-app

pause 