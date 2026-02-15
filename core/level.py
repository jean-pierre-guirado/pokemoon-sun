import math
import json
import os
from core.exp import ExperienceEngine

# Chemin vers les données pour recalculer les stats à chaque up
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "pokemon_data.json")

class LevelEngine:
    """
    Gère la montée en niveau, les courbes d'expérience et 
    la mise à jour proportionnelle des statistiques.
    """

    COURBES = {
        "rapide": lambda n: (4 * math.pow(n, 3)) / 5,
        "moyen": lambda n: math.pow(n, 3),
        "parabolique": lambda n: (1.2 * math.pow(n, 3)) - (15 * math.pow(n, 2)) + (100 * n) - 140,
        "lent": lambda n: (5 * math.pow(n, 3)) / 4
    }

    @staticmethod
    def exp_pour_niveau(niveau, courbe="moyen"):
        if niveau <= 1: return 0
        formule = LevelEngine.COURBES.get(courbe, LevelEngine.COURBES["moyen"])
        return math.floor(formule(niveau))

    @staticmethod
    def recalculer_stats(p_data):
        """
        Recalcule les stats proportionnellement au niveau.
        Formule simplifiée : Stat = ((Base * 2 * Niveau) / 100) + Constante
        """
        # On essaie de recharger les bases depuis le JSON si possible
        try:
            with open(DATA_PATH, 'r', encoding='utf-8') as f:
                pokedex = json.load(f)
            bases = pokedex[p_data['nom']].get('stats', pokedex[p_data['nom']])
        except:
            # Valeurs par défaut si le fichier est inaccessible
            bases = {"hp": 50, "attaque": 50, "defense": 50}

        niveau = p_data['niveau']
        
        # Mise à jour des PV Max
        ancienne_max_hp = p_data.get('max_hp', 10)
        base_hp = bases.get('hp') or bases.get('pv') or 50
        p_data['max_hp'] = int(((base_hp * 2 * niveau) / 100) + niveau + 10)
        
        # Soin lors de la montée de niveau (différence des PV max)
        diff_hp = p_data['max_hp'] - ancienne_max_hp
        p_data['pv_actuels'] += max(0, diff_hp)

        # Mise à jour Attaque et Défense
        base_atk = bases.get('attaque') or bases.get('attack') or 50
        base_def = bases.get('defense') or 50
        
        # Initialise le dictionnaire de stats s'il n'existe pas
        if 'stats' not in p_data: p_data['stats'] = {}
        
        p_data['stats']['attaque'] = int(((base_atk * 2 * niveau) / 100) + 5)
        p_data['stats']['defense'] = int(((base_def * 2 * niveau) / 100) + 5)

    @staticmethod
    def appliquer_gain_et_check(p_data, p_ennemi, est_dresseur=False):
        """
        Calcule le gain, l'ajoute, gère les montées de niveaux multiples 
        et met à jour les stats à chaque fois.
        """
        gain = ExperienceEngine.calculer_gain(p_data, p_ennemi, est_dresseur)
        p_data['exp'] = p_data.get('exp', 0) + gain
        
        a_monte = False
        while True:
            niveau_suivant = p_data.get('niveau', 1) + 1
            exp_requise = LevelEngine.exp_pour_niveau(niveau_suivant, p_data.get('courbe', 'moyen'))
            
            if p_data['exp'] >= exp_requise:
                p_data['niveau'] = niveau_suivant
                a_monte = True
                # CRITIQUE : On recalcule les stats pour que le niveau ait un impact !
                LevelEngine.recalculer_stats(p_data)
                print(f"🎉 {p_data['nom']} monte au niveau {p_data['niveau']} !")
            else:
                break
                
        return gain, a_monte

# --- TEST ---
if __name__ == "__main__":
    # On simule un Salamèche niveau 5 qui bat un ennemi très fort
    mon_pkm = {
        "nom": "Salameche", 
        "niveau": 5, 
        "exp": 125, 
        "courbe": "moyen",
        "max_hp": 20,
        "pv_actuels": 20,
        "stats": {"attaque": 12, "defense": 10}
    }
    
    # Ennemi niveau 50 pour forcer un gros gain
    ennemi_vaincu = {"nom": "Dracaufeu", "exp_base": 240, "niveau": 50}
    
    print(f"AVANT : Niveau {mon_pkm['niveau']} | PV Max: {mon_pkm['max_hp']} | Atk: {mon_pkm['stats']['attaque']}")
    
    gain, up = LevelEngine.appliquer_gain_et_check(mon_pkm, ennemi_vaincu)
    
    print(f"GAIN : +{gain} EXP")
    print(f"APRÈS : Niveau {mon_pkm['niveau']} | PV Max: {mon_pkm['max_hp']} | Atk: {mon_pkm['stats']['attaque']}")