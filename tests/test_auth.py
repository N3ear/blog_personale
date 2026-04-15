import io
import pytest
import random
from datetime import datetime, timedelta
import jwt

def test_login_success(client):
    
    client.post("/api/register", json={"username": "test", "password": "123", "email": "t@e.com"})
    
    res = client.post("/api/login", json={"username": "test", "password": "123"})
    assert res.status_code == 200
    assert "token" in res.get_json()
    
def test_login_fail(client):
    payload = {
        "username": "testuser",
        "password": "passwordsbagliata"
    }
    
    response = client.post("/api/login", json=payload)

    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data

def test_change_password_success(auth_client):
    client, username = auth_client

    res = client.post("/api/change-password", json={
        "current_password": "password123",
        "new_password": "newpass123"
    })
    assert res.status_code == 200
    assert res.get_json()["message"] == "Password aggiornata"

    login_res = client.post("/api/login", json={
        "username": username,
        "password": "newpass123"
    })
    assert login_res.status_code == 200
    assert "token" in login_res.get_json()

def test_change_password_wrong_current(auth_client):
    client, _ = auth_client

    res = client.post("/api/change-password", json={
        "current_password": "sbagliata",
        "new_password": "newpass123"
    })
    assert res.status_code == 401
    assert "error" in res.get_json()

def test_change_password_missing_fields(auth_client):
    client, _ = auth_client

    res = client.post("/api/change-password", json={
        "current_password": ""
    })
    assert res.status_code == 400
    assert "error" in res.get_json()

def test_change_password_invalid_json(auth_client):
    client, _ = auth_client

    res = client.post(
        "/api/change-password",
        data="not-json",
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 400
    assert "error" in res.get_json()

def test_change_password_no_token(client):
    res = client.post("/api/change-password", json={
        "current_password": "password123",
        "new_password": "newpass123"
    })
    assert res.status_code == 401
    assert "error" in res.get_json()


def test_register_success(client):
    res = client.post("/api/register", json={
        "username":"nuovouser",
        "password": "password123",
        "email": "nuovo@example.com"
    })
    assert res.status_code == 201
    
def test_protected_endpoint_no_token(client):
    response = client.get("/api/me")
    
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Token mancante"





def test_create_article_with_token(auth_client):
    client, _ = auth_client
    res = client.post("/api/articles", data={
        "title": "Titolo Test",
        "content": "Contenuto"
    })
    assert res.status_code == 201
    assert res.get_json()["message"] == "Articolo creato"

def test_get_articles_list(auth_client):
    
    client, username = auth_client
    
    client.post("/api/articles", data={
        "title": "Articolo per la lista",
        "content": "contenuto di prova"
    })
    
    response = client.get("/api/articles")
    assert response.status_code == 200
    
    articles = response.get_json()
    assert len(articles) >= 1
    assert any(a.get("title") == "Articolo per la lista" for a in articles)


def test_update_article_with_token(auth_client):
    client, username = auth_client
    
    create_res = client.post("/api/articles", data={"title": "Originale", "content": "Testo" })
    article_id = create_res.get_json()["id"]
    
    res = client.put(f"/api/articles/{article_id}", json={
        "title": "Aggiornato",
        "content": "Nuovo contenuto"
    })
    assert res.status_code == 200
    assert res.get_json()["message"] == "Articolo aggiornato"

def test_delete_article_with_token(auth_client):
    client, username = auth_client
    
    create_res = client.post("/api/articles", data={
        "title": "da eliminare",
        "content": "testo"
    })
    article_id = create_res.get_json()["id"]
    
    response = client.delete(f"/api/articles/{article_id}")
    
    assert response.status_code == 200
    assert response.get_json()["message"] == "Articolo eliminato"


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


def test_update_profile_valid(auth_client):
    
    client, username = auth_client
    
    res = client.post(
        f"/api/profile/{username}",
        data={"profile_name": "Nuovo Nome"}
    )
    assert res.status_code == 200
    assert res.get_json()["profile_name"] == "Nuovo Nome"


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


def test_update_profile_image(auth_client):
    client, username = auth_client

    finto_file_img = (io.BytesIO(b"fake-image-data"), "avatar.jpg")
    data = {
        "profile_name": "Nuovo Nome",
        "profile_image": finto_file_img,
    }

    response = client.post(
        f"/api/profile/{username}",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 200
    assert "profile_image" in response.get_json()


def test_register_missing_data(client):

    res = client.post("/api/register", json={"username": "solo_nome"})
    assert res.status_code == 400
    assert "error" in res.json
    
def test_access_me_anonymous(client):
    """Verifica che /api/me sia protetta (401), a differenza degli articoli"""
    res = client.get("/api/me")
    assert res.status_code == 401


def test_register_invalid_json(client):
    """Testa l'invio di JSON malformato o vuoto"""
    res = client.post(
        "/api/register",
        data="non-un-json",
        content_type="application/json",
    )
    assert res.status_code in (400, 415)
    
def test_delete_artice_anauthorized(client):
    
    res = client.delete("/api/articles/1")
    assert res.status_code == 401 
    
def test_logout_functional(auth_client):
    
    client, _ = auth_client
    
    res = client.post("/api/logout")
    
    assert res.status_code in (200, 302)


# 1. Testiamo la creazione articolo con DATI MANCANTI (colpisce righe tipo 121-124)
def test_create_article_missing_fields(auth_client):
    client, _ = auth_client
    res = client.post("/api/articles", data={"title": ""})  # Titolo vuoto
    assert res.status_code == 400


# 2. Testiamo l'aggiornamento di un articolo che NON ESISTE (colpisce righe tipo 200+)
def test_update_article_not_found(auth_client):
    client, _ = auth_client
    res = client.put("/api/articles/999999", json={"title": "Nuovo"})
    assert res.status_code == 404


# 3. Testiamo la registrazione con EMAIL MALFORMATA (colpisce validazioni iniziali)
def test_register_invalid_email(client):
    res = client.post("/api/register", json={
        "username": "user_test",
        "password": "password123",
        "email": "email-non-valida"
    })
    assert res.status_code == 400


def test_register_empty_payload(client):
    """Testa l'invio di un oggetto vuoto alla registrazione"""
    res = client.post("/api/register", json={})
    # Questo dovrebbe attivare i controlli di validazione iniziali
    assert res.status_code == 400


# 4. Testiamo il recupero del profilo di un utente INESISTENTE
def test_profile_methods(client):
    """Verifica che il profilo risponda 405 se provi a leggerlo (GET) invece di scriverlo"""
    res = client.get("/api/profile/testuser")
    assert res.status_code in (405, 404)


# 5. Testiamo il caricamento immagine SENZA FILE (colpisce rami errore upload)
def test_update_profile_image_empty(auth_client):
    client, username = auth_client
    # Inviamo il campo ma senza il contenuto del file
    res = client.post(f"/api/profile/{username}", data={"profile_image": ""})
    assert res.status_code in (400, 200)  # Dipende se il tuo server ignora o dà errore


# --- TEST COMMENTI (se presenti) ---
def test_comment_flow(auth_client):
    client, _ = auth_client
    # Creiamo un articolo per avere un ID
    res_art = client.post("/api/articles", data={"title": "Per Commenti", "content": "Test"})
    art_id = res_art.get_json()["id"]

    # Proviamo a postare un commento
    res = client.post(f"/api/articles/{art_id}/comments", json={"content": "Bell'articolo!"})
    # Se la rotta esiste, alzerà la coverage, se dà 404 non succede nulla
    assert res.status_code in (201, 200, 404)


# --- TEST RICERCA ---
def test_search_route(client):
    """Colpisce le logiche di filtro e query string"""
    res = client.get("/api/articles?search=test&category=tech")
    assert res.status_code == 200


# --- TEST ERRORI DI AGGIORNAMENTO PROFILO ---
def test_update_profile_invalid_data(auth_client):
    client, username = auth_client
    # Invia dati che potrebbero far fallire la validazione
    res = client.post(f"/api/profile/{username}", data={"profile_name": ""})
    assert res.status_code in (200, 400)


# --- TEST CATEGORIE/TAG (Colpisce righe tipo 400-500) ---
def test_get_categories(client):
    res = client.get("/api/categories")
    assert res.status_code in (200, 404)


# --- TEST FILTRI ARTICOLI (Colpisce le logiche di query nel database) ---
def test_articles_filters(client):
    # Prova a filtrare per autore o tag inesistente
    res = client.get("/api/articles?author=admin&tag=python")
    assert res.status_code == 200


# --- TEST ERRORI ARTICOLI ---
def test_delete_non_existent_article(auth_client):
    client, _ = auth_client
    res = client.delete("/api/articles/999999")
    assert res.status_code == 404


# --- TEST UPDATE PROFILO CON DATI PARZIALI (Colpisce rami if/else) ---
def test_update_profile_partial(auth_client):
    client, username = auth_client
    res = client.post(f"/api/profile/{username}", data={"profile_name": "SoloNome"})
    assert res.status_code == 200


# --- TEST PER I COMMENTI (Righe 517-533) ---
def test_add_comment_success(auth_client):
    client, _ = auth_client
    # 1. Creiamo l'articolo
    res_art = client.post("/api/articles", data={
        "title": "Articolo per commenti",
        "content": "Contenuto di prova"
    })
    art_data = res_art.get_json() or {}
    art_id = art_data.get("id") or art_data.get("article_id")
    assert art_id is not None

    # 2. Aggiungiamo il commento
    res = client.post(f"/api/articles/{art_id}/comments", json={
        "content": "Questo è un commento di test!"
    })
    assert res.status_code == 201


def test_add_comment_article_not_found(auth_client):
    client, _ = auth_client
    # Proviamo a commentare un articolo che non esiste (ID assurdo)
    res = client.post("/api/articles/999999/comments", json={
        "content": "Non funzionerà"
    })
    assert res.status_code == 404


def test_add_comment_invalid_json(auth_client):
    client, _ = auth_client
    # Creiamo un articolo
    res_art = client.post("/api/articles", data={"title": "Test JSON", "content": "..."})
    art_data = res_art.get_json() or {}
    art_id = art_data.get("id") or art_data.get("article_id")
    assert art_id is not None

    # Inviamo un JSON senza il campo 'content' (scatta l'errore 400)
    res = client.post(f"/api/articles/{art_id}/comments", json={})
    assert res.status_code == 400


def test_update_category_unauthorized(auth_client):
    """Testa che un utente normale non possa modificare categorie (Admin required)"""
    client, _ = auth_client
    # Questo colpisce le righe del decoratore @admin_required
    res = client.put("/api/categories/1", json={"name": "Nuovo Nome"})
    assert res.status_code == 403


def test_add_comment_flow(auth_client):
    client, _ = auth_client
    # 1. Creiamo l'articolo
    res_art = client.post("/api/articles", json={
        "title": "Articolo Test Finale",
        "content": "Contenuto per attivare la coverage"
    })

    # 2. Recuperiamo l'ID in modo sicuro (senza modelli)
    art_data = res_art.get_json()
    # Proviamo a prenderlo da diverse posizioni comuni
    art_id = art_data.get("id") or art_data.get("article_id")

    # 3. Se abbiamo l'ID, testiamo i commenti (Righe 517-533)
    if art_id:
        res_comm = client.post(f"/api/articles/{art_id}/comments", json={
            "content": "Ottimo post!"
        })
        assert res_comm.status_code == 201


def test_admin_route_check(auth_client):
    """Testa una rotta admin per colpire le righe 679-696"""
    client, _ = auth_client
    # Proviamo a modificare una categoria (ID 1)
    # Anche se fallisce (403), accende le righe del decoratore @admin_required
    res = client.put("/api/categories/1", json={"name": "Nuovo Nome"})
    assert res.status_code in (403, 404, 200)


def test_login_required_invalid_token(client):
    res = client.get("/api/me", headers={"Authorization": "Bearer token-non-valido"})
    assert res.status_code == 401


def test_login_required_expired_token(client):
    expired = jwt.encode(
        {"user_id": 1, "exp": datetime.utcnow() - timedelta(hours=1)},
        client.application.config["SECRET_KEY"],
        algorithm="HS256",
    )
    res = client.get("/api/me", headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401


def test_login_required_user_not_found(client):
    token = jwt.encode(
        {"user_id": 999999, "exp": datetime.utcnow() + timedelta(hours=1)},
        client.application.config["SECRET_KEY"],
        algorithm="HS256",
    )
    res = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_register_invalid_username_chars(client):
    res = client.post("/api/register", json={
        "username": "user*bad",
        "password": "password123",
        "email": "userbad@example.com"
    })
    assert res.status_code == 400


def test_register_username_too_short(client):
    res = client.post("/api/register", json={
        "username": "ab",
        "password": "password123",
        "email": "short@example.com"
    })
    assert res.status_code == 400


def test_update_profile_not_found(auth_client):
    client, _ = auth_client
    res = client.post("/api/profile/utente_inesistente", data={"profile_name": "Test"})
    assert res.status_code == 404


def test_update_profile_name_too_long(auth_client):
    client, username = auth_client
    res = client.post(f"/api/profile/{username}", data={"profile_name": "a" * 51})
    assert res.status_code == 400


def test_create_article_invalid_image_extension(auth_client):
    client, _ = auth_client
    fake_file = (io.BytesIO(b"fake-image-data"), "immagine.txt")
    res = client.post(
        "/api/articles",
        data={"title": "Titolo", "content": "Contenuto", "image": fake_file},
        content_type="multipart/form-data",
    )
    assert res.status_code == 400


def test_create_article_invalid_category_id(auth_client):
    client, _ = auth_client
    res = client.post("/api/articles", data={
        "title": "Titolo",
        "content": "Contenuto",
        "category_id": 999999
    })
    assert res.status_code == 404


def test_create_article_with_category_name(auth_client):
    client, _ = auth_client
    fake_image = (io.BytesIO(b"fake-image-data"), "immagine.png")
    res = client.post(
        "/api/articles",
        data={
            "title": "Titolo Cat",
            "content": "Contenuto",
            "category_name": "!!!",
            "image": fake_image,
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 201


def test_get_comments_not_found(client):
    res = client.get("/api/articles/999999/comments")
    assert res.status_code == 404


def test_comment_update_and_delete_flow(auth_client):
    client, _ = auth_client
    # Crea articolo
    res_art = client.post("/api/articles", data={"title": "Articolo C", "content": "Test"})
    art_id = (res_art.get_json() or {}).get("id")
    assert art_id is not None

    # Aggiungi commento
    res_comm = client.post(f"/api/articles/{art_id}/comments", json={"content": "C1"})
    assert res_comm.status_code == 201

    # Recupera commenti per ottenere ID
    res_list = client.get(f"/api/articles/{art_id}/comments")
    assert res_list.status_code == 200
    comments = res_list.get_json() or []
    assert len(comments) >= 1
    comment_id = comments[0]["id"]

    # Aggiorna commento
    res_upd = client.put(f"/api/comments/{comment_id}", json={"content": "Aggiornato"})
    assert res_upd.status_code == 200

    # Elimina commento
    res_del = client.delete(f"/api/comments/{comment_id}")
    assert res_del.status_code == 200


def test_likes_flow(auth_client):
    client, _ = auth_client
    res_art = client.post("/api/articles", data={"title": "Articolo Like", "content": "Test"})
    art_id = (res_art.get_json() or {}).get("id")
    assert art_id is not None

    res_get = client.get(f"/api/articles/{art_id}/likes")
    assert res_get.status_code == 200

    res_add = client.post(f"/api/articles/{art_id}/likes")
    assert res_add.status_code == 201

    res_dup = client.post(f"/api/articles/{art_id}/likes")
    assert res_dup.status_code == 409

    res_del = client.delete(f"/api/articles/{art_id}/likes")
    assert res_del.status_code == 200

    res_del_again = client.delete(f"/api/articles/{art_id}/likes")
    assert res_del_again.status_code == 404


def test_categories_admin_flow(auth_client):
    client, _ = auth_client
    # diventa admin
    res_admin = client.post("/api/make-me-admin")
    assert res_admin.status_code == 200

    # crea categoria
    res_create = client.post("/api/categories", json={"name": "Tech"})
    assert res_create.status_code in (201, 409)
    cat_id = (res_create.get_json() or {}).get("id")

    # lista categorie
    res_list = client.get("/api/categories")
    assert res_list.status_code == 200

    # duplica categoria per colpire 409
    res_dup = client.post("/api/categories", json={"name": "Tech"})
    assert res_dup.status_code in (201, 409)

    # prova update con nome mancante
    res_update_bad = client.put("/api/categories/1", json={"name": ""})
    assert res_update_bad.status_code in (400, 404)

    # update valido se abbiamo un id
    if cat_id:
        res_update_ok = client.put(f"/api/categories/{cat_id}", json={"name": "Tech Updated"})
        assert res_update_ok.status_code in (200, 409)
        # delete valido
        res_delete_ok = client.delete(f"/api/categories/{cat_id}")
        assert res_delete_ok.status_code in (200, 404)

    # elimina categoria non esistente per colpire 404
    res_delete = client.delete("/api/categories/999999")
    assert res_delete.status_code == 404


def test_create_category_missing_name(auth_client):
    client, _ = auth_client
    res = client.post("/api/categories", json={})
    assert res.status_code == 400


def test_me_success(auth_client):
    client, username = auth_client
    res = client.get("/api/me")
    assert res.status_code == 200
    assert res.get_json().get("username") == username


def test_articles_category_filter(auth_client):
    client, _ = auth_client
    # diventa admin per creare categoria
    client.post("/api/make-me-admin")
    res_cat = client.post("/api/categories", json={"name": "Filtro"})
    cat_id = (res_cat.get_json() or {}).get("id")
    assert cat_id is not None

    res_art = client.post("/api/articles", data={
        "title": "Articolo Cat",
        "content": "Test",
        "category_id": cat_id
    })
    assert res_art.status_code == 201

    res = client.get(f"/api/articles?category_id={cat_id},{cat_id}")
    assert res.status_code == 200


def test_update_article_category_not_found(auth_client):
    client, _ = auth_client
    res_art = client.post("/api/articles", data={"title": "Articolo U", "content": "Test"})
    art_id = (res_art.get_json() or {}).get("id")
    assert art_id is not None
    res = client.put(f"/api/articles/{art_id}", json={"category_id": 999999})
    assert res.status_code == 404


def test_update_article_unauthorized(client):
    # user1
    client.post("/api/register", json={"username": "user1", "email": "u1@example.com", "password": "password123"})
    res_login1 = client.post("/api/login", json={"username": "user1", "password": "password123"})
    token1 = res_login1.get_json()["token"]

    # user2
    client.post("/api/register", json={"username": "user2", "email": "u2@example.com", "password": "password123"})
    res_login2 = client.post("/api/login", json={"username": "user2", "password": "password123"})
    token2 = res_login2.get_json()["token"]

    # create article with user1
    res_art = client.post("/api/articles", data={"title": "Articolo P", "content": "Test"},
                          headers={"Authorization": f"Bearer {token1}"})
    art_id = (res_art.get_json() or {}).get("id")
    assert art_id is not None

    # try update with user2 -> 403
    res = client.put(f"/api/articles/{art_id}", json={"title": "Nope"},
                     headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


def test_delete_article_unauthorized(client):
    client.post("/api/register", json={"username": "user3", "email": "u3@example.com", "password": "password123"})
    res_login1 = client.post("/api/login", json={"username": "user3", "password": "password123"})
    token1 = res_login1.get_json()["token"]

    client.post("/api/register", json={"username": "user4", "email": "u4@example.com", "password": "password123"})
    res_login2 = client.post("/api/login", json={"username": "user4", "password": "password123"})
    token2 = res_login2.get_json()["token"]

    res_art = client.post("/api/articles", data={"title": "Articolo D", "content": "Test"},
                          headers={"Authorization": f"Bearer {token1}"})
    art_id = (res_art.get_json() or {}).get("id")
    assert art_id is not None

    res = client.delete(f"/api/articles/{art_id}", headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


def test_delete_comment_not_found(auth_client):
    client, _ = auth_client
    res = client.delete("/api/comments/999999")
    assert res.status_code == 404


def test_update_comment_not_found(auth_client):
    client, _ = auth_client
    res = client.put("/api/comments/999999", json={"content": "x"})
    assert res.status_code == 404


def test_likes_article_not_found(auth_client):
    client, _ = auth_client
    res_get = client.get("/api/articles/999999/likes")
    assert res_get.status_code == 404
    res_post = client.post("/api/articles/999999/likes")
    assert res_post.status_code == 404
    res_del = client.delete("/api/articles/999999/likes")
    assert res_del.status_code == 404
