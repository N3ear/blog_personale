import time 

def send_welcome_email(email, username):
    """simulazione di invio email di benvenuto"""
    print(f"inizio invio email a {email}...")
    # simuliamo ritardo nell'invio dell'email (il tempo di connettersi al server SMTP)
    time.sleep(5)
    print(f"email inviata con successo a {username}!")
    return True