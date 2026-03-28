import os
from flask import Flask, request, redirect, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "owlyx_saas_secret"

# ---------------- CLOUD DATABASE (POSTGRES OR FALLBACK SQLITE) ----------------
DB_URL = os.environ.get("DATABASE_URL")

if DB_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "owlyx.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20)) # admin / client


class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200))
    result = db.Column(db.String(500))
    user_id = db.Column(db.Integer)


# ---------------- INIT ----------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        db.session.add(User(
            username="admin",
            password=generate_password_hash("owlyx@execute"),
            role="admin"
        ))
        db.session.commit()


# ---------------- UI STYLE ----------------
STYLE = """
<style>
body { background:#0a0a0a; color:white; font-family:Arial; }
h1 { color:#ff2b2b; }
button { background:#ff2b2b; color:white; padding:10px; border:none; margin:5px; cursor:pointer; }
input { padding:8px; margin:5px; }
.card { background:#111; padding:12px; margin:10px; border-left:4px solid red; }
</style>
"""


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        user = User.query.filter_by(username=u).first()

        if user and check_password_hash(user.password, p):
            session["uid"] = user.id
            session["role"] = user.role
            session["username"] = user.username
            return redirect("/admin" if user.role == "admin" else "/client")

    return STYLE + """
    <h1>⚡ OWLYX SaaS LOGIN</h1>
    <form method='post'>
        <input name='username' placeholder='username'><br>
        <input name='password' type='password' placeholder='password'><br>
        <button>Login</button>
    </form>
    """


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "Access Denied"

    users = User.query.all()
    targets = Target.query.all()

    return STYLE + render_template_string("""
    <h1>⚡ OWLYX ADMIN SAAS</h1>

    <div class="card">
        <h3>Create Client</h3>
        <form action="/create_client" method="post">
            <input name="username" placeholder="client id">
            <input name="password" placeholder="password">
            <button>Create</button>
        </form>
    </div>

    <div class="card">
        <h3>Auto Scan</h3>
        <a href="/scan"><button>Run Scan</button></a>
    </div>

    <h3>Users</h3>
    {% for u in users %}
        <div class="card">{{u.username}} - {{u.role}}</div>
    {% endfor %}

    <h3>Targets</h3>
    {% for t in targets %}
        <div class="card">{{t.url}} → {{t.result}}</div>
    {% endfor %}
    """, users=users, targets=targets)


# ---------------- CREATE CLIENT ----------------
@app.route("/create_client", methods=["POST"])
def create_client():
    if session.get("role") != "admin":
        return "Denied"

    u = request.form["username"]
    p = request.form["password"]

    if not User.query.filter_by(username=u).first():
        db.session.add(User(
            username=u,
            password=generate_password_hash(p),
            role="client"
        ))
        db.session.commit()

    return redirect("/admin")


# ---------------- SCAN ----------------
def scan(site):
    return "SAFE - OWLYX AI SCAN"


@app.route("/scan")
def scan_all():
    if session.get("role") != "admin":
        return "Denied"

    clients = User.query.filter_by(role="client").all()

    for c in clients:
        db.session.add(Target(
            url="example.com",
            result=scan("example.com"),
            user_id=c.id
        ))

    db.session.commit()
    return redirect("/admin")


# ---------------- CLIENT DASHBOARD ----------------
@app.route("/client")
def client():
    if session.get("role") != "client":
        return "Denied"

    data = Target.query.filter_by(user_id=session["uid"]).all()

    return STYLE + render_template_string("""
    <h1>⚡ OWLYX CLIENT DASHBOARD</h1>

    <div class="card">
        <h3>Reports</h3>
        {% for d in data %}
            <p>{{d.url}} → {{d.result}}</p>
        {% endfor %}
    </div>

    <div class="card">
        <h3>💳 Subscription</h3>
        <p>Upgrade to Pro Plan</p>

        <!-- Razorpay placeholder -->
        <form action="/pay" method="post">
            <button>Pay ₹99</button>
        </form>
    </div>
    """, data=data)


# ---------------- PAYMENT (PLACEHOLDER FOR RAZORPAY) ----------------
@app.route("/pay", methods=["POST"])
def pay():
    if session.get("role") != "client":
        return "Denied"

    # Later: integrate Razorpay here
    return "<h2>Payment Gateway Coming (Razorpay Integration Next Step)</h2>"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
app.run(debug=True)