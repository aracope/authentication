from flask import Flask, render_template, redirect, session, flash
from forms import RegisterForm, LoginForm
from models import db, User

from flask_bcrypt import Bcrypt


app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///authentication_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here' 

bcrypt = Bcrypt(app)

# Initialize database with app
db.init_app(app)

@app.route("/")
def home():
    return redirect("/register")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            username=form.username.data,
            password=hashed_pw,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        db.session.add(new_user)
        db.session.commit()
        session['username'] = new_user.username
        return redirect(f"/users/{new_user.username}") 
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.get(form.username.data)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['username'] = user.username
            return redirect(f"/users/{user.username}") 
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

@app.route("/secret")
def secret():
    if "username" not in session:
        flash("You must be logged in to view that page.", "danger")
        return redirect("/login")
    return "You made it!"

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/")

@app.route("/users/<username>")
def show_user(username):
    if "username" not in session or session["username"] != username:
        flash("You don't have permission to view that page.", "danger")
        return redirect("/login")

    user = User.query.get_or_404(username)
    return render_template("user.html", user=user)

