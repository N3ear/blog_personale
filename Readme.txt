BLOG PERSONALE
backend in flask per un log personale con registrazione, login, profilo utente, gestione articoli e autenticazione tramite jwt 

CODICI
python
flask jwt 
pytest 
docker 

progetto realizzato come esercizio per sviluppare un backend flask per far vedere al tutor le mie capacita di implementare API, autenticazione jwt e test tramite pytest

AVIO PROGETTO
per avviare il backend è sufficente usare docker
(nel terminale) docker compose up --build 
http://localhost:5000 (per vedere il frontend)
docker compose down(per fermare i container)

TEST 
per eseguire i test bisogna usare il container del backend 
in un altro terminale usare docker compose exec backend pytest -q 
se tutto va bene uscira 20 passed 

AUTENTICAZIONE
POST /api/register
registra un nuovo utente 
body json { "username:" "", "email": "", "password": "" }

POST /api/login
fa il login e restituisce un token jwt 
body json {"username": "", "password": "" }

profilo utente 
GET /api/me 
restituisce i dati dell'utente loggato
richiede header: aturorization: bearer <token>

POST /api/profile/<username>
aggiorna il profilo dell utente 
richiede token e che l'utente sia il proprietario del profilo

ARTICOLI 
POST /api/articles
crea un nuovo articolo
richiede token 

GET /api/articles/<id>
restituisce un articolo

PUT /api/articles<id>
modifica articolo 
richiede token 

DELETE /api/articles/<id>
elimina articolo 
richiede token

STRUTTURA
blog_personale/
│
├── app.py
├── models.py
├── routes.py
├── make_admin.py
├── tempCodeRunnerFile.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── Readme.txt
│
├── database.db
├── instance/
│   └── blog.db
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── articles.js
│   │   ├── auth.js
│   │   ├── comments.js
│   │   ├── login.js
│   │   ├── profile.js
│   │   └── register.js
│   ├── immagini_profilo/
│   │   ├── default.png
│   │   └── (altri .png)
│   ├── uploads/
│   │   └── (immagini caricate)
│   └── favicon.svg
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── articles.html
│   └── profilo.html
│
└── tests/
    ├── conftest.py
    └── test_auth.py


STRUTTURA DEL CODICE

app.py  inizializzazione dell’app Flask e configurazione principale
routes.py  contiene tutte le route (autenticazione, articoli, profilo)
models.py  definizione dei modelli del database (User, Article)
make_admin.py  script per creare un utente amministratore