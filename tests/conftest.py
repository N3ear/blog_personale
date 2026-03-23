import os
import sys
from pathlib import Path
import pytest
import random

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Ensure project root is importable when pytest runs from /app/tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app, db, User, bcrypt

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(
            username="testuser",
            email="testuser@example.com",
            password=bcrypt.generate_password_hash("password123").decode("utf-8"),
            profile_name="Testuser",
            profile_image="default.png",
        )
        db.session.add(user)
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_client(client):
    
    suffix = random.randint(1000, 9999)
    username = f"user_{suffix}"
    email = f"test_{suffix}@example.com"
    password = "password123"
    
    client.post("/api/register", json={
        "username": username,
        "email":email,
        "password": password,
    })
    
    login_res = client.post("/api/login", json={
        "username": username,
        "password": password,
    })
    token = login_res.get_json()["token"]
    
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    
    return client, username