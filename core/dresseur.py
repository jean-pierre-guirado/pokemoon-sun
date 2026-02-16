import json
import os

class DresseurManager:
    def __init__(self, config_name="dresseur_config.json"):
        # Définition des chemins
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.data_path = os.path.join(self.root_dir, "data")
        self.config_file = os.path.join(self.data_path, config_name)
        
        # S'assurer que le dossier data existe
        os.makedirs(self.data_path, exist_ok=True)
        
        # 1. Création automatique du JSON s'il est absent
        if not os.path.exists(self.config_file):
            self._creer_json_par_defaut()
        
        # 2. Chargement de la configuration
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        # 3. Chargement du Pokedex pour les stats de base
        self.pokedex_path = os.path.join(self.data_path, "pokemon_data.json")
        self.pokedex = {}
        if os.path.exists(self.pokedex_path):
            with open(self.pokedex_path, 'r', encoding='utf-8') as f:
                self.pokedex = json.load(f)

        self.nom = self.config["nom_dresseur"]
        self.inventaire = self.config["inventaire"]
        self.equipe = []
        self._preparer_equipe()

    def _creer_json_par_defaut(self):
        """Génère le fichier JSON avec tes 6 Pokémon et ton inventaire spécifique."""
        data_initiale = {
            "nom_dresseur": "Horus",
            "equipe": [
                {"nom": "Felinferno", "niveau": 50, "objet_tenu": "life-orb"},
                {"nom": "Brasegali", "niveau": 50, "objet_tenu": "focus-sash"},
                {"nom": "Oratoria", "niveau": 50, "objet_tenu": "leftovers"},
                {"nom": "Tortank", "niveau": 50, "objet_tenu": "rocky-helmet"},
                {"nom": "Feunard", "niveau": 50, "objet_tenu": "choice-band"},
                {"nom": "Aligatueur", "niveau": 50, "objet_tenu": "life-orb"}
            ],
            "inventaire": {
                "Balls": {
                    "poke-ball": 10,
                    "great-ball": 10,
                    "ultra-ball": 10,
                    "master-ball": 1
                },
                "Soins": {
                    "potion": 10,
                    "super-potion": 10,
                    "hyper-potion": 10,
                    "max-potion": 10,
                    "revive": 10,
                    "full-restore": 10
                }
            }
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data_initiale, f, indent=4, ensure_ascii=False)
        print(f"✓ Fichier {self.config_file} créé avec succès !")

    def _preparer_equipe(self):
        """Construit les objets Pokémon pour le combat."""
        for p_cfg in self.config["equipe"]:
            nom = p_cfg["nom"]
            # On récupère les stats de base depuis le pokedex ou valeurs par défaut
            p_data = self.pokedex.get(nom, {})
            stats_base = p_data.get("stats", {"hp": 80, "attaque": 80, "defense": 80})
            
            # Formule simplifiée Niveau 50
            hp_m = int(((stats_base.get("hp", 80) * 2) * 50 / 100) + 50 + 10)
            atk_f = int(((stats_base.get("attaque", 80) * 2) * 50 / 100) + 5)
            def_f = int(((stats_base.get("defense", 80) * 2) * 50 / 100) + 5)

            self.equipe.append({
                "nom": nom,
                "niveau": p_cfg["niveau"],
                "types": p_data.get("types", ["Normal"]),
                "max_hp": hp_m,
                "pv_actuels": hp_m,
                "objet_tenu": p_cfg["objet_tenu"],
                "stats_finales": {"attaque": atk_f, "defense": def_f},
                "capacites": ["Charge", "Vive-Attaque"] # À lier avec ton capacite_list.json plus tard
            })

    def sauvegarder_etat(self):
        """Permet de mettre à jour le JSON (ex: après avoir perdu des PV ou utilisé un objet)."""
        self.config["inventaire"] = self.inventaire
        # Note: On pourrait aussi sauvegarder les PV actuels ici
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_equipe(self):
        return self.equipe

    def get_sac(self):
        return self.inventaire

# Petit test si on lance le script directement
if __name__ == "__main__":
    manager = DresseurManager()
    print(f"Dresseur : {manager.nom}")
    print(f"Nombre de Pokémon : {len(manager.get_equipe())}")
    print(f"Nombre de Poké Balls : {manager.get_sac()['Balls']['poke-ball']}")