import os
import sys

# --- CONFIGURATION DES CHEMINS ---
# os.path.dirname(__file__) = dossier 'core'
# Le premier ".." remonte à la racine 'poke fantasy'
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if BASE_PATH not in sys.path:
    sys.path.append(BASE_PATH)

# Chemins relatifs (plus besoin de C:\Users\...)
DATA_PATH  = os.path.join(BASE_PATH, "data")
ASSET_PATH = os.path.join(BASE_PATH, "asset")
SAVES_PATH = os.path.join(BASE_PATH, "saves")

os.makedirs(SAVES_PATH, exist_ok=True)

SPRITE_PATH = os.path.join(ASSET_PATH, "sprite")
TYPE_ICON_PATH = os.path.join(ASSET_PATH, "types")
OBJET_PATH = os.path.join(ASSET_PATH, "objet")
AUDIO_PATH = os.path.join(ASSET_PATH, "audio")

# Fichiers JSON
DRESSEUR_JSON     = os.path.join(DATA_PATH, "dresseur_config.json")
CAPA_JSON         = os.path.join(DATA_PATH, "capacite_list.json")
POKEDEX_JSON      = os.path.join(DATA_PATH, "pokedex.json")
POKEMON_DATA_JSON = os.path.join(DATA_PATH, "pokemon_data.json")
EVOLUTION_JSON    = os.path.join(DATA_PATH, "evolution_config.json")

# Audio
BATTLE_THEME_PATH = os.path.join(AUDIO_PATH, "battle_theme.mp3")

# Paramètres écran
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE  = "Poke Fantasy - Shiny Edition"

STATUS_DATA = {
    "Brûlure":   {"label": "BRN", "color": (255, 128, 0)},
    "Paralysie": {"label": "PAR", "color": (255, 215, 0)},
    "Poison":    {"label": "PSN", "color": (160, 32, 240)},
    "Sommeil":   {"label": "SLP", "color": (255, 105, 180)},
    "Gelé":      {"label": "FRZ", "color": (0, 255, 255)}
}