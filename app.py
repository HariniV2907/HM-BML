from flask import Flask, render_template, request, redirect, url_for, session
import qrcode, os, hashlib, random, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

users = []
otp_storage = {}
pending_requests = {}
approved_scanners = {}

qr_host = "http://127.0.0.1:5000"
USER_FILE = "users.json"
RECORD_FILE = "records.json"

def load_users():
    global users
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            users.extend(json.load(f))

def save_users():
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_records():
    if os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, "r") as f:
            return json.load(f)
    return {}

def save_records():
    with open(RECORD_FILE, "w") as f:
        json.dump(records, f, indent=2)

records = load_records()
load_users()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get("email")
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp
    return {"message": f"OTP sent successfully: {otp}"}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data["email"]

    if otp_storage.get(email) != data["otp"]:
        return {"message": "Invalid OTP!"}, 400

    if any(u['email'] == email for u in users):
        return {"message": "Email already registered!"}, 400

    hashed_password = hashlib.sha256(data["password"].encode()).hexdigest()

    user = {
        "name": data["name"],
        "age": data["age"],
        "email": email,
        "phone": data["phone"],
        "designation": data["designation"],
        "password": hashed_password
    }

    users.append(user)
    save_users()

    qr_url = f"{qr_host}/scan/{email}"
    qr = qrcode.make(qr_url)
    qr_path = f"static/qrcodes/{email}.png"
    os.makedirs("static/qrcodes", exist_ok=True)
    qr.save(qr_path)

    return {"message": "Registered successfully!", "qrCode": qr_path}

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get("email")
    entered_password = request.form.get("password")
    hashed_input = hashlib.sha256(entered_password.encode()).hexdigest()

    for user in users:
        if user["email"] == email:
            if user["password"] == hashed_input:
                session["user"] = email
                return redirect(url_for("profile", email=email))
            else:
                return "Incorrect password", 403
    return "User not found", 404

@app.route('/profile/<email>')
def profile(email):
    if session.get("user") != email:
        return "Unauthorized", 403

    user = next((u for u in users if u["email"] == email), None)
    user_records = records.get(email, [])
    requests = pending_requests.get(email, [])
    return render_template("profile.html", user=user, requests=requests, records=user_records)

@app.route('/scan/<email>', methods=["GET", "POST"])
def scan(email):
    if request.method == "POST":
        scanner = {
            "name": request.form["name"],
            "email": request.form["email"]
        }
        pending_requests.setdefault(email, []).append(scanner)
        approved_scanners[(email, scanner["email"])] = False
        return redirect(url_for("scan", email=email, scanner=scanner["email"]))

    scanner_email = request.args.get("scanner")
    return render_template("scanner_request.html", email=email, scanner_email=scanner_email)

@app.route('/approve/<owner>/<scanner_email>')
def approve(owner, scanner_email):
    approved_scanners[(owner, scanner_email)] = True
    return redirect(url_for("profile", email=owner))

@app.route('/check-access/<owner>/<scanner_email>')
def check_access(owner, scanner_email):
    return {"approved": approved_scanners.get((owner, scanner_email), False)}

@app.route('/shared-profile/<owner>/<scanner_email>', methods=["GET", "POST"])
def shared_profile(owner, scanner_email):
    if not approved_scanners.get((owner, scanner_email)):
        return "Access Denied", 403

    user = next((u for u in users if u["email"] == owner), None)
    doctor = next((u for u in users if u["email"] == scanner_email), None)

    if request.method == "POST" and doctor and doctor["designation"] == "doctor":
        record = {
            "complaint": request.form["complaint"],
            "diagnosis": request.form["diagnosis"],
            "treatment": request.form["treatment"],
            "prescription": request.form.get("prescription", ""),
            "next_visit": request.form["next_visit"],
            "added_by": doctor["email"],
            "date": str(datetime.now())
        }
        records.setdefault(owner, []).append(record)
        save_records()
        return redirect(url_for("shared_profile", owner=owner, scanner_email=scanner_email))

    patient_records = records.get(owner, [])
    return render_template("shared_profile.html", user=user, doctor=doctor, records=patient_records)

if __name__ == '__main__':
    app.run(debug=True)
