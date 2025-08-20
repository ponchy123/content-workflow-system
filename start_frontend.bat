@echo off

REM 启动前端应用
cd frontend
start npm start

REM 等待前端启动
timeout /t 5 /nobreak >nul

REM 启动API网关
cd ..\api_gateway
start npm start

REM 打开浏览器
start http://localhost:3000

REM 显示启动信息
echo 前端应用已启动: http://localhost:3000
echo API网关已启动: http://localhost:8001
echo 请确保RabbitMQ和MCP注册中心已手动启动
pause