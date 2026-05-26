"""
Inizializzazione dell'app Flask e configurazione principale.
Questo file crea l'applicazione, carica le estensioni e registra le route.
"""

from datetime import datetime
from functools import wraps
import os
import time

import jwt
import redis
import socket
import psutil
from flask import Flask, Blueprint, abort, g, jsonify, render_template, request
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from flask_socketio import SocketIO
from flasgger import Swagger
from rq import Queue
from sqlalchemy.exc import OperationalError

from extensions import db
from models import Category, Like
from services import (
    AdminService,
    ArticleService,
    AuthService,
    CategoryService,
    CommentService,
    LikeService,
    ProfileService,
)


def build_redis_connection(*, decode_responses: bool):
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis.from_url(redis_url, decode_responses=decode_responses)

    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=decode_responses,
    )


cache = build_redis_connection(decode_responses=True)
queue_connection = build_redis_connection(decode_responses=False)
queue = Queue(connection=queue_connection)

app = Flask(__name__)
print(">>> STO ESEGUENDO QUESTO app.py <<<")

socketio = SocketIO(app, message_queue=os.getenv("REDIS_URL", "redis://redis:6379/0"))


@app.route("/")
def index():
    """Renderizza la pagina principale dell'applicazione."""
    return render_template("index.html")


swagger = Swagger(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-fallback")
app.config["TESTING"] = os.getenv("TESTING", "0") == "1"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://Vincenzo:123456@db:3306/progetto_links",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["PROFILE_IMAGE_FOLDER"] = os.path.join("static", "immagini_profilo")
app.config["ALLOWED_IMAGE_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PROFILE_IMAGE_FOLDER"], exist_ok=True)

bcrypt = Bcrypt(app)
db.init_app(app)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    profile_name = db.Column(db.String(50), nullable=False)
    profile_image = db.Column(db.String(150), nullable=True, default='default.png')

    articles = db.relationship("Article", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    likes = db.relationship("Like", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship("Comment", backref="article", lazy=True)
    likes = db.relationship("Like", backref="article", lazy="dynamic", cascade="all, delete-orphan")

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


main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)


@main_bp.before_request
def require_auth_for_pages():
    return None


@main_bp.route("/")
def home_page():
    """Renderizza la home page del frontend."""
    return render_template("index.html")


@main_bp.route("/login")
def login_page():
    """Renderizza la pagina di accesso."""
    return render_template("login.html")


@main_bp.route("/register")
def register_page():
    """Renderizza la pagina di registrazione."""
    return render_template("register.html")


@main_bp.route("/articles")
def articles_page():
    """Renderizza la pagina che mostra gli articoli."""
    return render_template("articles.html")


@main_bp.route("/categories")
def categories_page():
    """Renderizza la pagina dedicata alle categorie."""
    return render_template("categories.html")


@main_bp.route("/dashboard")
def dashboard_page():
    """Renderizza la dashboard di monitoraggio del cluster."""
    return render_template("dashboard.html")


@main_bp.route("/profile/<username>")
def profile_page(username):
    """Renderizza la pagina profilo dell'utente richiesto."""
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404)
    return render_template("profilo.html", user=user)


@api_bp.route("/register", methods=["POST"])
def register():
    """
    Registrazione nuovo utente
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: UserRegistration
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              example: vincenzo_dev
            email:
              type: string
              example: vincenzo@test.it
            password:
              type: string
              example: password123
            profile_name:
              type: string
              example: Vincenzo Apulia
    responses:
      201:
        description: Utente creato con successo
      400:
        description: Dati mancanti o utente gia esistente
    """
    payload, status_code = AuthService.register_user(request.get_json(), bcrypt, queue)
    return jsonify(payload), status_code


@api_bp.route("/login", methods=["POST"])
def login():
    """
    Autentica un utente e restituisce un token JWT
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login effettuato con successo
      400:
        description: Dati mancanti o non validi
      401:
        description: Password errata
      404:
        description: Utente non trovato
    """
    payload, status_code = AuthService.login_user(
        request.get_json(silent=True),
        bcrypt,
        app.config["SECRET_KEY"],
    )
    return jsonify(payload), status_code


@api_bp.route("/logout", methods=["POST"])
@login_required_api
def logout():
    """
    Esegue il logout logico dell'utente autenticato
    ---
    tags:
      - Auth
    responses:
      200:
        description: Logout effettuato
      401:
        description: Token mancante o non valido
    """
    return jsonify({"message": "Logout effettuato"}), 200


@api_bp.route("/me", methods=["GET"])
@login_required_api
def me():
    """
    Restituisce i dati dell'utente autenticato
    ---
    tags:
      - Auth
    responses:
      200:
        description: Dati utente recuperati con successo
      401:
        description: Token mancante o non valido
    """
    payload, status_code = AuthService.current_user_payload(g.current_user)
    return jsonify(payload), status_code


@api_bp.route("/change-password", methods=["POST"])
@login_required_api
def change_password():
    """
    Aggiorna la password dell'utente autenticato
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            current_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Password aggiornata con successo
      400:
        description: Dati mancanti o non validi
      401:
        description: Password attuale errata o token non valido
    """
    payload, status_code = AuthService.change_password(
        g.current_user,
        request.get_json(silent=True),
        bcrypt,
    )
    return jsonify(payload), status_code


@api_bp.route("/profile/<username>", methods=["POST"])
@login_required_api
def update_profile(username):
    """
    Aggiorna il profilo di un utente
    ---
    tags:
      - Profile
    parameters:
      - name: username
        in: path
        type: string
        required: true
        description: Username dell'utente da aggiornare
      - name: profile_name
        in: formData
        type: string
        required: true
        description: Nuovo nome profilo
      - name: profile_image
        in: formData
        type: file
        required: false
        description: Immagine del profilo
    responses:
      200:
        description: Profilo aggiornato con successo
      400:
        description: Dati profilo non validi
      403:
        description: Utente non autorizzato
      404:
        description: Utente non trovato
    """
    payload, status_code = ProfileService.update_profile(
        username,
        g.current_user,
        request.form,
        request.files,
        app.config,
    )
    return jsonify(payload), status_code


@api_bp.route("/articles", methods=["GET"])
def get_articles():
    """
    Restituisce la lista degli articoli
    ---
    tags:
      - Articles
    parameters:
      - name: category_id
        in: query
        type: integer
        required: false
        description: ID della categoria per filtrare gli articoli
    responses:
      200:
        description: Lista articoli recuperata con successo
    """
    payload, status_code = ArticleService.get_articles(
        request.args.getlist("category_id", type=int),
        cache,
    )
    return jsonify(payload), status_code


@api_bp.route("/articles", methods=["POST"])
@login_required_api
def create_article():
    """
    Crea un nuovo articolo
    ---
    tags:
      - Articles
    consumes:
      - multipart/form-data
    parameters:
      - name: title
        in: formData
        type: string
        required: true
        description: Titolo dell'articolo (min 5 car.)
      - name: content
        in: formData
        type: string
        required: true
        description: Contenuto dell'articolo (min 10 car.)
      - name: category_id
        in: formData
        type: integer
        required: false
        description: ID della categoria
      - name: category_name
        in: formData
        type: string
        required: false
        description: Nome di una nuova categoria
      - name: image
        in: formData
        type: file
        required: false
        description: Immagine dell'articolo
    responses:
      201:
        description: Articolo creato con successo
      400:
        description: Errore di validazione
    """
    payload, status_code = ArticleService.create_article(
        request.form,
        request.files,
        g.current_user,
        cache,
        app.config,
    )
    return jsonify(payload), status_code


@api_bp.route("/articles/<int:article_id>", methods=["PUT"])
@login_required_api
def update_article(article_id):
    """
    Aggiorna un articolo esistente
    ---
    tags:
      - Articles
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: ID dell'articolo da aggiornare
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            title:
              type: string
            content:
              type: string
            category_id:
              type: integer
            category_name:
              type: string
    responses:
      200:
        description: Articolo aggiornato con successo
      401:
        description: Token mancante o non valido
      403:
        description: Utente non autorizzato
      404:
        description: Articolo o categoria non trovati
    """
    payload, status_code = ArticleService.update_article(
        article_id,
        request.get_json(),
        g.current_user,
        cache,
    )
    return jsonify(payload), status_code


@api_bp.route("/articles/<int:article_id>", methods=["DELETE"])
@login_required_api
def delete_article(article_id):
    """
    Elimina un articolo esistente
    ---
    tags:
      - Articles
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: ID dell'articolo da eliminare
    responses:
      200:
        description: Articolo eliminato con successo
      401:
        description: Token mancante o non valido
      403:
        description: Utente non autorizzato
      404:
        description: Articolo non trovato
    """
    ArticleService.delete_article(article_id, g.current_user, cache)
    return jsonify({"message": "Articolo eliminato"})


@api_bp.route("/articles/<int:article_id>/comments", methods=["GET"])
def get_comments(article_id):
    """
    Restituisce i commenti di un articolo
    ---
    tags:
      - Comments
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: ID dell'articolo
    responses:
      200:
        description: Lista commenti recuperata con successo
      404:
        description: Articolo non trovato
    """
    payload, status_code = CommentService.get_comments(article_id)
    return jsonify(payload), status_code


@api_bp.route("/articles/<int:article_id>/comments", methods=["POST"])
@login_required_api
def add_comment(article_id):
    """
    Aggiunge un commento a un articolo
    ---
    tags:
      - Comments
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          id: Comment
          required:
            - content
          properties:
            content:
              type: string
              description: Contenuto del commento
              example: "Bellissimo articolo!"
    responses:
      201:
        description: Commento aggiunto con successo
      400:
        description: Contenuto mancante
    """
    data = request.get_json()
    payload, status_code = CommentService.add_comment(
        article_id,
        data,
        g.current_user,
    )
    return jsonify(payload), status_code


@api_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@login_required_api
def delete_comment(comment_id):
    """
    Elimina un commento esistente
    ---
    tags:
      - Comments
    parameters:
      - name: comment_id
        in: path
        type: integer
        required: true
        description: ID del commento da eliminare
    responses:
      200:
        description: Commento eliminato con successo
      401:
        description: Token mancante o non valido
      403:
        description: Utente non autorizzato
      404:
        description: Commento non trovato
    """
    payload, status_code = CommentService.delete_comment(comment_id, g.current_user)
    return jsonify(payload), status_code


@api_bp.route("/comments/<int:comment_id>", methods=["PUT"])
@login_required_api
def update_comment(comment_id):
    """
    Aggiorna un commento esistente
    ---
    tags:
      - Comments
    parameters:
      - name: comment_id
        in: path
        type: integer
        required: true
        description: ID del commento da aggiornare
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            content:
              type: string
    responses:
      200:
        description: Commento aggiornato con successo
      401:
        description: Token mancante o non valido
      403:
        description: Utente non autorizzato
      404:
        description: Commento non trovato
    """
    payload, status_code = CommentService.update_comment(
        comment_id,
        request.get_json(),
        g.current_user,
    )
    return jsonify(payload), status_code


@api_bp.route("/articles/<int:article_id>/likes", methods=["GET"])
def get_likes(article_id):
    """
    Restituisce il numero di like di un articolo
    ---
    tags:
      - Likes
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: ID dell'articolo
    responses:
      200:
        description: Conteggio like recuperato con successo
      404:
        description: Articolo non trovato
    """
    payload, status_code = LikeService.get_likes(article_id)
    return jsonify(payload), status_code


@api_bp.route("/articles/<int:article_id>/likes", methods=["POST"])
@login_required_api
def add_like(article_id):
    """
    Aggiunge un like a un articolo
    ---
    tags:
      - Likes
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: ID dell'articolo
    responses:
      201:
        description: Like aggiunto con successo
      401:
        description: Token mancante o non valido
      404:
        description: Articolo non trovato
      409:
        description: Like gia presente
    """
    payload, status_code = LikeService.add_like(article_id, g.current_user)
    return jsonify(payload), status_code


@api_bp.route("/articles/<int:article_id>/likes", methods=["DELETE"])
@login_required_api
def remove_like(article_id):
    """
    Rimuove un like da un articolo
    ---
    tags:
      - Likes
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: ID dell'articolo
    responses:
      200:
        description: Like rimosso con successo
      401:
        description: Token mancante o non valido
      404:
        description: Articolo o like non trovato
    """
    payload, status_code = LikeService.remove_like(article_id, g.current_user)
    return jsonify(payload), status_code


@api_bp.route("/categories", methods=["GET"])
def list_categories():
    """
    Restituisce l'elenco delle categorie
    ---
    tags:
      - Categories
    responses:
      200:
        description: Lista categorie recuperata con successo
    """
    payload, status_code = CategoryService.list_categories()
    return jsonify(payload), status_code


@api_bp.route("/categories", methods=["POST"])
@login_required_api
def create_category():
    """
    Crea una nuova categoria
    ---
    tags:
      - Categories
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
    responses:
      201:
        description: Categoria creata con successo
      400:
        description: Nome categoria mancante
      401:
        description: Token mancante o non valido
      409:
        description: Categoria gia esistente
    """
    payload, status_code = CategoryService.create_category(request.get_json())
    return jsonify(payload), status_code


@api_bp.route("/categories/<int:category_id>", methods=["PUT"])
@login_required_api
@admin_required
def update_category(category_id):
    """
    Aggiorna una categoria esistente
    ---
    tags:
      - Categories
    parameters:
      - name: category_id
        in: path
        type: integer
        required: true
        description: ID della categoria da aggiornare
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
    responses:
      200:
        description: Categoria aggiornata con successo
      400:
        description: Nome categoria mancante
      401:
        description: Token mancante o non valido
      403:
        description: Permessi insufficienti
      404:
        description: Categoria non trovata
      409:
        description: Categoria gia esistente
    """
    payload, status_code = CategoryService.update_category(category_id, request.get_json())
    return jsonify(payload), status_code


@api_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@login_required_api
@admin_required
def delete_category(category_id):
    """
    Elimina una categoria esistente
    ---
    tags:
      - Categories
    parameters:
      - name: category_id
        in: path
        type: integer
        required: true
        description: ID della categoria da eliminare
    responses:
      200:
        description: Categoria eliminata con successo
      401:
        description: Token mancante o non valido
      403:
        description: Permessi insufficienti
      404:
        description: Categoria non trovata
    """
    payload, status_code = CategoryService.delete_category(category_id)
    return jsonify(payload), status_code


@api_bp.route("/make-me-admin", methods=["POST"])
@login_required_api
def make_me_admin():
    """
    Promuove l'utente autenticato a amministratore
    ---
    tags:
      - Admin
    responses:
      200:
        description: Utente promosso a admin
      401:
        description: Token mancante o non valido
    """
    payload, status_code = AdminService.make_me_admin(g.current_user)
    return jsonify(payload), status_code


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


@app.route("/api/stats")
def get_stats():
    # conta quanti articoli ci sono nel db
    total_articles = Article.query.count()

    # conta quanti commenti totali ci sono
    total_comments = Comment.query.count()

    # conta il numero totale di like (contando le righe nella tabella Like)
    total_likes = Like.query.count()

    return jsonify({
        "articles": total_articles,
        "comments": total_comments,
        "likes": total_likes,
        "server_id": socket.gethostname()
    })


@app.route("/api/health-check")
def health_check():
    return {
      "server_id": socket.gethostname(),
      "cpu_usage": psutil.cpu_percent(),
      "memory_usage": psutil.virtual_memory().percent,
      "status": "online"
    }


@app.errorhandler(404)
def page_not_found(e):
  # restituisce il template 404.html
  return render_template("404.html"), 404




if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
