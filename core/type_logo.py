import os
import requests

# Dossier de destination
OUTPUT_DIR = os.path.join("asset", "types")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Liste de tes types (doit correspondre au TypeChart)
TYPES = [
    "Normal", "Feu", "Eau", "Plante", "Électrik", "Glace", 
    "Combat", "Poison", "Sol", "Vol", "Psy", "Insecte", 
    "Roche", "Spectre", "Dragon", "Ténèbres", "Acier", "Fée"
]

# Mapping anglais pour les URLs
MAPPING_ENG = {
    "Normal": "normal", "Feu": "fire", "Eau": "water", "Plante": "grass",
    "Électrik": "electric", "Glace": "ice", "Combat": "fighting", "Poison": "poison",
    "Sol": "ground", "Vol": "flying", "Psy": "psychic", "Insecte": "bug",
    "Roche": "rock", "Spectre": "ghost", "Dragon": "dragon", "Ténèbres": "dark",
    "Acier": "steel", "Fée": "fairy"
}

# URL stable (via un CDN de sprites)
URL_TEMPLATE = "https://raw.githubusercontent.com/duiker101/pokemon-type-svg-icons/master/icons/{}.svg"

print("--- Téléchargement des icônes de types (Format SVG/PNG) ---")

# On ajoute un header pour éviter d'être bloqué
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for type_fr in TYPES:
    type_en = MAPPING_ENG.get(type_fr)
    # Note: On utilise des fichiers SVG ici car ils sont plus propres, 
    # mais Arcade préfère le PNG. Si tu as besoin de PNG, voici une source alternative :
    url = f"https://www.serebii.net/pokedex-bw/type/{type_en}.gif"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # On enregistre en .png pour la compatibilité Arcade (même si c'est un .gif à l'origine)
            file_path = os.path.join(OUTPUT_DIR, f"{type_fr}.png")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"✓ {type_fr}.png téléchargé avec succès.")
        else:
            print(f"✗ Erreur {response.status_code} pour {type_fr}")
    except Exception as e:
        print(f"Erreur pour {type_fr}: {e}")

print("\nTerminé ! Vérifie le dossier asset/types/")