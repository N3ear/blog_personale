"""
Script per creare un utente amministratore manualmente.
Da usare solo per configurazione iniziale o manutenzione.

Esempi:
python make_admin.py --username mario
python make_admin.py --email mario@example.com
"""

import argparse
import sys

from app import app, db, User


def _set_admin(username: str | None, email: str | None) -> int:
    if not username and not email:
        print("Errore: specifica --username oppure --email")
        return 2

    with app.app_context():
        query = User.query
        user = None
        if username:
            user = query.filter_by(username=username).first()
        if user is None and email:
            user = query.filter_by(email=email).first()

        if user is None:
            print("Errore: utente non trovato")
            return 1

        if user.is_admin:
            print(f"Utente '{user.username}' e' gia' admin")
            return 0

        user.is_admin = True
        db.session.commit()
        print(f"Utente '{user.username}' promosso ad admin")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Promuove un utente a admin")
    parser.add_argument("--username", help="Username da promuovere")
    parser.add_argument("--email", help="Email da promuovere")
    args = parser.parse_args()
    return _set_admin(args.username, args.email)


if __name__ == "__main__":
    raise SystemExit(main())
 
