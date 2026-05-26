import json
import os
import re
import uuid
from utils import compress_image

from datetime import datetime, timedelta

import jwt
from flask import abort
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from extensions import db

from marshmallow import ValidationError
from schemas import ArticleSchema, RegisterSchema, ProfileSchema

# Inizializza gli schemi
article_schema = ArticleSchema()
register_schema = RegisterSchema()
profile_schema = ProfileSchema()



class BaseService:
    @staticmethod
    def get_model(model_name: str):
        """Recupera un modello SQLAlchemy registrato per nome."""
        model = db.Model._sa_registry._class_registry.get(model_name)
        if model is None or isinstance(model, str):
            raise RuntimeError(f"Modello non trovato: {model_name}")
        return model


class AuthService(BaseService):
    @staticmethod
    def register_user(data, bcrypt, queue):
        User = AuthService.get_model("User")

        # Valida i dati con Marshmallow
        try:
            valid_data = register_schema.load(data or {})
        except ValidationError as err:
            error_msgs = []
            for field, msgs in err.messages.items():
                if isinstance(msgs, list):
                    error_msgs.append(f"{field}: {', '.join(msgs)}")
                else:
                    error_msgs.append(f"{field}: {msgs}")
            return {"error": " | ".join(error_msgs)}, 400

        username = valid_data["username"].strip()
        email = valid_data["email"].strip().lower()
        password = valid_data["password"]

        profile_name = (data or {}).get("profile_name", username)
        if not isinstance(profile_name, str):
            profile_name = str(profile_name)
        profile_name = profile_name.strip()
        if not profile_name:
            profile_name = username
        profile_name = profile_name.title()
        if len(profile_name) > 50:
            return {"error": "profile_name troppo lungo"}, 400

        if User.query.filter((User.username == username) | (User.email == email)).first():
            return {"error": "Username o email gia esistenti"}, 400

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            username=username,
            email=email,
            password=hashed_pw,
            profile_name=profile_name,
            profile_image="default.png",
        )
        db.session.add(user)
        db.session.commit()

        from tasks import send_welcome_email

        queue.enqueue(send_welcome_email, user.email, user.username)
        print(f"job aggiunto alla coda per {user.email}")
        return {"message": "utente registrato, email in arrivo!"}, 201

    @staticmethod
    def login_user(data, bcrypt, secret_key):
        User = AuthService.get_model("User")

        if not isinstance(data, dict):
            return {"error": "JSON mancante"}, 400

        username = data.get("username")
        password = data.get("password")
        if not isinstance(username, str) or not isinstance(password, str):
            return {"error": "username e password obbligatori"}, 400

        username = username.strip()
        if not username or not password:
            return {"error": "username e password obbligatori"}, 400

        user = User.query.filter_by(username=username).first()
        if user is None:
            return {"error": "utente inesistente"}, 404

        try:
            password_ok = bcrypt.check_password_hash(user.password, password)
        except (ValueError, TypeError):
            return {"error": "password errata"}, 401

        if not password_ok:
            return {"error": "password errata"}, 401

        payload = {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return {"message": "Login effettuato", "token": token}, 200

    @staticmethod
    def current_user_payload(current_user):
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin,
        }, 200

    @staticmethod
    def change_password(current_user, data, bcrypt):
        if not isinstance(data, dict):
            return {"error": "JSON mancante"}, 400

        current_password = data.get("current_password")
        new_password = data.get("new_password")
        if not isinstance(current_password, str) or not isinstance(new_password, str):
            return {"error": "password obbligatorie"}, 400

        current_password = current_password.strip()
        new_password = new_password.strip()
        if not current_password or not new_password:
            return {"error": "password obbligatorie"}, 400

        try:
            password_ok = bcrypt.check_password_hash(current_user.password, current_password)
        except (ValueError, TypeError):
            return {"error": "password attuale errata"}, 401

        if not password_ok:
            return {"error": "password attuale errata"}, 401

        current_user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.session.commit()
        return {"message": "Password aggiornata"}, 200


class ProfileService(BaseService):
    @staticmethod
    def update_profile(username, current_user, form, files, app_config):
        User = ProfileService.get_model("User")

        user = User.query.filter_by(username=username).first()
        if not user:
            return {"error": "Utente non trovato"}, 404
        if current_user.id != user.id and not current_user.is_admin:
            return {"error": "Non autorizzato"}, 403

        # Validazione con Marshmallow (include il controllo dell'immagine)
        try:
            data_to_validate = form.to_dict()
            if files.get("profile_image"):
                data_to_validate["profile_image"] = files["profile_image"]
            
            valid_data = profile_schema.load(data_to_validate)
        except ValidationError as err:
            return {"error": err.messages}, 400

        user.profile_name = valid_data["profile_name"].title()

        profile_image = valid_data.get("profile_image")
        if profile_image and profile_image.filename:
            image_filename = f"{uuid.uuid4().hex}.jpg"
            temp_path = os.path.join(app_config["PROFILE_IMAGE_FOLDER"], f"temp_{image_filename}")
            final_path = os.path.join(app_config["PROFILE_IMAGE_FOLDER"], image_filename)
            
            # Salviamo temporaneamente l'originale
            profile_image.save(temp_path)
            
            # Comprimiamo e salviamo nella destinazione finale
            if compress_image(temp_path, final_path):
                user.profile_image = image_filename
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            else:
                # Se fallisce, usiamo l'originale rinominandolo
                os.rename(temp_path, final_path)
                user.profile_image = image_filename

        db.session.commit()
        return {
            "message": "Profilo aggiornato",
            "profile_name": user.profile_name,
            "profile_image": user.profile_image,
        }, 200


class CategoryService(BaseService):
    @staticmethod
    def slugify(name: str) -> str:
        Category = CategoryService.get_model("Category")

        base = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
        base = base.strip("-")
        if not base:
            base = "categoria"
        slug = base
        suffix = 1
        while Category.query.filter_by(slug=slug).first():
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug

    @staticmethod
    def get_or_create_category(name: str):
        Category = CategoryService.get_model("Category")

        name = name.strip()
        if not name:
            return None
        existing = Category.query.filter(db.func.lower(Category.name) == name.lower()).first()
        if existing:
            return existing
        slug = CategoryService.slugify(name)
        new_cat = Category(name=name, slug=slug)
        db.session.add(new_cat)
        db.session.flush()
        return new_cat

    @staticmethod
    def list_categories():
        Category = CategoryService.get_model("Category")
        categories = Category.query.order_by(Category.name).all()
        return [
            {"id": c.id, "name": c.name, "slug": c.slug, "created_at": c.created_at.strftime("%Y-%m-%d")}
            for c in categories
        ], 200

    @staticmethod
    def create_category(data):
        Category = CategoryService.get_model("Category")

        name = (data or {}).get("name", "").strip()
        if not name:
            return {"error": "Nome categoria mancante"}, 400

        slug = CategoryService.slugify(name)
        category = Category(name=name, slug=slug)
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "Categoria gia esistente"}, 409

        return {"message": "Categoria creata", "id": category.id, "slug": category.slug}, 201

    @staticmethod
    def update_category(category_id, data):
        Category = CategoryService.get_model("Category")

        category = db.session.get(Category, category_id)
        if not category:
            abort(404)

        name = (data or {}).get("name", "").strip()
        if not name:
            return {"error": "Nome categoria mancante"}, 400

        category.name = name
        category.slug = CategoryService.slugify(name)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "Categoria gia esistente"}, 409

        return {"message": "Categoria aggiornata"}, 200

    @staticmethod
    def delete_category(category_id):
        Category = CategoryService.get_model("Category")
        Article = CategoryService.get_model("Article")

        category = db.session.get(Category, category_id)
        if not category:
            abort(404)

        Article.query.filter_by(category_id=category.id).update({"category_id": None})
        db.session.delete(category)
        db.session.commit()
        return {"message": "Categoria eliminata"}, 200


class ArticleService(BaseService):
    @staticmethod
    def get_articles(category_ids, cache):
        Article = ArticleService.get_model("Article")

        cache_key = f"articles_{sorted(category_ids)}"
        cached_data = cache.get(cache_key)
        if cached_data:
            print(" REDIS: Cache Hit per la lista articoli")
            return json.loads(cached_data), 200

        print(" DB: Cache Miss, leggo dal database")
        query = Article.query
        if category_ids:
            query = query.filter(Article.category_id.in_(category_ids))

        articles = query.order_by(Article.date_posted.desc()).all()
        articles_data = [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "image": a.image,
                "author": a.author.username,
                "author_id": a.author_id,
                "date_posted": a.date_posted.strftime("%Y-%m-%d %H:%M"),
                "likes": a.likes.count(),
                "category": a.category.name if a.category_id else None,
                "category_id": a.category_id,
            }
            for a in articles
        ]

        cache.setex(cache_key, 600, json.dumps(articles_data))
        return articles_data, 200

    @staticmethod
    def create_article(data, files, current_user, cache, app_config):
        Article = ArticleService.get_model("Article")

        # Valida i dati con Marshmallow (titolo, contenuto E immagine)
        try:
            data_to_validate = data.to_dict() if hasattr(data, 'to_dict') else dict(data or {})
            if files and files.get("image"):
                data_to_validate["image"] = files["image"]
                
            valid_data = article_schema.load(data_to_validate)
        except ValidationError as err:
            return {"error": err.messages}, 400

        title = valid_data["title"].strip()
        content = valid_data["content"].strip()
        image_file = valid_data.get("image")
        
        category_id = data_to_validate.get("category_id")
        category_name = data_to_validate.get("category_name", "").strip() if isinstance(data_to_validate.get("category_name"), str) else ""

        category = None
        if category_name:
            category = CategoryService.get_or_create_category(category_name)
        elif category_id and str(category_id).isdigit():
            Category = ArticleService.get_model("Category")
            category = db.session.get(Category, int(category_id))
            if not category:
                return {"error": "Categoria non trovata"}, 404

        image_filename = None
        if image_file and image_file.filename:
            image_filename = f"{uuid.uuid4().hex}.jpg"
            temp_path = os.path.join(app_config["UPLOAD_FOLDER"], f"temp_{image_filename}")
            final_path = os.path.join(app_config["UPLOAD_FOLDER"], image_filename)
            
            # Salva file temporaneo
            image_file.save(temp_path)
            
            # Comprime
            if compress_image(temp_path, final_path):
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            else:
                os.rename(temp_path, final_path)

        article = Article(
            title=title,
            content=content,
            image=image_filename,
            author_id=current_user.id,
            category_id=category.id if category else None,
        )

        db.session.add(article)
        db.session.commit()

        for key in cache.keys("articles_*"):
            cache.delete(key)
        print(" REDIS: cache svuotata dopo creazione articolo")
        return {"message": "Articolo creato", "id": article.id}, 201

    @staticmethod
    def update_article(article_id, data, current_user, cache):
        Article = ArticleService.get_model("Article")
        Category = ArticleService.get_model("Category")

        article = db.session.get(Article, article_id)
        if not article:
            abort(404)
        if article.author_id != current_user.id and not current_user.is_admin:
            return {"error": "Non autorizzato"}, 403

        data = data or {}
        article.title = data.get("title", article.title)
        article.content = data.get("content", article.content)

        if "category_id" in data or "category_name" in data:
            category_id = data.get("category_id")
            category_name = data.get("category_name", "").strip() if isinstance(data.get("category_name"), str) else ""
            if category_name:
                category = CategoryService.get_or_create_category(category_name)
                article.category_id = category.id
            elif category_id is None:
                article.category_id = None
            else:
                category = db.session.get(Category, category_id)
                if not category:
                    return {"error": "Categoria non trovata"}, 404
                article.category_id = category.id

        db.session.commit()
        for key in cache.keys("articles_*"):
            cache.delete(key)
        return {"message": "Articolo aggiornato"}, 200

    @staticmethod
    def delete_article(article_id, current_user, cache):
        Article = ArticleService.get_model("Article")
        Comment = ArticleService.get_model("Comment")

        article = db.session.get(Article, article_id)
        if not article:
            abort(404)
        if article.author_id != current_user.id and not current_user.is_admin:
            abort(403, description="Non autorizzato a cancellare questo articolo")

        Comment.query.filter_by(article_id=article.id).delete()
        db.session.delete(article)
        db.session.commit()

        for key in cache.keys("articles_*"):
            cache.delete(key)
        return True


class CommentService(BaseService):
    @staticmethod
    def get_comments(article_id):
        Article = CommentService.get_model("Article")
        Comment = CommentService.get_model("Comment")

        if not db.session.get(Article, article_id):
            abort(404)

        comments = Comment.query.filter_by(article_id=article_id).order_by(Comment.date_posted.desc()).all()
        return [
            {
                "id": c.id,
                "content": c.content,
                "author": c.author.username,
                "author_id": c.author_id,
                "date_posted": c.date_posted.strftime("%Y-%m-%d %H:%M"),
            }
            for c in comments
        ], 200

    @staticmethod
    def add_comment(article_id, data, current_user):
        Article = CommentService.get_model("Article")
        Comment = CommentService.get_model("Comment")

        if not db.session.get(Article, article_id):
            abort(404)
        if not data or not data.get("content"):
            return {"error": "Contenuto mancante"}, 400

        comment = Comment(
            content=data["content"],
            article_id=article_id,
            author_id=current_user.id,
        )
        db.session.add(comment)
        db.session.commit()
        return {"message": "Commento aggiunto"}, 201

    @staticmethod
    def delete_comment(comment_id, current_user):
        Comment = CommentService.get_model("Comment")

        comment = db.session.get(Comment, comment_id)
        if not comment:
            abort(404)
        if comment.author_id != current_user.id and not current_user.is_admin:
            return {"error": "Non autorizzato"}, 403

        db.session.delete(comment)
        db.session.commit()
        return {"message": "Commento eliminato"}, 200

    @staticmethod
    def update_comment(comment_id, data, current_user):
        Comment = CommentService.get_model("Comment")

        comment = db.session.get(Comment, comment_id)
        if not comment:
            abort(404)
        if comment.author_id != current_user.id and not current_user.is_admin:
            return {"error": "Non autorizzato"}, 403

        data = data or {}
        comment.content = data.get("content", comment.content)
        db.session.commit()
        return {"message": "Commento aggiornato"}, 200


class LikeService(BaseService):
    @staticmethod
    def get_likes(article_id):
        Article = LikeService.get_model("Article")

        article = db.session.get(Article, article_id)
        if not article:
            abort(404)
        return {"likes": article.likes.count()}, 200

    @staticmethod
    def add_like(article_id, current_user):
        Article = LikeService.get_model("Article")
        Like = LikeService.get_model("Like")

        article = db.session.get(Article, article_id)
        if not article:
            abort(404)

        like = Like(user_id=current_user.id, article_id=article.id)
        db.session.add(like)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "Hai gia messo like a questo articolo"}, 409

        return {"message": "Like aggiunto"}, 201

    @staticmethod
    def remove_like(article_id, current_user):
        Article = LikeService.get_model("Article")
        Like = LikeService.get_model("Like")

        article = db.session.get(Article, article_id)
        if not article:
            abort(404)

        like = Like.query.filter_by(user_id=current_user.id, article_id=article.id).first()
        if not like:
            return {"error": "Like non trovato"}, 404

        db.session.delete(like)
        db.session.commit()
        return {"message": "Like rimosso"}, 200


class AdminService:
    @staticmethod
    def make_me_admin(current_user):
        current_user.is_admin = True
        db.session.commit()
        return {"message": "Ora sei admin"}, 200
