import pytest
from app import app, db, User, Feedback
from flask_bcrypt import generate_password_hash

# Test Configuration
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///authentication_db_test'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        with app.test_client() as client:
            yield client

@pytest.fixture
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

# User Fixtures
@pytest.fixture
def test_user(init_db):
    hashed_pw = generate_password_hash("correctpassword").decode('utf-8')
    user = User(
        username="testuser",
        password=hashed_pw,
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def other_user(init_db):
    hashed_pw = generate_password_hash("otherpassword").decode('utf-8')
    user = User(
        username="otheruser",
        password=hashed_pw,
        email="other@example.com",
        first_name="Other",
        last_name="User"
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def feedback(init_db, test_user):
    feedback = Feedback(
        title="Great app!",
        content="Loved using this app.",
        user_id=test_user.id
    )
    db.session.add(feedback)
    db.session.commit()
    return feedback

@pytest.fixture
def other_feedback(init_db, other_user):
    feedback = Feedback(
        title="Should not edit",
        content="Nope.",
        user_id=other_user.id
    )
    db.session.add(feedback)
    db.session.commit()
    return feedback

# Helper to simulate login
@pytest.fixture
def auth(client):
    class AuthActions:
        def login(self, username="testuser", password="correctpassword"):
            return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

        def logout(self):
            return client.get("/logout", follow_redirects=True)
    return AuthActions()

# Test Cases

# Authentication Tests
def test_register_user(client, init_db):
    resp = client.post("/register", data={
        "username": "newuser",
        "password": "password",
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "User"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"newuser" in resp.data

def test_login_valid(client, test_user, auth):
    resp = auth.login(username=test_user.username, password="correctpassword")
    assert resp.status_code == 200
    assert b"testuser" in resp.data

def test_login_invalid(client, init_db):
    resp = client.post("/login", data={"username": "wrong", "password": "wrong"}, follow_redirects=True)
    assert b"Invalid credentials" in resp.data

def test_logout(client, auth, init_db):
    auth.login()
    resp = auth.logout()
    assert b"You have been logged out." in resp.data

def test_user_access_their_own_profile(client, auth, test_user):
    auth.login()
    resp = client.get(f"/users/{test_user.username}")
    assert resp.status_code == 200
    assert b"Welcome, testuser!" in resp.data

def test_user_cannot_access_other_profile(client, auth, other_user):
    auth.login()
    resp = client.get(f"/users/{other_user.username}")
    assert resp.status_code == 403

def test_user_cannot_edit_other_feedback(client, auth, other_feedback):
    auth.login()
    resp = client.post(f"/feedback/{other_feedback.id}/update", data={
        "title": "Hacked!",
        "content": "Changed!"
    }, follow_redirects=True)
    assert resp.status_code == 403

def test_user_can_edit_own_feedback(client, auth, feedback):
    auth.login()
    resp = client.post(f"/feedback/{feedback.id}/update", data={
        "title": "Updated Title",
        "content": "Updated content."
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Updated Title" in resp.data

def test_user_can_delete_own_feedback(client, auth, feedback):
    auth.login()
    resp = client.post(f"/feedback/{feedback.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Great app!" not in resp.data
