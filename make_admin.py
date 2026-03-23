# Script per creare un utente amministratore manualmente
# Da usare solo per configurazione iniziale o manutenzione



from app import app, db, User

with app.app_context():
    user = User.query.filter_by(username="Vincenzo").first()
    if user:
        user.is_admin = True
        db.session.commit()
        print("Utente promosso ad ADMIN")
    else:
        print("Utente non trovato")
