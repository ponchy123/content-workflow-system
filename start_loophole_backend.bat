@echo off
echo 正在启动 Loophole 后端服务...
echo 请不要关闭此窗口

:: 设置路径 - 已修改为实际路径
cd /d D:\common_software\loophole

:: 设置正确的loophole路径
set LOOPHOLE=D:\common_software\loophole\loophole.exe

:: 后端服务（运行在端口8000）
echo 正在启动后端隧道，连接到端口8000...
"%LOOPHOLE%" http 8000 --hostname freight-api

echo 如果上面的命令自动退出，请按照以下步骤手动运行：
echo 1. 打开命令提示符(cmd.exe)
echo 2. 输入: cd /d D:\common_software\loophole
echo 3. 输入: D:\common_software\loophole\loophole.exe http 8000 --hostname freight-api

pause 