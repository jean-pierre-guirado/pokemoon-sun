import math

class ExperienceEngine:
    """
    Gère le calcul de l'expérience gagnée après un combat.
    Utilise la formule simplifiée des générations classiques.
    """

    @staticmethod
    def calculer_gain(p_joueur, p_ennemi, est_dresseur=False, partage_exp=False):
        """
        Calcule l'expérience gagnée par le Pokémon du joueur.
        Formule : EXP = (a * b * L) / (7 * s)
        
        a : 1.0 si sauvage, 1.5 si dresseur
        b : Expérience de base du Pokémon vaincu (donnée dans le pokedex)
        L : Niveau du Pokémon vaincu
        s : Nombre de Pokémon ayant participé (1 si combat solo sans partage)
        """
        
        # 1. Coefficient dresseur (a)
        a = 1.5 if est_dresseur else 1.0
        
        # 2. Expérience de base de l'espèce (b)
        # On cherche 'base_experience' ou on met 64 par défaut (moyenne des petits Pokémon)
        b = p_ennemi.get('base_experience') or p_ennemi.get('exp_base') or 64
        
        # 3. Niveau du vaincu (L)
        L = p_ennemi.get('niveau') or 5  # Défaut à 5 si non précisé
        
        # 4. Nombre de participants (s)
        s = 1 if not partage_exp else 2
        
        # Formule officielle simplifiée
        gain = (a * b * L) / (7 * s)
        
        return math.floor(gain)

    @staticmethod
    def verifier_niveau_sup(p_data):
        """
        Vérifie si le Pokémon a assez d'exp pour monter de niveau.
        Utilise la courbe de progression 'Moyenne' (Niveau^3).
        """
        lvl_actuel = p_data.get('niveau', 1)
        exp_actuelle = p_data.get('exp', 0)
        
        # Seuil pour le niveau suivant
        # Seuil = (Niveau + 1)^3
        seuil_suivant = math.pow(lvl_actuel + 1, 3)
        
        if exp_actuelle >= seuil_suivant:
            return True
        return False

# Exemple d'utilisation rapide si on lance le script seul
if __name__ == "__main__":
    # Simulation d'un Pokémon battu
    ennemi = {"nom": "Ratentif", "exp_base": 51, "niveau": 7}
    joueur = {"nom": "Vipélierre", "niveau": 5, "exp": 100}
    
    moteur = ExperienceEngine()
    gain = moteur.calculer_gain(joueur, ennemi)
    
    print(f"{joueur['nom']} a gagné {gain} points d'expérience !")