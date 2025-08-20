#!/bin/bash
set -e

echo "正在重置MySQL root密码..."

docker-compose run --rm mysql sh -c "mysqld_safe --skip-grant-tables & sleep 5 && mysql -u root -e \"ALTER USER 'root'@'%' IDENTIFIED BY 'password'; FLUSH PRIVILEGES;\""

echo "密码重置完成！"