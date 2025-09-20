from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "peer2learn_secret"

# SQLite baza
import os

# -------- DATABASE SETUP --------
# Render.comdagi PostgreSQL yoki lokal SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///peer2learn.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -------- MODELLAR --------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, default=0)
    courses = db.relationship("Enrollment", backref="user", lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    enrollments = db.relationship("Enrollment", backref="course", lazy=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

# -------- ROUTELAR --------
@app.route("/")
def index():
    if "username" in session:
        return f"""
        <h1>Salom, {session['username']}!</h1>
        <p><a href='/profile'>👤 Profil</a></p>
        <p><a href='/courses'>📚 Kurslar</a></p>
        <p><a href='/ranking'>🏆 Reyting</a></p>
        <p><a href='/logout'>🚪 Chiqish</a></p>
        """
    return """
    <h1>Peer2Learn platformasiga xush kelibsiz!</h1>
    <p><a href='/login'>🔑 Kirish</a></p>
    <p><a href='/register'>📝 Ro‘yxatdan o‘tish</a></p>
    <p><a href='/ranking'>🏆 Reyting</a></p>
    """

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return "❌ Bu foydalanuvchi allaqachon mavjud!"
        user = User(username=username, password=password, points=10)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return """
    <h2>Ro‘yxatdan o‘tish</h2>
    <form method="post">
        Username: <input type="text" name="username"><br>
        Parol: <input type="password" name="password"><br>
        <button type="submit">Ro‘yxatdan o‘tish</button>
    </form>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["username"] = user.username
            return redirect(url_for("index"))
        return "❌ Login yoki parol xato!"
    return """
    <h2>Kirish</h2>
    <form method="post">
        Username: <input type="text" name="username"><br>
        Parol: <input type="password" name="password"><br>
        <button type="submit">Kirish</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))

@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(username=session["username"]).first()
    courses = [enrollment.course.name for enrollment in user.courses]
    return f"""
    <h2>👤 Profil: {user.username}</h2>
    <p>Ball: {user.points}</p>
    <p>Kurslar: {', '.join(courses) or 'Yo‘q'}</p>
    <p><a href='/courses'>📚 Kurslar ro‘yxati</a></p>
    """

@app.route("/courses")
def show_courses():
    if "username" not in session:
        return redirect(url_for("login"))
    courses = Course.query.all()
    html = "<h2>Kurslar</h2><ul>"
    for c in courses:
        html += f"<li>{c.name} – <a href='/enroll/{c.id}'>Ro‘yxatdan o‘tish (10 ball)</a></li>"
    html += "</ul>"
    return html

@app.route("/enroll/<int:course_id>")
def enroll(course_id):
    if "username" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(username=session["username"]).first()
    course = Course.query.get(course_id)
    if not course:
        return "❌ Kurs topilmadi!"
    if user.points >= 10:
        user.points -= 10
        enrollment = Enrollment(user_id=user.id, course_id=course.id)
        db.session.add(enrollment)
        db.session.commit()
        return f"{user.username} {course.name} kursiga yozildi! Ball qoldi: {user.points}"
    else:
        return "❌ Yetarli ball yo‘q!"

@app.route("/ranking")
def ranking():
    users = User.query.order_by(User.points.desc()).all()
    html = "<h2>🏆 Reyting</h2><ol>"
    for u in users:
        html += f"<li>{u.username} – {u.points} ball</li>"
    html += "</ol>"
    return html

# -------- BAZA TAYYORLASH --------
# before_first_request o'rniga ishlatiladi
first_request = True

@app.before_request
def setup():
    global first_request
    if first_request:
        db.create_all()
        if not Course.query.first():
            db.session.add_all([
                Course(name="Matematika"),
                Course(name="Ingliz tili"),
                Course(name="Fizika"),
                Course(name="Dasturlash")
            ])
            db.session.commit()
        first_request = False

if __name__ == "__main__":
    app.run()