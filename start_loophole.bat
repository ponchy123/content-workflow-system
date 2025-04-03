@echo off
echo 正在启动 Loophole 服务...
echo 请不要关闭此窗口

:: 设置路径 - 已修改为实际路径
cd /d D:\common_software\loophole

:: 设置正确的loophole路径
set LOOPHOLE=D:\common_software\loophole\loophole\loophole.exe

:: 前端服务（运行在端口5176）
echo 正在启动前端隧道，连接到端口5176...
"%LOOPHOLE%" http 5176 --hostname freight-app

echo 如果上面的命令自动退出，请按照以下步骤手动运行：
echo 1. 打开命令提示符(cmd.exe)
echo 2. 输入: cd /d D:\common_software\loophole
echo 3. 输入: D:\common_software\loophole\loophole\loophole.exe http 5176 --hostname freight-app

echo.
echo Loophole 服务已启动
echo 前端地址: https://freight-app.loophole.site
echo.
echo 请确保前端和后端服务已经启动：
echo 1. 前端：npm run dev（在frontend目录）
echo 2. 后端：python manage.py runserver 0.0.0.0:8000
echo.
pause 