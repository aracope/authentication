from flask import Flask, render_template, redirect, session, flash, abort, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from forms import RegisterForm, LoginForm, FeedbackForm
from models import db, User, Feedback
from flask_bcrypt import Bcrypt

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///authentication_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here' 
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Initialize extensions
toolbar = DebugToolbarExtension(app)
bcrypt = Bcrypt(app)
db.init_app(app)

# Helpers
def ensure_correct_user(username):
    if session.get("username") != username:
        abort(403)

# Error Handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Routes
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
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        return redirect(url_for('show_user', username=new_user.username))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(f"/users/{user.username}")
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route("/users/<username>")
def show_user(username):
    ensure_correct_user(username)
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user.html", user=user)

@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    ensure_correct_user(username)
    user = User.query.get_or_404(session.get("user_id"))
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash("User deleted successfully.", "success")
    return redirect(url_for('home'))

@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    ensure_correct_user(username)
    form = FeedbackForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        feedback = Feedback(
            title=form.title.data,
            content=form.content.data,
            user_id=user.id
        )
        db.session.add(feedback)
        db.session.commit()
        return redirect(url_for('show_user', username=username))
    return render_template("add_feedback.html", form=form)

@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.user_id != session.get("user_id"):
        abort(403)
    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        flash("Feedback updated!", "success")
        return redirect(url_for('show_user', username=feedback.user.username))
    return render_template("edit_feedback.html", form=form, feedback=feedback)

@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.user_id != session.get('user_id'):
        abort(403)
    username = feedback.user.username
    db.session.delete(feedback)
    db.session.commit()
    flash("Feedback deleted.", "success")
    return redirect(url_for('show_user', username=username))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)