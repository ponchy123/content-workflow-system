import os
import sys
import subprocess
import time
import socket
from threading import Thread

def check_redis():
    """检查Redis服务是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(('localhost', 6379))
        sock.close()
        return True
    except:
        return False

def check_port(port):
    """检查端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', port))
        sock.close()
        return True
    except:
        return False

def run_backend():
    """启动Django后端服务"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    subprocess.run([sys.executable, 'manage.py', 'runserver', '8000'])

def run_celery():
    """启动Celery异步任务"""
    if os.name == 'nt':  # Windows
        subprocess.run([sys.executable, '-m', 'celery', '-A', 'config.celery', 'worker', '--loglevel=info', '--pool=solo'])
    else:
        subprocess.run([sys.executable, '-m', 'celery', '-A', 'config.celery', 'worker', '--loglevel=info'])

def run_celery_beat():
    """启动Celery定时任务"""
    subprocess.run([sys.executable, '-m', 'celery', '-A', 'config.celery', 'beat', '--loglevel=info'])

def run_frontend():
    """启动Vue前端服务"""
    os.chdir('frontend')
    if os.name == 'nt':  # Windows
        subprocess.run('npm install && npm run dev', shell=True)
    else:
        subprocess.run(['npm', 'install'], shell=True)
        subprocess.run(['npm', 'run', 'dev'])

if __name__ == '__main__':
    print("Starting all services...")
    
    # 检查Redis服务
    if check_redis():
        print("Redis is running")
    else:
        print("Warning: Redis is not running! Celery may not work properly.")
    
    # 检查端口
    frontend_port = 5174
    
    # 创建线程
    backend_thread = Thread(target=run_backend)
    celery_thread = Thread(target=run_celery)
    celery_beat_thread = Thread(target=run_celery_beat)
    frontend_thread = Thread(target=run_frontend)
    
    # 启动所有服务
    print("Backend server started at http://localhost:8000")
    backend_thread.start()
    
    time.sleep(2)  # 等待后端启动
    
    print("Starting Celery worker...")
    celery_thread.start()
    
    time.sleep(1)
    
    print("Starting Celery beat...")
    celery_beat_thread.start()
    
    time.sleep(1)
    
    print(f"Frontend server started at http://localhost:{frontend_port}")
    frontend_thread.start()
    
    # 等待所有线程结束
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        sys.exit(0)