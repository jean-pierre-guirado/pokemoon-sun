import os
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIGURATION ---
BASE_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data"
INPUT_JSON = os.path.join(BASE_PATH, "pokemon_data.json")
OUTPUT_JSON = os.path.join(BASE_PATH, "capacite_list.json")
POKE_API_URL = "https://pokeapi.co/api/v2/pokemon/"

class MoveScraper:
    def __init__(self, input_file=INPUT_JSON, output_file=OUTPUT_JSON):
        self.input_file = input_file
        self.output_file = output_file
        self.move_cache = {}
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def get_move_details(self, url):
        if url in self.move_cache:
            return self.move_cache[url]

        try:
            res = self.session.get(url, timeout=10)
            if res.status_code != 200: return None
            
            data = res.json()
            nom_fr = next((n['name'] for n in data['names'] if n['language']['name'] == 'fr'), data['name'])
            
            cat_api = data.get('damage_class', {}).get('name', 'status')
            categorie = "Statut" if cat_api == "status" else ("Spécial" if cat_api == "special" else "Physique")
            
            effet_data = self._analyser_effet_complexe(data)

            # --- LOGIQUE D'ASSOCIATION DES IMAGES ---
            # On récupère le nom anglais technique (ex: 'water', 'fire', 'electric')
            # C'est ce nom qui permet de faire le lien avec tes fichiers PNG
            type_raw = data['type']['name'].lower()
            
            # Correction spécifique pour correspondre à tes fichiers "electrick.png" si nécessaire
            if type_raw == "electric":
                type_final = "electrick"
            else:
                type_final = type_raw

            move_info = {
                "nom_attaque": nom_fr,
                "puissance": data.get('power'),
                "type": type_final, # Stocké en minuscule pour le mapping image
                "precision": data.get('accuracy'),
                "pp": data.get('pp'),
                "categorie": categorie,
                "effet": effet_data["type_effet"],
                "stat_touchee": effet_data["stat"],
                "valeur_stat": effet_data["valeur"],
                "chance_effet": effet_data["chance"]
            }
            
            self.move_cache[url] = move_info
            return move_info
            
        except Exception as e:
            print(f"  ! Erreur sur l'attaque ({url.split('/')[-2]}) : {e}")
            return None

    def _analyser_effet_complexe(self, data):
        res = {"type_effet": "DAMAGE", "stat": None, "valeur": 0, "chance": 100}
        meta = data.get('meta', {})
        if not meta: return res
        
        # 1. Statuts
        ailment = meta.get('ailment', {}).get('name', 'none')
        status_map = {
            'paralysis': "PARALYZE", 'burn': "BURN", 'poison': "POISON", 
            'toxic': "TOXIC", 'sleep': "SLEEP", 'freeze': "FREEZE"
        }
        
        if ailment in status_map:
            res["type_effet"] = status_map[ailment]
            res["chance"] = meta.get('ailment_chance', 100) or 100

        # 2. Stats (Boosts/Debuffs)
        stats_changes = data.get('stat_changes', [])
        if stats_changes:
            change = stats_changes[0]
            res["valeur"] = change['change']
            s_map = {"special-attack": "attaque_spe", "special-defense": "defense_spe", 
                     "attack": "attaque", "defense": "defense", "speed": "vitesse"}
            res["stat"] = s_map.get(change['stat']['name'], change['stat']['name'])
            
            # Logique : Si valeur positive -> Boost lanceur, sinon Debuff ennemi
            if res["valeur"] > 0:
                res["type_effet"] = "BOOST_SELF"
            else:
                res["type_effet"] = "DEBUFF_ENEMY"
            
            res["chance"] = meta.get('stat_chance', 100) or 100

        if meta.get('category', {}).get('name') == 'healing':
            res["type_effet"] = "HEAL_SELF"

        return res

    def run(self):
        print("--- Démarrage de l'extraction ---")
        if not os.path.exists(self.input_file): return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            pokedex = json.load(f)

        all_moves_final = []
        for idx, (nom_fr, infos) in enumerate(pokedex.items(), 1):
            api_name = infos.get("nom_api")
            if not api_name: continue
            print(f"[{idx}] Extraction : {nom_fr}...")
            try:
                r = self.session.get(f"{POKE_API_URL}{api_name}", timeout=10)
                if r.status_code != 200: continue
                pk_data = r.json()
                for m_entry in pk_data['moves']:
                    move_details = self.get_move_details(m_entry['move']['url'])
                    if move_details and move_details not in all_moves_final:
                        all_moves_final.append(move_details)
                time.sleep(0.05)
            except: continue

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(all_moves_final, f, ensure_ascii=False, indent=4)
        print("--- Terminé ! ---")

if __name__ == "__main__":
    scraper = MoveScraper()
    scraper.run()