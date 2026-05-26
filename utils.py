import os 
from PIL import Image

def compress_image(source_path, target_path, max_width=1200, quality=70):
    """
    prende un immagine la ridimensiona e la comprime
    - source_path: dove si trova la foto originale (temporanea)
    - target_path: dove salva la foto compressa finale
    - max_width: larghezza massima (mantiene le proporzioni)
    - quality: livello di compressione (1-100)
    """
    try:
        with Image.open(source_path) as img:
            # Forza la conversione in RGB (necessario per JPEG se l'originale ha trasparenza)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Calcola le nuove dimensioni
            width, height = img.size
            if width > max_width:
                ratio = max_width / float(width)
                new_height = int(float(height) * ratio)
                # Filtro compatibile con tutte le versioni di Pillow
                resample_filter = getattr(Image, 'LANCZOS', getattr(getattr(Image, 'Resampling', {}), 'LANCZOS', 1))
                img = img.resize((max_width, new_height), resample_filter)

            # Salva l'immagine compressa
            img.save(target_path, "JPEG", optimize=True, quality=quality)
            return True
    except Exception as e:
        print(f"Errore durante la compressione: {e}")
        return False