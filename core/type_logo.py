import os
import requests
import time

# --- CONFIGURATION DES CHEMINS ---
BASE_PATH = os.getcwd()
TYPES_DIR = os.path.join(BASE_PATH, "asset", "types")
os.makedirs(TYPES_DIR, exist_ok=True)

# --- CONFIGURATION DES TYPES ---
MAPPING_TYPES = {
    "Normal": "normal", "Feu": "fire", "Eau": "water", "Plante": "grass",
    "Électrik": "electric", "Glace": "ice", "Combat": "fighting", "Poison": "poison",
    "Sol": "ground", "Vol": "flying", "Psy": "psychic", "Insecte": "bug",
    "Roche": "rock", "Spectre": "ghost", "Dragon": "dragon", "Ténèbres": "dark",
    "Acier": "steel", "Fée": "fairy"
}

# --- CONFIGURATION TECHNIQUE DES STATUTS (UI) ---
# Ce dictionnaire fait le lien entre ton CombatEngine et ton affichage Arcade
STATUS_DATA = {
    "Brûlure":  {"label": "BRN", "color": (255, 128, 0)},    # Orange
    "Paralysie": {"label": "PAR", "color": (255, 215, 0)},   # Jaune/Or
    "Poison":    {"label": "PSN", "color": (160, 32, 240)},  # Violet
    "Toxique":   {"label": "TOX", "color": (120, 0, 200)},   # Violet Foncé
    "Sommeil":   {"label": "SLP", "color": (255, 105, 180)}, # Rose (Hot Pink)
    "Gelé":      {"label": "FRZ", "color": (0, 255, 255)},   # Cyan / Bleu clair
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def download_type_icon(name_fr, name_en):
    """Télécharge les icônes de types (Source Gen 8 - Épée/Bouclier)."""
    dest_path = os.path.join(TYPES_DIR, f"{name_fr}.png")
    
    # Liste d'URLs prioritaires pour les types
    urls = [
        f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/types/generation-viii/sword-shield/{list(MAPPING_TYPES.keys()).index(name_fr)+1}.png",
        f"https://play.pokemonshowdown.com/sprites/types/{name_en}.png"
    ]
    
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(r.content)
                print(f"✓ Type {name_fr} : Téléchargé depuis {url[:30]}...")
                return True
        except:
            continue
    
    print(f"✗ Type {name_fr} : Échec du téléchargement.")
    return False

def generer_memo_statuts():
    """Affiche un récapitulatif pour l'intégration dans le HUD."""
    print("\n" + "="*40)
    print(" CONFIGURATION DES STATUTS POUR ARCADE ")
    print("="*40)
    for nom, data in STATUS_DATA.items():
        print(f"{nom:10} -> Label: {data['label']} | Couleur RGB: {data['color']}")
    print("="*40 + "\n")

if __name__ == "__main__":
    print("--- Début de la récupération des assets ---")
    
    # 1. Téléchargement des types
    for fr, en in MAPPING_TYPES.items():
        download_type_icon(fr, en)
        time.sleep(0.1)
    
    # 2. Affichage du mémo pour le HUD
    generer_memo_statuts()
    
    print(f"Opération terminée. Les types sont dans : {TYPES_DIR}")