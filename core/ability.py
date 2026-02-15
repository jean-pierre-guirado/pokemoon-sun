import os
import requests
import json
import time

# --- CONFIGURATION ---
BASE_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data"
INPUT_JSON = os.path.join(BASE_PATH, "pokemon_data.json")
OUTPUT_JSON = os.path.join(BASE_PATH, "pokemon_abilities_full.json")
API_URL = "https://pokeapi.co/api/v2/pokemon/"

class AbilityScraperFromJSON:
    def __init__(self):
        self.abilities_data = {}

    def get_ability_info(self, url):
        """Récupère le nom et la description FR d'un talent"""
        try:
            res = requests.get(url)
            if res.status_code != 200:
                return None, None
            
            data = res.json()
            # Nom en français
            nom_fr = next((n['name'] for n in data['names'] if n['language']['name'] == 'fr'), data['name'])
            
            # Description en français (Priorité short_effect, sinon flavor_text)
            desc_fr = next((e['short_effect'] for e in data.get('effect_entries', []) if e['language']['name'] == 'fr'), None)
            if not desc_fr:
                desc_fr = next((f['flavor_text'] for f in data.get('flavor_text_entries', []) if f['language']['name'] == 'fr'), "Description non disponible.")
            
            return nom_fr, desc_fr.replace("\n", " ")
        except Exception as e:
            print(f"Erreur talent : {e}")
            return None, None

    def run(self):
        # 1. Charger ton fichier existant
        if not os.path.exists(INPUT_JSON):
            print(f"Erreur : {INPUT_JSON} introuvable !")
            return

        with open(INPUT_JSON, 'r', encoding='utf-8') as f:
            pokedex = json.load(f)

        print(f"--- Début de l'extraction pour {len(pokedex)} Pokémon ---")

        for nom_fr, infos in pokedex.items():
            api_name = infos.get("nom_api")
            if not api_name:
                continue

            print(f"Récupération des talents pour : {nom_fr} ({api_name})...")
            
            try:
                res = requests.get(f"{API_URL}{api_name}")
                if res.status_code == 200:
                    pk_data = res.json()
                    talents_liste = []
                    
                    # Logique de probabilité
                    normal_slots = [a for a in pk_data['abilities'] if not a['is_hidden']]
                    prob_normal = 100 if len(normal_slots) == 1 else 50

                    for ab in pk_data['abilities']:
                        n_fr, d_fr = self.get_ability_info(ab['ability']['url'])
                        
                        talents_liste.append({
                            "nom": n_fr,
                            "description": d_fr,
                            "is_hidden": ab['is_hidden'],
                            "probabilite": "Rare (Caché)" if ab['is_hidden'] else f"{prob_normal}%"
                        })

                    # On stocke le résultat
                    self.abilities_data[nom_fr] = {
                        "id": infos["id"],
                        "nom_api": api_name,
                        "talents": talents_liste
                    }
                else:
                    print(f" ! Impossible de trouver {api_name} sur l'API.")

                # Petite pause pour ne pas spammer l'API
                time.sleep(0.1)

            except Exception as e:
                print(f" ! Erreur sur {nom_fr} : {e}")

        # 2. Sauvegarder le nouveau JSON
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(self.abilities_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n--- Terminé ! Fichier créé : {OUTPUT_JSON} ---")

if __name__ == "__main__":
    scraper = AbilityScraperFromJSON()
    scraper.run()