"""Modelli addizionali separati da app.py."""

from datetime import datetime

from extensions import db


class Like(db.Model):
    """Relazione like tra utente e articolo; uno per utente per articolo."""

    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "article_id",
            name="uix_like_user_article",
        ),
    )


class Category(db.Model):
    """Categoria di appartenenza per gli articoli."""

    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    articles = db.relationship("Article", backref="category", lazy=True)
