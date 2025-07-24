from flask import Flask, render_template, request, jsonify, url_for, session as flask_session, redirect
from database import session, init_db, User, DailyData
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

init_db()

questions = [
    "Bugün ne kadar su içtin? (Litre)",
    "Bugün kaç adım attın?",
    "Bugün kaç saat uyudun?",
    "Ruh halin nasıl? (İyi, Orta, Kötü)"
]

@app.route("/")
def index():
    user_id = flask_session.get("user_id")
    user = session.query(User).get(user_id) if user_id else None
    if user:
        return redirect(url_for("dashboard"))
    return render_template("index.html", questions=questions, user=None)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        health_goal = request.form.get("health_goal", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not password:
            return "İsim ve şifre zorunludur! <a href='/register'>Geri dön</a>"

        try:
            age_val = int(age) if age else None
        except ValueError:
            return "Yaş sayısal olmalı! <a href='/register'>Geri dön</a>"

        password_hash = generate_password_hash(password)
        new_user = User(name=name, age=age_val, gender=gender, health_goal=health_goal, password_hash=password_hash)
        session.add(new_user)
        session.commit()
        return "Kullanıcı başarıyla eklendi! <a href='/login'>Giriş Yap</a>"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        user = session.query(User).filter_by(name=name).first()

        if not user or not check_password_hash(user.password_hash, password):
            return "Hatalı kullanıcı adı veya şifre! <a href='/login'>Tekrar dene</a>"

        flask_session["user_id"] = user.id
        flask_session["q_index"] = 0
        flask_session["answers"] = {}
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    flask_session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    user_id = flask_session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = session.query(User).get(user_id)
    if not user:
        return redirect(url_for("login"))

    data = session.query(DailyData).filter_by(user_id=user_id).order_by(DailyData.date.asc()).all()
    chart_data = {
        "dates": [d.date.strftime("%Y-%m-%d") for d in data],
        "water": [d.water_intake for d in data],
        "steps": [d.steps for d in data],
        "sleep": [d.sleep_hours for d in data]
    }

    return render_template(
        "dashboard.html",
        user=user,
        data=data,
        chart_data=json.dumps(chart_data),
        questions=questions
    )

@app.route("/chatbot/next", methods=["POST"])
def chatbot_next():
    data = request.get_json()
    user_reply = data.get("answer", "").strip()

    q_index = flask_session.get("q_index", 0)
    if q_index > 0:
        flask_session["answers"][questions[q_index - 1]] = user_reply

    if q_index >= len(questions):
        ans = flask_session["answers"]
        try:
            water = float(ans[questions[0]]) if ans[questions[0]].replace('.', '', 1).isdigit() else 0
            steps = int(ans[questions[1]]) if ans[questions[1]].isdigit() else 0
            sleep = float(ans[questions[2]]) if ans[questions[2]].replace('.', '', 1).isdigit() else 0
            mood = ans[questions[3]]
        except Exception as e:
            return jsonify({"done": True, "message": f"Veri kaydı sırasında hata: {str(e)}"})

        new_data = DailyData(
            user_id=flask_session["user_id"],
            date=date.today(),
            water_intake=water,
            steps=steps,
            sleep_hours=sleep,
            mood=mood
        )
        session.add(new_data)
        session.commit()
        flask_session.pop("answers", None)
        flask_session.pop("q_index", None)
        return jsonify({"done": True, "message": "Tüm cevaplar kaydedildi! Teşekkürler."})

    question = questions[q_index]
    flask_session["q_index"] = q_index + 1
    return jsonify({"done": False, "question": question})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
