# Script per resettare la password di un utente
# Uso: python reset_password.py

from app import app, db, User, bcrypt

USERNAME = "Vincenzo"
NEW_PASSWORD = "123456"

with app.app_context():
    user = User.query.filter_by(username=USERNAME).first()
    if not user:
        print("Utente non trovato")
        raise SystemExit(1)

    user.password = bcrypt.generate_password_hash(NEW_PASSWORD).decode("utf-8")
    db.session.commit()
    print("Password aggiornata")
