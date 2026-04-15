# Script per aggiornare email utente
# Uso: python update_email.py

from app import app, db, User

USERNAME = "Vincenzo"
NEW_EMAIL = "vincenzocasieri005@gmail.com"

with app.app_context():
    user = User.query.filter_by(username=USERNAME).first()
    if not user:
        print("Utente non trovato")
        raise SystemExit(1)

    user.email = NEW_EMAIL
    db.session.commit()
    print("Email aggiornata")
