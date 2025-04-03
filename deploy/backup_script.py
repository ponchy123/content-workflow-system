#!/usr/bin/env python
import os
import datetime
import subprocess
import logging
import zipfile
from pathlib import Path
from django.conf import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self):
        self.now = datetime.datetime.now()
        self.backup_root = Path(settings.BASE_DIR) / 'backups'
        self.backup_dir = self.backup_root / self.now.strftime('%Y%m')
        self.backup_file = f"freight_{self.now.strftime('%Y%m%d_%H%M%S')}.sql"
        self.db_settings = settings.DATABASES['default']

    def create_backup_dirs(self):
        """创建备份目录"""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created backup directory: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            raise

    def backup_database(self):
        """执行数据库备份"""
        try:
            backup_path = self.backup_dir / self.backup_file
            cmd = [
                'mysqldump',
                f"--host={self.db_settings['HOST']}",
                f"--port={self.db_settings['PORT']}",
                f"--user={self.db_settings['USER']}",
                f"--password={self.db_settings['PASSWORD']}",
                '--single-transaction',  # 保证数据一致性
                '--quick',  # 大表优化
                '--lock-tables=false',  # 避免锁表
                '--set-gtid-purged=OFF',  # 避免GTID相关警告
                self.db_settings['NAME'],
                f"> {backup_path}"
            ]
            
            subprocess.run(' '.join(cmd), shell=True, check=True)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Database backup failed: {e}")
            raise

    def compress_backup(self, backup_path):
        """压缩备份文件"""
        try:
            # 使用zipfile替代gzip，更好地跨平台兼容
            zip_path = str(backup_path) + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, os.path.basename(backup_path))
            
            # 压缩完成后删除原始文件
            os.remove(backup_path)
            logger.info(f"Backup compressed: {zip_path}")
        except Exception as e:
            logger.error(f"Backup compression failed: {e}")
            raise

    def cleanup_old_backups(self):
        """清理30天前的备份"""
        try:
            # 修改为跨平台兼容的方式清理旧备份
            current_time = datetime.datetime.now()
            cutoff_time = current_time - datetime.timedelta(days=30)
            
            # 遍历备份目录查找旧文件
            for root, dirs, files in os.walk(self.backup_root):
                for file in files:
                    if file.endswith('.zip') or file.endswith('.sql'):
                        file_path = os.path.join(root, file)
                        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_time < cutoff_time:
                            os.remove(file_path)
                            logger.info(f"Deleted old backup: {file_path}")
            
            logger.info("Old backups cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise

    def run(self):
        """执行完整的备份流程"""
        try:
            logger.info("Starting database backup process")
            self.create_backup_dirs()
            backup_path = self.backup_database()
            self.compress_backup(backup_path)
            self.cleanup_old_backups()
            logger.info("Database backup process completed successfully")
        except Exception as e:
            logger.error(f"Backup process failed: {e}")
            raise

if __name__ == '__main__':
    backup = DatabaseBackup()
    backup.run() 