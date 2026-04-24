from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required

app = Flask(__name__)
app.config["SECRET_KEY"] = "petcare_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///petcare.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_name = db.Column(db.String(120), nullable=False)
    pet_name = db.Column(db.String(120), nullable=False)
    pet_type = db.Column(db.String(80), nullable=False)
    service = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/grooming")
@login_required
def grooming():
    return render_template("grooming.html")


@app.route("/vetcare")
@login_required
def vetcare():
    return render_template("vetcare.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered. Please login.")
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    appointments = Appointment.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", appointments=appointments)


@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "POST":
        appointment = Appointment(
            owner_name=current_user.name,
            pet_name=request.form["pet_name"],
            pet_type=request.form["pet_type"],
            service=request.form["service"],
            date=request.form["date"],
            phone=request.form["phone"],
            message=request.form["message"],
            user_id=current_user.id
        )

        db.session.add(appointment)
        db.session.commit()

        flash("Appointment booked successfully.")
        return redirect(url_for("dashboard"))

    return render_template("book.html")


@app.route("/appointments")
@login_required
def appointments():
    all_appointments = Appointment.query.all()
    return render_template("appointments.html", appointments=all_appointments)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)