# 📝 Blog Personale - Flask Backend & Frontend

Benvenuto nel progetto **Blog Personale**, un'applicazione web completa sviluppata con **Flask** per gestire un log personale. Il sistema include funzionalità di autenticazione, gestione articoli, profili utente e un'infrastruttura moderna basata su container.

## 🚀 Funzionalità Principali

### 🔐 Autenticazione e Sicurezza
- **Registrazione e Login**: Gestiti tramite JWT (JSON Web Tokens).
- **Password Hashing**: Utilizzo di Bcrypt per la sicurezza delle credenziali.
- **Accesso Protetto**: Route API protette da decorator `@login_required_api`.

### 📰 Gestione Articoli (CRUD)
- **Creazione/Modifica/Eliminazione**: Gli utenti possono gestire i propri contenuti.
- **Immagini**: Supporto per il caricamento di immagini negli articoli.
- **Categorie**: Organizzazione degli articoli per categorie dinamiche.

### 👤 Profilo Utente
- **Personalizzazione**: Modifica del nome profilo e caricamento immagine avatar.
- **Dashboard**: Visualizzazione dei dati dell'utente loggato.

### 💬 Interazione
- **Commenti**: Sistema di commenti per ogni articolo (CRUD).
- **Like**: Possibilità di mettere/togliere like agli articoli.

### 📊 Monitoraggio e Real-time
- **Dashboard Statistiche**: Monitoraggio in tempo reale del sistema (CPU, RAM) tramite SocketIO e psutil.
- **Swagger UI**: Documentazione interattiva delle API.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, SQLAlchemy, Flask-Bcrypt, JWT, Flask-SocketIO.
- **Frontend**: HTML5, Vanilla JS, CSS3.
- **Database**: MySQL (in produzione/container), SQLite (opzionale per dev locale).
- **Task Queue**: Redis + RQ (Redis Queue) per compiti in background.
- **Web Server & Proxy**: Nginx.
- **Containerization**: Docker & Docker Compose.
- **Testing**: Pytest.

---

## 📂 Struttura del Progetto

```text
blog_personale/
├── app.py              # Inizializzazione Flask e configurazione
├── models.py           # Definizione modelli Database (User, Article, etc.)
├── routes.py           # Route dell'applicazione (commenti e placeholder)
├── services.py         # Logica di business (AuthService, ArticleService, etc.)
├── schemas.py          # Validazione dati (Marshmallow)
├── utils.py            # Utility e helper
├── worker.py           # Worker per task Redis
├── static/             # Asset statici (CSS, JS, Immagini)
│   ├── css/            # Fogli di stile
│   ├── js/             # Logica frontend suddivisa per servizi
│   └── uploads/        # Immagini caricate
├── templates/          # Template HTML (Jinja2)
├── tests/              # Suite di test automatizzati
├── nginx/              # Configurazione Nginx
└── docker-compose.yml  # Definizione dei servizi Docker
```

---

## ⚙️ Installazione e Avvio

### Requisiti
- [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/) installati.

### Avvio Rapido
1. Clona la repository.
2. Nella root del progetto, esegui:
   ```bash
   docker compose up --build
   ```
3. L'applicazione sarà disponibile su:
   - **Frontend**: [http://localhost:5000](http://localhost:5000)
   - **Documentazione API (Swagger)**: [http://localhost:5000/apidocs/](http://localhost:5000/apidocs/)

### Ferma i Container
```bash
docker compose down
```

---

## 🧪 Testing

I test sono scritti con **Pytest**. Per eseguirli all'interno dell'ambiente Docker:
```bash
docker compose exec backend pytest
```

---

## 🔌 API Endpoints (Esempi)

| Metodo | Endpoint | Descrizione |
| :--- | :--- | :--- |
| `POST` | `/api/register` | Registra un nuovo utente |
| `POST` | `/api/login` | Effettua il login e ottiene il token JWT |
| `GET` | `/api/me` | Recupera i dati del profilo corrente |
| `GET` | `/api/articles` | Elenca tutti gli articoli |
| `POST` | `/api/articles` | Crea un nuovo articolo (Richiede Token) |
| `POST` | `/api/articles/{id}/comments` | Aggiunge un commento (Richiede Token) |

---

## ✒️ Autore
Progetto realizzato come esercizio per dimostrare competenze nello sviluppo backend con Flask, gestione API, autenticazione e containerizzazione.
