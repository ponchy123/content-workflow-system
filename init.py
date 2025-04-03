import os
import sys
import subprocess
import platform
import shutil

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("Error: Python 3.9+ is required")
        sys.exit(1)
    print(f"Python version check passed: {sys.version}")

def check_node_version():
    """检查Node.js版本"""
    # 首先检查npm命令是否存在
    npm_path = shutil.which('npm')
    if not npm_path:
        print("Error: npm not found. Please install Node.js from https://nodejs.org/")
        print("After installation, you may need to restart your terminal/IDE")
        sys.exit(1)
    
    try:
        result = subprocess.run(['node', '-v'], capture_output=True, text=True)
        version = result.stdout.strip()
        if not version.startswith('v16'):
            print(f"Warning: Node.js 16+ is recommended (current: {version})")
        print(f"Node.js version check passed: {version}")
    except FileNotFoundError:
        print("Error: Node.js is not installed")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)

def install_python_dependencies():
    """安装Python依赖"""
    print("Installing Python dependencies...")
    try:
        # 升级pip
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        # 安装依赖
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Error installing Python dependencies:")
            print(result.stderr)
            sys.exit(1)
        print("Python dependencies installed successfully")
    except Exception as e:
        print(f"Error installing Python dependencies: {str(e)}")
        sys.exit(1)

def install_node_dependencies():
    """安装Node.js依赖"""
    print("Installing Node.js dependencies...")
    if not os.path.exists('frontend'):
        print("Error: frontend directory not found")
        return
    
    try:
        os.chdir('frontend')
        # 检查package.json是否存在
        if not os.path.exists('package.json'):
            print("Error: package.json not found in frontend directory")
            return
        
        # 清理node_modules
        if os.path.exists('node_modules'):
            print("Cleaning existing node_modules...")
            try:
                shutil.rmtree('node_modules')
            except Exception as e:
                print(f"Warning: Failed to clean node_modules: {str(e)}")
        
        # 安装依赖
        result = subprocess.run('npm install', shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("Error installing Node.js dependencies:")
            print(result.stderr)
        else:
            print("Node.js dependencies installed successfully")
    except Exception as e:
        print(f"Error in Node.js setup: {str(e)}")
    finally:
        os.chdir('..')

def setup_database():
    """初始化数据库"""
    print("Setting up database...")
    try:
        # 检查是否存在.env文件
        if not os.path.exists('.env'):
            print("Creating default .env file...")
            with open('.env', 'w') as f:
                f.write("""DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://root:password@localhost:3306/freight
REDIS_URL=redis://localhost:6379/0
""")
            print("Please update .env file with your database credentials")
        
        # 运行数据库迁移
        result = subprocess.run([sys.executable, 'manage.py', 'migrate'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error running database migrations:")
            print(result.stderr)
            sys.exit(1)
        print("Database setup completed successfully")
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        sys.exit(1)

def create_superuser():
    """创建超级用户"""
    print("Creating superuser...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'createsuperuser'], check=True)
    except subprocess.CalledProcessError:
        print("Error creating superuser")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """主函数"""
    print("="*50)
    print("Initializing Freight Calculation System")
    print("="*50)
    
    # 检查环境
    check_python_version()
    check_node_version()
    
    # 安装依赖
    install_python_dependencies()
    install_node_dependencies()
    
    # 初始化数据库
    setup_database()
    
    # 询问是否创建超级用户
    create_superuser_input = input("Do you want to create a superuser? (y/n): ")
    if create_superuser_input.lower() == 'y':
        create_superuser()
    
    print("\n" + "="*50)
    print("Initialization completed!")
    print("\nNext steps:")
    print("1. Update the .env file with your database credentials")
    print("2. Start the project using: python start.py")
    print("="*50)

if __name__ == '__main__':
    main() 