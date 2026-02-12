import json
import random
import sys
import os
import time

# Configuration des chemins
CORE_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\core"
DATA_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data"

sys.path.append(CORE_PATH)

# Importations de vos classes spécifiques
from table_type import PokemonType
from nature import PokemonNature  # Import de votre classe PokemonNature
from pokedex import Pokedex

class Combat:
    def __init__(self, pokemon_joueur, pokemon_adverse):
        """
        Gère le combat en utilisant l'efficacité des types ET l'influence des natures.
        """
        self.p1 = pokemon_joueur
        self.p2 = pokemon_adverse
        self.pokedex = Pokedex()
        
        # Le combat démarre dès l'instanciation
        self.demarrer_sequence_combat()

    def calculer_degats(self, attaquant, defenseur):
        """
        Méthode qui retire des PV en fonction de la défense, 
        du multiplicateur de type et de la nature.
        """
        # 1. Multiplicateur de Type (via table_type.py)
        mult_type = PokemonType.get_multiplier(attaquant['type'], defenseur['type'])
        
        # 2. Influence de la Nature (via nature.py)
        # On suppose que PokemonNature a une méthode pour récupérer le bonus
        # Par exemple : +10% d'attaque si la nature est favorable
        bonus_nature = 1.0
        if 'nature' in attaquant:
            # On appelle ici votre classe PokemonNature pour ajuster l'attaque
            bonus_nature = PokemonNature.get_multiplier(attaquant['nature'], "attaque")

        # 3. Calcul des dégâts finaux
        # Formule : ((Attaque * Nature) / (Défense / 5)) * Type
        attaque_finale = attaquant['attaque'] * bonus_nature
        defense_effective = max(1, defenseur['defense'] / 5)
        
        degats = (attaque_finale / defense_effective) * mult_type
        
        return round(degats)

    def demarrer_sequence_combat(self):
        print(f"\n--- DÉBUT DU COMBAT : {self.p1['nom']} vs {self.p2['nom']} ---")
        
        # Enregistrement de la rencontre dans le Pokédex
        self.pokedex.enregistrer_pokemon(self.p2)
        
        while self.p1['pv'] > 0 and self.p2['pv'] > 0:
            time.sleep(0.5)
            
            # TOUR DU JOUEUR
            if random.random() > 0.1: 
                dmg = self.calculer_degats(self.p1, self.p2)
                self.p2['pv'] -= dmg
                print(f"[*] {self.p1['nom']} attaque ! {dmg} dégâts.")
            else:
                print(f"[!] {self.p1['nom']} a loupé son attaque !")

            if self.p2['pv'] <= 0: break

            # TOUR DE L'ADVERSAIRE
            if random.random() > 0.1:
                dmg_adv = self.calculer_degats(self.p2, self.p1)
                self.p1['pv'] -= dmg_adv
                print(f"[*] {self.p2['nom']} riposte ! {dmg_adv} dégâts.")
            else:
                print(f"[!] {self.p2['nom']} a loupé sa riposte !")

        self.afficher_resultat()

    def afficher_resultat(self):
        if self.p1['pv'] <= 0:
            print(f"\nMessage : {self.p2['nom']} est le vainqueur !")
            print(f"Le Pokémon {self.p1['nom']} est KO.")
        else:
            print(f"\nMessage : {self.p1['nom']} est le vainqueur !")
            print(f"Le Pokémon {self.p2['nom']} est KO.")