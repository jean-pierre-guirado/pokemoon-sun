import json
import os

class Pokedex:
    def __init__(self):
        self.path = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data\pokedex.json"
        self.data_source = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data\pokemon_data.json"
        self.pokedex = self._charger_pokedex()

    def _charger_pokedex(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"vus": [], "captures": []}

    def enregistrer_rencontre(self, pokemon_obj, a_ete_capture=False):
        """Enregistre un Pokémon s'il n'est pas déjà présent."""
        noms_vus = [p['nom'] for p in self.pokedex['vus']]
        
        if pokemon_obj['nom'] not in noms_vus:
            nouvelle_entree = {
                "nom": pokemon_obj['nom'],
                "type": pokemon_obj['type'],
                "defense": pokemon_obj['defense'],
                "attaque": pokemon_obj['attaque'],
                "pv_max": pokemon_obj['pv']
            }
            self.pokedex['vus'].append(nouvelle_entree)
            print(f"--- {pokemon_obj['nom']} ajouté au Pokédex ! ---")

        if a_ete_capture and pokemon_obj['nom'] not in self.pokedex['captures']:
            self.pokedex['captures'].append(pokemon_obj['nom'])

        self._sauvegarder()

    def _sauvegarder(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.pokedex, f, indent=4, ensure_ascii=False)

    def afficher_pokedex(self):
        print("\n--- ÉTAT DU POKÉDEX ---")
        print(f"Nombre de Pokémon rencontrés : {len(self.pokedex['vus'])}")
        for p in self.pokedex['vus']:
            statut = "O" if p['nom'] in self.pokedex['captures'] else "X"
            print(f"[{statut}] {p['nom']} | Type: {p['type']} | PV: {p['pv_max']}")
        print("------------------------\n")