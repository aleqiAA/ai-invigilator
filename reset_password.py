# Reset invigilator password
from app import app
from database import db, Invigilator

with app.app_context():
    inv = Invigilator.query.filter_by(email='johndoe@gmail.com').first()
    if inv:
        inv.set_password('password123')
        db.session.commit()
        print("Password reset to: password123")
    else:
        print("Invigilator not found")
