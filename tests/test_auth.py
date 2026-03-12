def test_login_success(client):
    # Dati di login validi
    payload = {
        "username": "testuser",
        "password": "password123"
    }

    # Richiesta POST al login
    response = client.post("/api/login", json=payload)

    # Controlli
    assert response.status_code == 200
    data = response.get_json()
    assert "token" in data
    
def test_login_fail(client):
    payload = {
        "username": "testuser",
        "password": "passwordsbagliata"
    }
    
    response = client.post("/api/login", json=payload)

    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data

def test_register_success(client):
    payload = {
        "username": "nuovoutente",
        "password": "password123",
        "email": "nuovoutente@example.com",
    }
    
    response = client.post("/api/register", json=payload)

    assert response.status_code == 201
    data = response.get_json()
    assert "message" in data

def test_register_username_exists(client):
    
    payload = {
        "username": "utenteesistente",
        "password": "password123",
        "email":  "utente1@example.com",  
    }
    response = client.post("/api/register", json=payload)
    assert response.status_code == 201
    
    payload2 = {
        "username": "utenteesistente",
        "password": "password123",
        "email":  "utente2@example.com",  
    }
    response2 = client.post("/api/register", json=payload2)
    
    assert response2.status_code == 400
    data = response2.get_json()
    assert "error" in data
    
def test_protected_endpoint_no_token(client):
    response = client.get("/api/me")
    
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Token mancante"


def test_update_profile_with_token(client):
    
    reg_payload = {
        "username": "utente_test",
        "password": "password123",
        "email": "utente_test@example.com",
    }
    client.post("/api/register", json=reg_payload)
    
    login_payload = {
        "username": "utente_test",
        "password": "password123"
    }
    login_payload = {
        "username": "utente_test",
        "password": "password123"
    }
    login_response = client.post("/api/login", json=login_payload)
    token = login_response.get_json()["token"]
    
    response = client.post(
        "/api/profile/utente_test",
        data={"profile_name": "nuovo nome"},
        headers={"authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Profilo aggiornato"
    assert data["profile_name"] == "Nuovo Nome"


def test_create_article_with_token(client):
    # 1. Registrazione utente
    reg_payload = {
        "username": "autore_test",
        "password": "password123",
        "email": "autore_test@example.com"
    }
    client.post("/api/register", json=reg_payload)

    # 2. Login per ottenere il token
    login_payload = {
        "username": "autore_test",
        "password": "password123"
    }
    login_response = client.post("/api/login", json=login_payload)
    token = login_response.get_json()["token"]

    # 3. Creazione articolo (senza immagine)
    response = client.post(
        "/api/articles",
        data={
            "title": "Titolo di Test",
            "content": "Contenuto di prova"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # 4. Verifiche
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Articolo creato"
    assert "id" in data
    assert isinstance(data["id"], int)


def test_get_articles_list(client):
    # 1. Registrazione utente
    reg_payload = {
        "username": "autore_lista",
        "password": "password123",
        "email": "autore_lista@example.com"
    }
    client.post("/api/register", json=reg_payload)

    # 2. Login per ottenere il token
    login_payload = {
        "username": "autore_lista",
        "password": "password123"
    }
    login_response = client.post("/api/login", json=login_payload)
    token = login_response.get_json()["token"]

    # 3. Creazione articolo
    client.post(
        "/api/articles",
        data={
            "title": "Articolo per la lista",
            "content": "Contenuto di prova"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # 4. GET /api/articles
    response = client.get("/api/articles")
    assert response.status_code == 200

    articles = response.get_json()

    # 5. Verifiche sulla lista
    assert isinstance(articles, list)
    assert len(articles) >= 1

    article = articles[0]

    # 6. Verifica dei campi
    assert "id" in article
    assert "title" in article
    assert "content" in article
    assert "image" in article
    assert "author" in article
    assert "author_id" in article
    assert "date_posted" in article

    # 7. Verifica valori coerenti
    assert article["title"] == "Articolo per la lista"
    assert article["content"] == "Contenuto di prova"


def test_update_article_with_token(client):
    # 1. Registrazione utente
    reg_payload = {
        "username": "autore_update",
        "password": "password123",
        "email": "autore_update@example.com"
    }
    client.post("/api/register", json=reg_payload)

    # 2. Login per ottenere il token
    login_payload = {
        "username": "autore_update",
        "password": "password123"
    }
    login_response = client.post("/api/login", json=login_payload)
    token = login_response.get_json()["token"]

    # 3. Creazione articolo
    create_response = client.post(
        "/api/articles",
        data={
            "title": "Titolo originale",
            "content": "Contenuto originale"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = create_response.get_json()["id"]

    # 4. Aggiornamento articolo
    update_response = client.put(
        f"/api/articles/{article_id}",
        json={
            "title": "Titolo aggiornato",
            "content": "Contenuto aggiornato"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # 5. Verifiche
    assert update_response.status_code == 200
    data = update_response.get_json()
    assert data["message"] == "Articolo aggiornato"


def test_delete_article_with_token(client):
    # 1. Registrazione utente
    reg_payload = {
        "username": "autore_delete",
        "password": "password123",
        "email": "autore_delete@example.com"
    }
    client.post("/api/register", json=reg_payload)

    # 2. Login per ottenere il token
    login_payload = {
        "username": "autore_delete",
        "password": "password123"
    }
    login_response = client.post("/api/login", json=login_payload)
    token = login_response.get_json()["token"]

    # 3. Creazione articolo
    create_response = client.post(
        "/api/articles",
        data={
            "title": "Articolo da eliminare",
            "content": "Contenuto da eliminare"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = create_response.get_json()["id"]

    # 4. Eliminazione articolo
    delete_response = client.delete(
        f"/api/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 5. Verifiche sulla risposta
    assert delete_response.status_code == 200
    data = delete_response.get_json()
    assert data["message"] == "Articolo eliminato"

    # 6. Verifica che l'articolo non esista più
    list_response = client.get("/api/articles")
    articles = list_response.get_json()

    # L'articolo eliminato non deve essere presente
    assert all(a["id"] != article_id for a in articles)


def test_register_and_login(client):
    import random
    n = random.randint(1000, 9999)

    username = f"user{n}"
    email = f"user{n}@example.com"
    password = "password123"

    # 1. Registrazione
    res = client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    assert res.status_code == 201
    assert res.json["message"] == "Utente registrato"

    # 2. Login
    res = client.post("/api/login", json={
        "username": username,
        "password": password
    })

    assert res.status_code == 200
    assert "token" in res.json


def test_register_email_already_exists(client):
    import random
    n = random.randint(1000, 9999)

    email = f"user{n}@example.com"
    password = "password123"

    # 1. Prima registrazione (valida)
    res = client.post("/api/register", json={
        "username": f"user{n}",
        "email": email,
        "password": password
    })
    assert res.status_code == 201

    # 2. Seconda registrazione con la stessa email
    res = client.post("/api/register", json={
        "username": f"user{n}_alt",
        "email": email,  # stessa email
        "password": password
    })

    assert res.status_code == 400
    assert "error" in res.json
    assert "email" in res.json["error"].lower() or "esiste" in res.json["error"].lower()


def test_register_username_already_exists(client):
    import random
    n = random.randint(1000, 9999)

    username = f"user{n}"
    password = "password123"

    # 1. Prima registrazione (valida)
    res = client.post("/api/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": password
    })
    assert res.status_code == 201

    # 2. Seconda registrazione con lo stesso username
    res = client.post("/api/register", json={
        "username": username,  # stesso username
        "email": f"{username}_alt@example.com",
        "password": password
    })

    assert res.status_code == 400
    assert "error" in res.json
    assert "username" in res.json["error"].lower() or "esiste" in res.json["error"].lower()


def test_login_valid(client):
    import random
    n = random.randint(1000, 9999)

    username = f"user{n}"
    email = f"user{n}@example.com"
    password = "password123"

    # 1. Registrazione
    client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    # 2. Login valido
    res = client.post("/api/login", json={
        "username": username,
        "password": password
    })

    assert res.status_code == 200
    assert "token" in res.json


def test_login_wrong_password(client):
    import random
    n = random.randint(1000, 9999)

    username = f"user{n}"
    email = f"user{n}@example.com"
    password = "password123"

    # 1. Registrazione
    client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    # 2. Login con password sbagliata
    res = client.post("/api/login", json={
        "username": username,
        "password": "wrongpass"
    })

    assert res.status_code == 401
    assert "error" in res.json
    assert "password" in res.json["error"].lower()


def test_login_nonexistent_user(client):
    res = client.post("/api/login", json={
        "username": "utente_che_non_esiste",
        "password": "qualcosa"
    })

    assert res.status_code == 404
    assert "error" in res.json
    assert "inesistente" in res.json["error"].lower() or "non trovato" in res.json["error"].lower()


def test_me_without_token(client):
    res = client.get("/api/me")
    assert res.status_code == 401
    assert "error" in res.json


def test_update_profile_valid(client):
    import random
    n = random.randint(1000, 9999)

    username = f"user{n}"
    email = f"user{n}@example.com"
    password = "password123"

    # 1. Registrazione
    client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    # 2. Login
    res = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    token = res.json["token"]

    # 3. Aggiornamento profilo (usa form-data come da backend)
    res = client.post(
        f"/api/profile/{username}",
        data={"profile_name": "Nuovo Nome"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 200
    assert res.json["message"] == "Profilo aggiornato"
    assert res.json["profile_name"] == "Nuovo Nome"


def test_update_profile_wrong_user(client):
    import random
    n = random.randint(1000, 9999)

    username = f"user{n}"
    email = f"user{n}@example.com"
    password = "password123"

    # 1. Registrazione
    client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    # 2. Login
    res = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    token = res.json["token"]

    # 3. Tentativo di aggiornare il profilo di un altro utente
    res = client.post(
        "/api/profile/altro_utente",
        data={"profile_name": "Test"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code in (403, 404)


def test_update_profile_without_token(client):
    res = client.post("/api/profile/someuser", data={"profile_name": "Test"})
    assert res.status_code == 401
    assert "error" in res.json
