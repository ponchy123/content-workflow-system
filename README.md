# 物流报价单计算系统

本系统用于计算物流运费，支持多种物流服务商、多区域费率矩阵、附加费计算等功能。

## 主要功能

- 基础运费计算
- 附加费计算
- 批量计算处理
- 邮编区域管理
- 费率管理
- 用户权限控制

## 技术栈

- 前端：Vue3 + Element Plus
- 后端：Django REST Framework
- 数据库：MySQL 8.0
- 缓存：Redis
- 任务队列：Celery

## 安装与运行

```bash
# 后端服务
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 前端服务
cd frontend
npm install
npm run dev
```

## 系统架构

本系统采用前后端分离架构，通过REST API实现通信，支持分布式部署和高可用配置。 