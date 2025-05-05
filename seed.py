from app import app, db 
from models import User, Feedback 

def seed():
    with app.app_context():  
        # Create some users
        user1 = User(username="testuser1", password="password1")
        user2 = User(username="testuser2", password="password2")
        db.session.add(user1)
        db.session.add(user2)

        # Create some feedback for user1
        feedback1 = Feedback(title="Great app!", content="I really enjoyed using this app.", user_id=user1.id)
        feedback2 = Feedback(title="Needs improvement", content="I think the UI could be better.", user_id=user1.id)
        db.session.add(feedback1)
        db.session.add(feedback2)

        # Commit the session to save the data
        db.session.commit()

if __name__ == "__main__":
    seed()
