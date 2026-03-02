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
            if not data: return None

            # --- FILTRES D'EXCLUSION (Météo et Champs) ---
            move_name = data.get('name', '')
            
            # Sécurité sur meta
            meta = data.get('meta')
            meta_category = meta.get('category', {}).get('name', '') if meta else ''
            
            exclusions = [
                'rain-dance', 'sunny-day', 'sandstorm', 'hail', 'snowscape',
                'electric-terrain', 'grassy-terrain', 'misty-terrain', 'psychic-terrain',
                'weather-ball', 'solar-beam', 'solar-blade', 'aurora-veil', 'morning-sun', 'synthesis', 'moonlight'
            ]
            
            excluded_categories = ['weather', 'field-effects']

            if any(excl in move_name for excl in exclusions) or meta_category in excluded_categories:
                return None

            nom_fr = next((n['name'] for n in data.get('names', []) if n['language']['name'] == 'fr'), data.get('name'))
            
            cat_api = data.get('damage_class', {}).get('name', 'status')
            categorie = "Statut" if cat_api == "status" else ("Spécial" if cat_api == "special" else "Physique")
            
            effet_data = self._analyser_effet_complexe(data)

            type_raw = data.get('type', {}).get('name', 'normal').lower()
            type_final = "electrick" if type_raw == "electric" else type_raw

            move_info = {
                "nom_attaque": nom_fr,
                "puissance": data.get('power'),
                "type": type_final,
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
            # On affiche l'erreur mais on ne bloque pas le script
            print(f"  ! Erreur sur l'attaque ({url.split('/')[-2]}) : {e}")
            return None

    def _analyser_effet_complexe(self, data):
        res = {"type_effet": "DAMAGE", "stat": None, "valeur": 0, "chance": 100}
        meta = data.get('meta')
        if not meta: return res
        
        # 1. Statuts
        ailment_data = meta.get('ailment')
        ailment = ailment_data.get('name', 'none') if ailment_data else 'none'
        
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
            res["valeur"] = change.get('change', 0)
            s_map = {"special-attack": "attaque_spe", "special-defense": "defense_spe", 
                     "attack": "attaque", "defense": "defense", "speed": "vitesse"}
            stat_name = change.get('stat', {}).get('name', '')
            res["stat"] = s_map.get(stat_name, stat_name)
            
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
        if not os.path.exists(self.input_file):
            print(f"Fichier d'entrée introuvable : {self.input_file}")
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            pokedex = json.load(f)

        all_moves_final = []
        # On utilise une liste de noms pour éviter les doublons d'attaques
        seen_moves_names = set()

        for idx, (nom_fr, infos) in enumerate(pokedex.items(), 1):
            api_name = infos.get("nom_api")
            if not api_name: continue
            print(f"[{idx}] Extraction : {nom_fr}...")
            try:
                r = self.session.get(f"{POKE_API_URL}{api_name}", timeout=10)
                if r.status_code != 200: continue
                pk_data = r.json()
                
                for m_entry in pk_data.get('moves', []):
                    move_details = self.get_move_details(m_entry['move']['url'])
                    
                    if move_details and move_details['nom_attaque'] not in seen_moves_names:
                        all_moves_final.append(move_details)
                        seen_moves_names.add(move_details['nom_attaque'])
                
                time.sleep(0.05)
            except Exception as e:
                print(f"Erreur sur Pokemon {nom_fr}: {e}")
                continue

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(all_moves_final, f, ensure_ascii=False, indent=4)
        print(f"--- Terminé ! {len(all_moves_final)} attaques récupérées ---")

if __name__ == "__main__":
    scraper = MoveScraper()
    scraper.run()