import os
import requests
import json
import time

# --- CONFIGURATION ---
BASE_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data"
INPUT_JSON = os.path.join(BASE_PATH, "pokemon_data.json")
OUTPUT_JSON = os.path.join(BASE_PATH, "capacite_list.json")
POKE_API_URL = "https://pokeapi.co/api/v2/pokemon/"

class MoveScraper:
    def __init__(self, input_file=INPUT_JSON, output_file=OUTPUT_JSON):
        self.input_file = input_file
        self.output_file = output_file
        self.move_cache = {}  # Pour éviter de télécharger 50 fois la même attaque

    def get_move_details(self, url):
        """Récupère les infos d'une attaque (Nom FR, Puissance, Type)"""
        if url in self.move_cache:
            return self.move_cache[url]

        try:
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                return None
            
            data = res.json()
            power = data.get('power')

            # On ne garde que les attaques qui font des dégâts (> 10)
            if power and power > 10:
                nom_fr = next((n['name'] for n in data['names'] if n['language']['name'] == 'fr'), data['name'])
                move_info = {
                    "nom_attaque": nom_fr,
                    "puissance": power,
                    "type": data['type']['name'].capitalize(),
                    "precision": data.get('accuracy'),
                    "pp": data.get('pp')
                }
                self.move_cache[url] = move_info
                return move_info
            
            self.move_cache[url] = None # Cache pour les attaques non-offensives
            return None
        except Exception as e:
            print(f"Erreur API Move: {e}")
            return None

    def run(self):
        if not os.path.exists(self.input_file):
            print(f"Erreur : {self.input_file} introuvable !")
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            pokedex = json.load(f)

        all_moves_final = []
        total_pkmn = len(pokedex)
        
        print(f"🚀 Scan des capacités pour {total_pkmn} Pokémon...")

        for nom_fr, infos in pokedex.items():
            api_name = infos.get("nom_api")
            if not api_name: continue

            print(f"-> Extraction : {nom_fr}...")
            try:
                r = requests.get(f"{POKE_API_URL}{api_name}", timeout=5)
                if r.status_code != 200: continue
                
                pk_data = r.json()
                
                for m_entry in pk_data['moves']:
                    # On récupère le détail de l'attaque
                    move_url = m_entry['move']['url']
                    move_details = self.get_move_details(move_url)
                    
                    if move_details:
                        # On crée une entrée liée à ce Pokémon
                        move_entry = {
                            "pokemon": nom_fr,
                            "nom_attaque": move_details["nom_attaque"],
                            "puissance": move_details["puissance"],
                            "type": move_details["type"],
                            "precision": move_details["precision"],
                            "pp": move_details["pp"]
                        }
                        all_moves_final.append(move_entry)
                        
                    # Petite pause pour ne pas surcharger l'API
                    time.sleep(0.02)

            except Exception as e:
                print(f" ! Erreur sur {nom_fr} : {e}")

        # Sauvegarde
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(all_moves_final, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ Terminé ! {len(all_moves_final)} capacités sauvegardées dans {self.output_file}")

if __name__ == "__main__":
    scraper = MoveScraper()
    scraper.run()