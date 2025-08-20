from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, String, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from prometheus_fastapi_instrumentator import Instrumentator

# 初始化FastAPI应用
app = FastAPI(title="MCP Tool Registry")

# 启动Prometheus指标服务器
metrics_port = int(os.environ.get("MCP_REGISTRY_METRICS_PORT", 8004))
start_http_server(metrics_port)
print(f"Prometheus metrics server started on port {metrics_port}")

# 配置数据库
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./tools.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 依赖：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化Prometheus指标
instrumentator = Instrumentator()

# 添加自定义指标
tool_count = Gauge('mcp_tool_count', 'Number of registered tools')
request_counter = Counter('mcp_requests_total', 'Total number of requests', ['endpoint', 'method', 'status_code'])
request_latency = Histogram('mcp_request_latency_seconds', 'Request latency in seconds', ['endpoint', 'method'])

def update_tool_count(db: Session = Depends(get_db)):
    """更新工具计数指标"""
    count = db.query(Tool).count()
    tool_count.set(count)

# 添加请求指标中间件
@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    start_time = datetime.now()
    endpoint = request.url.path
    method = request.method

    # 处理请求
    response = await call_next(request)

    # 计算请求延迟
    latency = (datetime.now() - start_time).total_seconds()

    # 记录指标
    request_counter.labels(endpoint=endpoint, method=method, status_code=response.status_code).inc()
    request_latency.labels(endpoint=endpoint, method=method).observe(latency)

    return response

# 定义工具模型
class Tool(Base):
    __tablename__ = "tools"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(500))
    endpoint = Column(String(255))
    parameters = Column(JSON)
    auth_required = Column(Boolean, default=True)
    owner_id = Column(String(255))

# 安全配置
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 验证密码
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 获取密码哈希
def get_password_hash(password):
    return pwd_context.hash(password)

# 创建访问令牌
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # 在实际应用中，这里应该从数据库中获取用户
    return {"username": username}

# 路由：获取访问令牌
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 在实际应用中，这里应该验证用户凭据
    # 为简化示例，我们假设任何用户名/密码组合都有效
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# 路由：注册工具
@app.post("/tools/")
async def register_tool(
    tool: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 检查工具是否已存在
    db_tool = db.query(Tool).filter(Tool.name == tool.get("name")).first()
    if db_tool:
        raise HTTPException(status_code=400, detail="Tool already registered")

    # 创建新工具
    new_tool = Tool(
        id=tool.get("id", str(hash(tool.get("name")))),
        name=tool.get("name"),
        description=tool.get("description"),
        endpoint=tool.get("endpoint"),
        parameters=tool.get("parameters", {}),
        auth_required=tool.get("auth_required", True),
        owner_id=current_user.get("username")
    )

    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)

    # 更新工具计数
    update_tool_count(db)

    return new_tool

# 路由：获取工具列表
@app.get("/tools/")
async def get_tools(db: Session = Depends(get_db)):
    return db.query(Tool).all()

# 路由：获取特定工具
@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str, db: Session = Depends(get_db)):
    db_tool = db.query(Tool).filter(Tool.name == tool_name).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return db_tool

# 路由：更新工具
@app.put("/tools/{tool_name}")
async def update_tool(
    tool_name: str,
    tool: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_tool = db.query(Tool).filter(Tool.name == tool_name).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    # 检查所有权
    if db_tool.owner_id != current_user.get("username"):
        raise HTTPException(status_code=403, detail="Not authorized to update this tool")

    # 更新工具信息
    for key, value in tool.items():
        if hasattr(db_tool, key):
            setattr(db_tool, key, value)

    db.commit()
    db.refresh(db_tool)
    return db_tool

# 路由：删除工具
@app.delete("/tools/{tool_name}")
async def delete_tool(
    tool_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_tool = db.query(Tool).filter(Tool.name == tool_name).first()
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    # 检查所有权
    if db_tool.owner_id != current_user.get("username"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this tool")

    db.delete(db_tool)
    db.commit()

    # 更新工具计数
    update_tool_count(db)

    return {"detail": "Tool deleted"}

# 初始化数据库
Base.metadata.create_all(bind=engine)

# 启动时更新工具计数
with next(get_db()) as db:
    update_tool_count(db)

# 启动Prometheus指标服务器
metrics_port = int(os.environ.get('METRICS_PORT', '8004'))
start_http_server(metrics_port)
print(f"Prometheus指标服务器启动在端口 {metrics_port}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)