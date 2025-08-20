import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 使用SQLite内存数据库进行测试
SQLALCHEMY_DATABASE_URL = 'sqlite:///:memory:'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 覆盖依赖项，使用测试数据库
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_user():
    """测试创建用户"""
    response = client.post(
        "/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test@1234"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_create_user_duplicate_username():
    """测试创建重复用户名的用户"""
    # 先创建一个用户
    client.post(
        "/users/",
        json={
            "username": "duplicateuser",
            "email": "duplicate@example.com",
            "password": "Test@1234"
        }
    )
    # 尝试使用相同的用户名创建另一个用户
    response = client.post(
        "/users/",
        json={
            "username": "duplicateuser",
            "email": "another@example.com",
            "password": "Test@1234"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data

def test_login():
    """测试登录功能"""
    # 先创建一个用户
    client.post(
        "/users/",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "Test@1234"
        }
    )
    # 尝试登录
    response = client.post(
        "/token",
        data={
            "username": "loginuser",
            "password": "Test@1234"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    """测试使用无效凭据登录"""
    response = client.post(
        "/token",
        data={
            "username": "nonexistentuser",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data

def test_read_users_me():
    """测试获取当前用户信息"""
    # 先创建一个用户
    client.post(
        "/users/",
        json={
            "username": "meuser",
            "email": "me@example.com",
            "password": "Test@1234"
        }
    )
    # 登录获取令牌
    login_response = client.post(
        "/token",
        data={
            "username": "meuser",
            "password": "Test@1234"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    # 使用令牌获取用户信息
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert data["email"] == "me@example.com"