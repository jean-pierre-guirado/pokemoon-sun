import random
from core.table_type import TypeChart
from core.nature import NatureEngine

class CombatEngine:
    """Moteur de combat avec calculs de précision, critiques et multiplicateurs."""

    def __init__(self, pokemon_joueur, pokemon_adversaire):
        self.p1 = self._preparer_stats(pokemon_joueur)
        self.p2 = self._preparer_stats(pokemon_adversaire)

    def _preparer_stats(self, p_data):
        base_stats = p_data.get("stats", {})
        if "nature" in p_data:
            p_data["stats_finales"] = NatureEngine.apply_nature_to_stats(
                p_data["nature"], base_stats
            )
        else:
            p_data["stats_finales"] = base_stats.copy()
        return p_data

    def calculer_degats(self, attaquant, defenseur, capacite):
        """
        Renvoie : (dégâts, multiplicateur_type, est_critique, est_esquive)
        """
        # 1. Test de Précision (Miss/Esquive)
        precision_atk = capacite.get('precision', 100)
        if random.randint(1, 100) > precision_atk:
            return 0, 1.0, False, True

        # 2. Multiplicateur de Type
        type_atk = capacite.get('type', 'Normal')
        types_def = defenseur.get('types', ["Normal"])
        mult_type = TypeChart.get_multiplier(type_atk, types_def)

        if mult_type == 0:
            return 0, 0, False, False

        # 3. Coup Critique (6.25% de chance)
        est_critique = random.random() < 0.0625
        boost_crit = 1.5 if est_critique else 1.0

        # 4. Formule de Dégâts
        # 
        niveau = attaquant.get('niveau', 5)
        atk_stat = attaquant["stats_finales"].get("attaque", 50)
        def_stat = defenseur["stats_finales"].get("defense", 50)
        puissance = capacite.get('puissance', 40)
        stab = 1.5 if type_atk in attaquant.get('types', []) else 1.0
        
        base_dmg = (((2 * niveau / 5) + 2) * puissance * (atk_stat / def_stat) / 50) + 2
        
        # Aléatoire et calcul final
        random_mod = random.uniform(0.85, 1.0)
        final_dmg = int(base_dmg * stab * mult_type * boost_crit * random_mod)

        return max(1, final_dmg), mult_type, est_critique, False

    @staticmethod
    def est_ko(pokemon):
        return pokemon.get("pv_actuels", 0) <= 0