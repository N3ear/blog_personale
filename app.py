from flask import Flask, jsonify, request, render_template, Blueprint, redirect, url_for, abort, g
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import uuid
import time
import re
import jwt
from sqlalchemy.exc import OperationalError

# --- APP ---
app = Flask(__name__)
print(">>> STO ESEGUENDO QUESTO app.py <<<")

# --- CONFIG ---
app.config["SECRET_KEY"] = "questaèunachiavesecret123"
app.config["TESTING"] = os.getenv("TESTING", "0") == "1"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "mysql+pymysql://Vincenzo:123456@db:3306/progetto_links")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["PROFILE_IMAGE_FOLDER"] = os.path.join("static", "immagini_profilo")
app.config["ALLOWED_IMAGE_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PROFILE_IMAGE_FOLDER"], exist_ok=True)

# --- EXTENSIONS ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
# =====================================================
# MODELS
# =====================================================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    articles = db.relationship("Article", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    
    
    profile_name = db.Column(db.String(50), nullable=False)
    profile_image = db.Column(db.String(255), default="default.png")



    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship("Comment", backref="article", lazy=True)

    def __repr__(self):
        return f"Article('{self.title}')"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Comment('{self.content[:20]}...')"


# =====================================================
# DECORATORS
# =====================================================

def login_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token mancante"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token scaduto"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token non valido"}), 401

        user = db.session.get(User, payload.get("user_id"))
        if not user:
            return jsonify({"error": "Utente non trovato"}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not getattr(g, "current_user", None):
            return jsonify({"error": "Utente non loggato"}), 401
        if not g.current_user.is_admin:
            return jsonify({"error": "Solo admin"}), 403
        return f(*args, **kwargs)
    return decorated


# =====================================================
# BLUEPRINTS
# =====================================================

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)


# =====================================================
# HTML ROUTES (FRONTEND)
# =====================================================

@main_bp.before_request
def require_auth_for_pages():
    return None


@main_bp.route("/")
def home_page():
    return render_template("index.html")


@main_bp.route("/login")
def login_page():
    return render_template("login.html")


@main_bp.route("/register")
def register_page():
    return render_template("register.html")


@main_bp.route("/articles")
def articles_page():
    return render_template("articles.html")


@main_bp.route("/profile/<username>")
def profile_page(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404)
    return render_template("profilo.html", user=user)


# =====================================================
# API AUTH
# =====================================================

@api_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON mancante"}), 400

    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Dati mancanti"}), 400
    
    if not isinstance(data["username"], str):
        return jsonify({"error": "username deve essere una stringa"}), 400
    
    if not isinstance(data["email"], str):
        return jsonify({"error": "email deve essere una stringa"}), 400
    
    username = data["username"].strip()
    email = data["email"].strip().lower()

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"error": "email non valida"}), 400
    
    if not re.match(r"^[A-Za-z0-9_]+$", username):
        return jsonify({"error": "username puo contenere solo lettere, numeri e underscore"}), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify({"error": "username deve essere tra 3 e 20 caratteri"}), 400
    
    if username == "" or email == "":
        return jsonify({"error": "username e email non possono essere vuoti"}), 400

    # 1️ Leggo profile_name
    profile_name = data.get("profile_name", username)
    
    if not isinstance(profile_name, str):
        return jsonify({"error": "profile_name deve essere una stringa"}), 400
    
    profile_name = profile_name.strip()
    
    if profile_name == "":
        return jsonify({"error": "profile_name non puo essere vuoto"}), 400
    
    profile_name = profile_name.title()
    
    if len(profile_name) > 50:
        return jsonify({"error": "profile_name troppo lungo"}), 400
    

    # 2️ Controllo duplicati
    if User.query.filter(
        (User.username == username) |
        (User.email == email)
    ).first():
        return jsonify({"error": "Username o email gia esistenti"}), 400

    # 3️ Hash password
    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    # 4️ Creo l’utente
    user = User(
        username=username,
        email=email,
        password=hashed_pw,
        profile_name=profile_name,
        profile_image="default.png"
    )
    # 5️ Salvo
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Utente registrato"}), 201


@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON mancante"}), 400

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "username e password obbligatori"}), 400

    username = username.strip()
    if not username or not password:
        return jsonify({"error": "username e password obbligatori"}), 400

    user = User.query.filter_by(username=username).first()
    if user is None:
        return jsonify({"error": "utente inesistente"}), 404

    try:
        password_ok = bcrypt.check_password_hash(user.password, password)
    except (ValueError, TypeError):
        return jsonify({"error": "password errata"}), 401

    if not password_ok:
        return jsonify({"error": "password errata"}), 401

    payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({
        "message": "Login effettuato",
        "token": token
    }), 200


@api_bp.route("/logout", methods=["POST"])
@login_required_api
def logout():
    return jsonify({"message": "Logout effettuato"}), 200


@api_bp.route("/me", methods=["GET"])
@login_required_api
def me():
    return jsonify({
        "id": g.current_user.id,
        "username": g.current_user.username,
        "email": g.current_user.email,
        "is_admin": g.current_user.is_admin
    })


@api_bp.route("/profile/<username>", methods=["POST"])
@login_required_api
def update_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404

    if g.current_user.id != user.id and not g.current_user.is_admin:
        return jsonify({"error": "Non autorizzato"}), 403

    profile_name = request.form.get("profile_name", "").strip()
    if not profile_name:
        return jsonify({"error": "Il nome profilo non puo essere vuoto"}), 400
    if len(profile_name) > 50:
        return jsonify({"error": "Il nome profilo deve essere massimo 50 caratteri"}), 400

    user.profile_name = profile_name.title()

    profile_image = request.files.get("profile_image")
    if profile_image and profile_image.filename:
        safe_name = secure_filename(profile_image.filename)
        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        if ext not in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
            return jsonify({"error": "Formato immagine non supportato"}), 400

        image_filename = f"{uuid.uuid4().hex}.{ext}"
        profile_image.save(os.path.join(app.config["PROFILE_IMAGE_FOLDER"], image_filename))
        user.profile_image = image_filename

    db.session.commit()
    return jsonify({"message": "Profilo aggiornato", "profile_name": user.profile_name, "profile_image": user.profile_image}), 200


# =====================================================
# API ARTICLES
# =====================================================

@api_bp.route("/articles", methods=["GET"])
def get_articles():
    articles = Article.query.all()
    return jsonify([
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "image": a.image,
            "author": a.author.username,
            "author_id": a.author_id,
            "date_posted": a.date_posted.strftime("%Y-%m-%d %H:%M")
        } for a in articles
    ])


@api_bp.route("/articles", methods=["POST"])
@login_required_api
def create_article():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    image = request.files.get("image")

    if not title or not content:
        return jsonify({"error": "Dati mancanti"}), 400

    image_filename = None
    if image and image.filename:
        safe_name = secure_filename(image.filename)
        if not safe_name:
            return jsonify({"error": "Nome file non valido"}), 400

        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        if ext not in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
            return jsonify({"error": "Formato immagine non supportato"}), 400

        image_filename = f"{uuid.uuid4().hex}.{ext}"
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

    article = Article(
        title=title,
        content=content,
        image=image_filename,
        author_id=g.current_user.id
    )

    db.session.add(article)
    db.session.commit()

    return jsonify({"message": "Articolo creato", "id": article.id}), 201


@api_bp.route("/articles/<int:article_id>", methods=["PUT"])
@login_required_api
def update_article(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        abort(404)

    if article.author_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Non autorizzato"}), 403

    data = request.get_json()
    article.title = data.get("title", article.title)
    article.content = data.get("content", article.content)

    db.session.commit()
    return jsonify({"message": "Articolo aggiornato"})


@api_bp.route("/articles/<int:article_id>", methods=["DELETE"])
@login_required_api
def delete_article(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        abort(404)

    if article.author_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Non autorizzato"}), 403

    Comment.query.filter_by(article_id=article.id).delete()
    db.session.delete(article)
    db.session.commit()

    return jsonify({"message": "Articolo eliminato"})


# =====================================================
# API COMMENTS
# =====================================================

@api_bp.route("/articles/<int:article_id>/comments", methods=["GET"])
def get_comments(article_id):
    if not db.session.get(Article, article_id):
        abort(404)

    comments = Comment.query.filter_by(article_id=article_id)\
        .order_by(Comment.date_posted.desc()).all()

    return jsonify([
        {
            "id": c.id,
            "content": c.content,
            "author": c.author.username,
            "author_id": c.author_id,
            "date_posted": c.date_posted.strftime("%Y-%m-%d %H:%M")
        } for c in comments
    ])


@api_bp.route("/articles/<int:article_id>/comments", methods=["POST"])
@login_required_api
def add_comment(article_id):
    if not db.session.get(Article, article_id):
        abort(404)
    data = request.get_json()

    if not data or not data.get("content"):
        return jsonify({"error": "Contenuto mancante"}), 400

    comment = Comment(
        content=data["content"],
        article_id=article_id,
        author_id=g.current_user.id
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({"message": "Commento aggiunto"}), 201


@api_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@login_required_api
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        abort(404)

    if comment.author_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Non autorizzato"}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": "Commento eliminato"})


@api_bp.route("/comments/<int:comment_id>", methods=["PUT"])
@login_required_api
def update_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        abort(404)

    if comment.author_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Non autorizzato"}), 403

    data = request.get_json()
    comment.content = data.get("content", comment.content)

    db.session.commit()
    return jsonify({"message": "Commento aggiornato"})


# =====================================================
# DEV ONLY – CREA ADMIN
# =====================================================

@api_bp.route("/make-me-admin", methods=["POST"])
@login_required_api
def make_me_admin():
    g.current_user.is_admin = True
    db.session.commit()
    return jsonify({"message": "Ora sei admin"})


# =====================================================
# START
# =====================================================

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix="/api")

with app.app_context():
    if app.config.get("TESTING"):
        db.create_all()
    else:
        max_attempts = 30
        for attempt in range(1, max_attempts + 1):
            try:
                db.create_all()
                break
            except OperationalError:
                if attempt == max_attempts:
                    raise
                time.sleep(2)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)



