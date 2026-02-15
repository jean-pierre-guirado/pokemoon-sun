import json
import os

class Pokedex:
    def __init__(self):
        # Chemins vers tes fichiers
        self.base_path = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data"
        self.pokedex_file = os.path.join(self.base_path, "pokedex.json")
        self.source_file = os.path.join(self.base_path, "pokemon_data.json")
        
        # Chargement des données existantes
        self.pokedex = self._charger_pokedex()

    def _charger_pokedex(self):
        """Charge le pokedex.json ou en crée un nouveau s'il n'existe pas."""
        if os.path.exists(self.pokedex_file):
            with open(self.pokedex_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return [] # Le Pokédex final reste une liste pour faciliter l'affichage

    def _recuperer_infos_source(self, nom_pokemon):
        """Va chercher les infos directement dans le dictionnaire source."""
        if os.path.exists(self.source_file):
            with open(self.source_file, 'r', encoding='utf-8') as f:
                data_source = json.load(f)
                
                # Accès direct car le nom est la clé du dictionnaire
                # On utilise .get() pour éviter de planter si le nom n'existe pas
                infos = data_source.get(nom_pokemon)
                if infos:
                    # On rajoute manuellement le nom dans l'objet pour le Pokédex
                    infos['nom_final'] = nom_pokemon
                    return infos
        return None

    def enregistrer_rencontre(self, nom_pokemon):
        """Enregistre un Pokémon s'il n'est pas déjà présent."""
        # Vérification des doublons (insensible à la casse)
        noms_existants = [p['nom'].lower() for p in self.pokedex]
        
        if nom_pokemon.lower() in noms_existants:
            # On ne print rien ici pour ne pas polluer la console de combat
            return

        # Récupération des données
        infos = self._recuperer_infos_source(nom_pokemon)
        
        if infos:
            # Extraction selon TA structure (stats est un sous-dictionnaire)
            stats = infos.get('stats', {})
            
            nouvelle_entree = {
                "nom": infos['nom_final'],
                "type": infos['types'][0], # Premier type
                "defense": stats.get('defense', 0),
                "attaque": stats.get('attaque', 0),
                "pv": stats.get('hp', 0) # Ton JSON utilise 'hp'
            }
            
            self.pokedex.append(nouvelle_entree)
            self._sauvegarder()
            print(f"✨ {infos['nom_final']} a été ajouté à votre Pokédex !")
        else:
            print(f"⚠️ Données source introuvables pour : {nom_pokemon}")

    def _sauvegarder(self):
        """Sauvegarde l'état actuel dans pokedex.json."""
        with open(self.pokedex_file, 'w', encoding='utf-8') as f:
            json.dump(self.pokedex, f, indent=4, ensure_ascii=False)

    def afficher_pokedex(self):
        """Affiche le contenu du Pokédex."""
        print("\n" + "="*40)
        print(f"        VOTRE POKÉDEX ({len(self.pokedex)} Pokémon)")
        print("="*40)
        
        if not self.pokedex:
            print("Le Pokédex est vide pour le moment.")
        else:
            for p in self.pokedex:
                print(f"Nom: {p['nom']} | Type: {p['type']}")
                print(f"Stats -> ATQ: {p['attaque']} | DEF: {p['defense']} | PV: {p['pv']}")
                print("-" * 30)
        print("="*40 + "\n")