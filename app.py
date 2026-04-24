import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print("API KEY LOADED =", api_key[:10] if api_key else None)

client = OpenAI(api_key=api_key)

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



WEBSITE_LINK = "https://petcare-ixn0.onrender.com"

def get_website_content():
    try:
        response = requests.get(WEBSITE_LINK, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text[:6000]

    except Exception as e:
        print("Website read error:", e)
        return "PetCare offers grooming, vet care, vaccination and appointment booking."


@app.route("/chatbot", methods=["POST"])
@login_required
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "Please type a message."})

        response = client.responses.create(
            model="gpt-5.4-mini",
            instructions="""
            You are PetCare Assistant.
            Answer about pet grooming, vet care, vaccination, booking and pet care.
            Keep answers short and friendly.
            """,
            input=user_message
        )

        return jsonify({"reply": response.output_text})

    except Exception as e:
        print("CHATBOT ERROR:", e)
        return jsonify({
            "reply": "Sorry, chatbot is not working right now. Please check API key or server logs."
        })

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


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