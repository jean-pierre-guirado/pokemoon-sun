import json
import os
import requests

# Chemins
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data")
OBJET_IMG_PATH = os.path.join(ROOT_DIR, "asset", "objet")

os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(OBJET_IMG_PATH, exist_ok=True)

# Mapping mis à jour avec le Super Bonbon
items_data = {
    # BALLS
    "poke-ball": ["Poké Ball", "Ball", 200, "Ball de base."],
    "great-ball": ["Super Ball", "Ball", 600, "Efficace (x1.5)."],
    "ultra-ball": ["Hyper Ball", "Ball", 1200, "Très efficace (x2)."],
    "master-ball": ["Master Ball", "Ball", 0, "Capture garantie."],
    "premier-ball": ["Honor Ball", "Ball", 200, "Ball commémorative."],
    "luxury-ball": ["Luxe Ball", "Ball", 1000, "Rend le Pokémon amical."],
    "quick-ball": ["Rapide Ball", "Ball", 1000, "Efficace au début du combat."],
    "timer-ball": ["Chrono Ball", "Ball", 1000, "Efficace si le combat dure."],
    "net-ball": ["Filet Ball", "Ball", 1000, "Efficace sur Eau/Insecte."],
    "dusk-ball": ["Sombre Ball", "Ball", 1000, "Efficace de nuit ou grotte."],

    # SOINS
    "potion": ["Potion", "Soin", 300, "Restaure 20 PV."],
    "super-potion": ["Super Potion", "Soin", 700, "Restaure 50 PV."],
    "hyper-potion": ["Hyper Potion", "Soin", 1200, "Restaure 200 PV."],
    "max-potion": ["Max Potion", "Soin", 2500, "Restaure tous les PV."],
    "revive": ["Rappel", "Soin", 1500, "Réanime un Pokémon (50% PV)."],
    "max-revive": ["Rappel Max", "Soin", 3000, "Réanime (100% PV)."],
    "full-restore": ["Guérison", "Soin", 3000, "Soigne tout (PV + Statut)."],

    # RARE / LEVEL UP
    "rare-candy": ["Super Bonbon", "Rare", 4800, "Fait monter d'un niveau."],

    # BOOSTS
    "x-attack": ["Attaque +", "Boost", 500, "Boost l'Attaque en combat."],
    "x-defense": ["Défense +", "Boost", 500, "Boost la Défense en combat."],
    "x-speed": ["Vitesse +", "Boost", 500, "Boost la Vitesse en combat."],
    "x-sp-atk": ["Atk Spé +", "Boost", 500, "Boost l'Atk Spé en combat."],
    "x-sp-def": ["Déf Spé +", "Boost", 500, "Boost la Déf Spé en combat."],

    # ARGENT / VENTE
    "nugget": ["Pépite", "Vente", 5000, "Se vend très cher."],
    "pearl": ["Perle", "Vente", 1000, "Se vend cher."],
    "big-nugget": ["Maxi Pépite", "Vente", 10000, "Se vend extrêmement cher."],
    "stardust": ["Poussière Étoile", "Vente", 1500, "Un joli sable brillant."],

    # STRATEGIE
    "leftovers": ["Restes", "Strat", 4000, "Restaure des PV à chaque tour."],
    "life-orb": ["Orbe Vie", "Strat", 4000, "Boost dégâts mais blesse le porteur."],
    "choice-band": ["Bandeau Choix", "Strat", 4000, "Boost Attaque mais bloque 1 capacité."],
    "focus-sash": ["Ceinture Force", "Strat", 4000, "Empêche le K.O en 1 coup."],
    "rocky-helmet": ["Casque Brut", "Strat", 4000, "Blesse ceux qui vous touchent."]
}

def setup():
    final_json = {}
    print("--- Début du téléchargement ---")
    base_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/"

    for api_id, info in items_data.items():
        nom_fr, cat, prix, desc = info
        filename = f"{api_id}.png"
        save_path = os.path.join(OBJET_IMG_PATH, filename)
        
        # Téléchargement
        try:
            r = requests.get(f"{base_url}{filename}")
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(r.content)
                print(f"✓ {nom_fr} (OK)")
            else:
                print(f"✗ {nom_fr} (Introuvable sur API)")
        except:
            print(f"! Erreur réseau pour {nom_fr}")

        # Préparation JSON
        if cat not in final_json: final_json[cat] = []
        final_json[cat].append({
            "id": api_id,
            "nom": nom_fr,
            "prix": prix,
            "desc": desc,
            "image": filename
        })

    with open(os.path.join(DATA_PATH, "items.json"), "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)
    
    print(f"\nConfiguration terminée ! {len(items_data)} objets traités.")

if __name__ == "__main__":
    setup()