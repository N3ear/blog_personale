import time
import os
from flask_socketio import SocketIO

# ATTENZIONE: Usa l'URL che punta al servizio 'redis' di Docker
# In Docker, il nome dell'host è solitamente il nome del servizio nel docker-compose (quindi 'redis')
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Inizializziamo il "pubblicatore" di SocketIO
# Questo si connette a Redis per inviare segnali verso Flask
socketio_publisher = SocketIO(message_queue=REDIS_URL)

def send_welcome_email(email, username):
    print(f"📧 [TASK] Inizio invio email a {email}...")
    time.sleep(5)  # Simuliamo il tempo di invio
    
    print(f"✅ [TASK] Email inviata a {username}!")

    # INVIAMO LA NOTIFICA
    # Il nome 'notifica_email' deve essere identico a quello nel JS
    socketio_publisher.emit('notifica_email', {
        'message': f'Ehi {username}, la mail di benvenuto è stata spedita!'
    }, namespace='/') 
    
    print("📡 [TASK] Segnale WebSocket inviato con successo!")