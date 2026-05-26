from marshmallow import Schema, fields, validate, ValidationError
from PIL import Image
import io

# Estensioni consentite per le immagini
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def validate_image_extension(file_storage):
    """
    Validatore avanzato: controlla sia l'estensione che il contenuto reale del file.
    """
    if not file_storage or not file_storage.filename:
        return
    
    # 1. Controllo Estensione (Superficiale)
    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Estensione .{ext} non supportata.")

    # 2. Controllo Contenuto (Reale)
    try:
        # Leggiamo il contenuto senza chiudere il file (importante per Flask)
        image_bytes = file_storage.read()
        file_storage.seek(0) # Resettiamo il puntatore per i passaggi successivi
        
        img = Image.open(io.BytesIO(image_bytes))
        img.verify() # Verifica che il file sia effettivamente un'immagine valida
    except Exception:
        raise ValidationError("Il file non è un'immagine valida, anche se l'estensione sembra corretta.")

# Schema per validare i dati di un articolo
class ArticleSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=5, max=100))
    content = fields.Str(required=True, validate=validate.Length(min=10))
    category_id = fields.Int(required=False, allow_none=True)
    category_name = fields.Str(required=False, allow_none=True)
    image = fields.Raw(required=False, allow_none=True, validate=validate_image_extension)

# Schema per la registrazione di un utente
class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=25))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    profile_name = fields.Str(required=False, validate=validate.Length(max=50))

# Schema per l'aggiornamento del profilo
class ProfileSchema(Schema):
    profile_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    profile_image = fields.Raw(required=False, allow_none=True, validate=validate_image_extension)
