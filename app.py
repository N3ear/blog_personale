from flask import Flask, jsonify, request, render_template, Blueprint, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user
)
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime

# --- APP ---
app = Flask(__name__)

# --- CONFIG ---
app.config["SECRET_KEY"] = "questaèunachiavesecret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- EXTENSIONS ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "main.login_page"  # ✔ corretto
login_manager.login_message_category = "info"

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

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
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
# LOGIN MANAGER
# =====================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================================================
# DECORATORS
# =====================================================

def login_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Utente non loggato"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Utente non loggato"}), 401
        if not current_user.is_admin:
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
    if request.endpoint in ("main.register_page", "main.login_page", "static"):
        return None
    if not current_user.is_authenticated:
        return redirect(url_for("main.register_page"))


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

    if User.query.filter(
        (User.username == data["username"]) |
        (User.email == data["email"])
    ).first():
        return jsonify({"error": "Username o email già esistenti"}), 400

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(
        username=data["username"],
        email=data["email"],
        password=hashed_pw
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Utente registrato"}), 201


@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON mancante"}), 400

    user = User.query.filter_by(username=data.get("username")).first()
    if user and bcrypt.check_password_hash(user.password, data.get("password")):
        login_user(user)
        return jsonify({"message": "Login effettuato"}), 200

    return jsonify({"error": "Credenziali errate"}), 401


@api_bp.route("/logout", methods=["POST"])
@login_required_api
def logout():
    logout_user()
    return jsonify({"message": "Logout effettuato"}), 200


@api_bp.route("/me", methods=["GET"])
@login_required_api
def me():
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    })


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
            "author": a.author.username,
            "author_id": a.author_id,
            "date_posted": a.date_posted.strftime("%Y-%m-%d %H:%M")
        } for a in articles
    ])


@api_bp.route("/articles", methods=["POST"])
@login_required_api
def create_article():
    data = request.get_json()
    if not data or not data.get("title") or not data.get("content"):
        return jsonify({"error": "Dati mancanti"}), 400

    article = Article(
        title=data["title"],
        content=data["content"],
        author_id=current_user.id
    )

    db.session.add(article)
    db.session.commit()

    return jsonify({"message": "Articolo creato", "id": article.id}), 201


@api_bp.route("/articles/<int:article_id>", methods=["PUT"])
@login_required_api
def update_article(article_id):
    article = Article.query.get_or_404(article_id)

    if article.author_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Non autorizzato"}), 403

    data = request.get_json()
    article.title = data.get("title", article.title)
    article.content = data.get("content", article.content)

    db.session.commit()
    return jsonify({"message": "Articolo aggiornato"})


@api_bp.route("/articles/<int:article_id>", methods=["DELETE"])
@login_required_api
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)

    if article.author_id != current_user.id and not current_user.is_admin:
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
    Article.query.get_or_404(article_id)

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
    Article.query.get_or_404(article_id)
    data = request.get_json()

    if not data or not data.get("content"):
        return jsonify({"error": "Contenuto mancante"}), 400

    comment = Comment(
        content=data["content"],
        article_id=article_id,
        author_id=current_user.id
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({"message": "Commento aggiunto"}), 201


@api_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@login_required_api
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.author_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Non autorizzato"}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": "Commento eliminato"})


@api_bp.route("/comments/<int:comment_id>", methods=["PUT"])
@login_required_api
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.author_id != current_user.id and not current_user.is_admin:
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
    current_user.is_admin = True
    db.session.commit()
    return jsonify({"message": "Ora sei admin"})


# =====================================================
# START
# =====================================================

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix="/api")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
