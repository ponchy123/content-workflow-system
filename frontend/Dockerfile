# 第一阶段：构建React应用
FROM node:18-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制应用代码
COPY . .

# 构建应用
RUN npm run build

# 第二阶段：使用Nginx提供静态文件
FROM nginx:alpine

# 复制构建产物到Nginx的html目录
COPY --from=build /app/build /usr/share/nginx/html

# 复制自定义Nginx配置（如果有的话）
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]