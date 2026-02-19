import math
import random

from core.utils import normaliser
from core.table_type import TypeChart


# ---------------------------------------------------------------------------
# LevelEngine
# ---------------------------------------------------------------------------

class LevelEngine:
    @staticmethod
    def recalculer_stats(p_data, poke_data_map):
        """Recalcule les stats d'un Pokémon après un level-up.

        Args:
            p_data (dict): Dictionnaire représentant le Pokémon (modifié en place).
            poke_data_map (dict): Base de données des stats de base.

        Returns:
            dict: Gains par stat (hp, attaque, defense, vitesse).
        """
        anciennes_stats = {
            "hp":       p_data.get('hp_base', 10),
            "attaque":  p_data.get('stats', {}).get('attaque', 5),
            "defense":  p_data.get('stats', {}).get('defense', 5),
            "vitesse":  p_data.get('stats', {}).get('vitesse', 5),
        }

        target = normaliser(p_data.get('nom', ''))
        bases = {"hp": 50, "attaque": 50, "defense": 50, "vitesse": 50}
        for k, v in poke_data_map.items():
            if normaliser(k) == target:
                bases = v.get('stats', v)
                break

        niveau = p_data['niveau']
        base_hp = bases.get('hp') or bases.get('pv') or 50
        p_data['hp_base'] = math.floor(((2 * base_hp) * niveau) / 100) + niveau + 10

        diff_hp = p_data['hp_base'] - anciennes_stats["hp"]
        p_data['hp_actuel'] = p_data.get('hp_actuel', 0) + max(0, diff_hp)

        gains = {"hp": diff_hp}
        for s_nom in ['attaque', 'defense', 'vitesse']:
            b_val = bases.get(s_nom, 50)
            n_val = math.floor(((2 * b_val) * niveau) / 100) + 5
            gains[s_nom] = n_val - anciennes_stats.get(s_nom, 5)
            p_data['stats'][s_nom] = n_val

        return gains


# ---------------------------------------------------------------------------
# ExperienceEngine
# ---------------------------------------------------------------------------

class ExperienceEngine:
    @staticmethod
    def calculer_xp_gagne(ennemi):
        """Retourne l'XP gagnée en battant l'ennemi donné."""
        return ennemi.niveau * random.randint(15, 25)


# ---------------------------------------------------------------------------
# CombatEngine
# ---------------------------------------------------------------------------

class CombatEngine:
    @staticmethod
    def _get_stat_multiplicateur(stage):
        return (2 + stage) / 2 if stage >= 0 else 2 / (2 + abs(stage))

    @staticmethod
    def _get_stat_actuelle(pokemon, stat_nom):
        base = pokemon.stats.get(stat_nom, 50)
        mult = CombatEngine._get_stat_multiplicateur(pokemon.stages.get(stat_nom, 0))
        return base * mult

    @staticmethod
    def get_effectiveness_text(multiplier):
        if multiplier >= 1.9:
            return "C'est super efficace !"
        if 0 < multiplier <= 0.6:
            return "Ce n'est pas très efficace..."
        if multiplier == 0:
            return "Ça n'affecte pas l'adversaire..."
        return ""

    @staticmethod
    def calculer_degats(attaquant, defenseur, move_data):
        """Calcule les dégâts infligés et applique les effets de statut secondaires.

        Returns:
            tuple: (dégâts, multiplicateur_type, critique, raté, message)
        """
        capa = move_data

        # Paralysie — blocage du tour
        if attaquant.statut == "Paralysie" and random.random() < 0.25:
            return 0, 1.0, False, False, "Est totalement paralysé !"

        # Précision
        acc = capa.get('precision', 100) or 100
        if random.randint(1, 100) > acc:
            return 0, 1.0, False, True, "L'attaque a échoué !"

        pui    = capa.get('puissance', 0)
        t_atk  = capa.get('type', 'Normal')
        mult_type = TypeChart.get_multiplier(t_atk, defenseur.types)
        eff_txt   = CombatEngine.get_effectiveness_text(mult_type)

        cat = capa.get('categorie', 'Physique')
        if cat == 'Status' or not pui or pui == 0:
            msg_effet = StatusEngine.appliquer_effet_technique(attaquant, defenseur, capa)
            return 0, mult_type, False, False, f"{eff_txt}\n{msg_effet}".strip()

        if mult_type == 0:
            return 0, 0.0, False, False, eff_txt

        crit   = random.random() < 0.0625
        b_crit = 1.5 if crit else 1.0

        a = CombatEngine._get_stat_actuelle(attaquant, "attaque")
        d = CombatEngine._get_stat_actuelle(defenseur, "defense")
        if attaquant.statut == "Brûlure":
            a *= 0.5

        lvl  = attaquant.niveau
        stab = 1.5 if t_atk in attaquant.types else 1.0
        dmg_brut  = (((2 * lvl / 5) + 2) * pui * (a / d) / 50) + 2
        dmg_final = int(dmg_brut * b_crit * random.uniform(0.85, 1.0) * stab * mult_type)
        dmg_final = max(1, dmg_final)

        msg_extra = eff_txt
        if crit:
            msg_extra = f"Coup critique !\n{eff_txt}".strip()

        if capa.get('chance_effet', 0) > 0 or capa.get('effet', 'DAMAGE') != "DAMAGE":
            res_tech = StatusEngine.appliquer_effet_technique(attaquant, defenseur, capa)
            if res_tech:
                msg_extra = f"{msg_extra}\n{res_tech}".strip()

        return dmg_final, mult_type, crit, False, msg_extra


# ---------------------------------------------------------------------------
# StatusEngine
# ---------------------------------------------------------------------------

class StatusEngine:
    @staticmethod
    def modifier_stage(p, stat, q):
        actuel  = p.stages.get(stat, 0)
        nouveau = max(-6, min(6, actuel + q))
        p.stages[stat] = nouveau
        if nouveau == actuel:
            return f"La {stat} de {p.nom} ne change plus."
        v     = "augmente" if q > 0 else "baisse"
        force = " fortement" if abs(q) >= 2 else ""
        return f"{stat.replace('_', ' ').capitalize()} de {p.nom} {v}{force} !"

    @staticmethod
    def appliquer_effet_technique(att, defs, capa):
        eff    = capa.get('effet')
        nom    = capa.get('nom_attaque', '').lower()
        val    = capa.get('valeur_stat', 1)
        stat_t = capa.get('stat_touchee')
        chance = capa.get('chance_effet', 100)

        if random.randint(1, 100) > (chance or 100):
            return ""

        if eff == "HEAL_SELF":
            att.hp = min(att.hp_base, att.hp + (att.hp_base // 2))
            return f"{att.nom} se soigne !"
        if eff == "BOOST_SELF" and stat_t:
            return StatusEngine.modifier_stage(att, stat_t, val)
        if eff == "DEBUFF_ENEMY" and stat_t:
            return StatusEngine.modifier_stage(defs, stat_t, val)
        if "danse lames" in nom:
            return StatusEngine.modifier_stage(att, "attaque", 2)
        if "machination" in nom:
            return StatusEngine.modifier_stage(att, "attaque_spe", 2)
        if "rugissement" in nom:
            return StatusEngine.modifier_stage(defs, "attaque", -1)
        if "grimace" in nom:
            return StatusEngine.modifier_stage(defs, "vitesse", -2)
        if eff in ["TOXIC", "POISON", "BURN", "PARALYZE"]:
            if defs.statut is None:
                m = {"TOXIC": "Toxique", "POISON": "Poison", "BURN": "Brûlure", "PARALYZE": "Paralysie"}
                defs.statut = m[eff]
                return f"{defs.nom} est {m[eff].lower()} !"
        return ""

    @staticmethod
    def gerer_fin_de_tour(p):
        if not p.statut or p.hp <= 0:
            return None
        d = 0
        if p.statut == "Brûlure":
            d = p.hp_base // 16
        elif p.statut == "Poison":
            d = p.hp_base // 8
        elif p.statut == "Toxique":
            p.compteur_toxic += 1
            d = (p.hp_base // 16) * p.compteur_toxic
        if d > 0:
            p.hp = max(0, p.hp - int(d))
            return f"{p.nom} souffre de son statut !"
        return None


# ---------------------------------------------------------------------------
# ItemEngine
# ---------------------------------------------------------------------------

class ItemEngine:
    @staticmethod
    def utiliser_objet(item_nom, pokemon):
        """Applique l'effet d'un objet de soin sur un Pokémon.

        Returns:
            tuple: (succès: bool, message: str)
        """
        nom = item_nom.lower().strip()

        if "bonbon" in nom or "rare-candy" in nom:
            logs = pokemon.gain_xp(pokemon.xp_max)
            return True, "\n".join(logs) if logs else "Niveau up !"

        if "potion" in nom:
            if pokemon.hp <= 0:
                return False, f"{pokemon.nom} est KO !"
            if pokemon.hp >= pokemon.hp_base:
                return False, "Deja full PV !"
            soin = 200 if "hyper" in nom else 50 if "super" in nom else 20
            if "max" in nom:
                soin = pokemon.hp_base
            old = pokemon.hp
            pokemon.hp = min(pokemon.hp_base, pokemon.hp + soin)
            return True, f"{pokemon.nom} soigne de {int(pokemon.hp - old)} PV."

        if "rappel" in nom or "revive" in nom:
            if pokemon.hp <= 0:
                pokemon.hp = pokemon.hp_base // 2
                if "max" in nom:
                    pokemon.hp = pokemon.hp_base
                return True, f"{pokemon.nom} est reanime !"
            return False, f"{pokemon.nom} n'est pas KO !"

        return False, "Aucun effet."

    @staticmethod
    def tenter_capture(ball_nom, ennemi):
        """Tente de capturer l'ennemi avec la Poké Ball donnée.

        Returns:
            bool: True si la capture réussit.
        """
        nom = ball_nom.lower().strip()
        if "master" in nom:
            return True
        taux_pv = ennemi.hp / ennemi.hp_base
        chance  = 0.3
        if "hyper" in nom or "ultra" in nom:
            chance = 0.6
        elif "super" in nom or "great" in nom:
            chance = 0.4
        chance += (1.0 - taux_pv) * 0.3
        return random.random() < chance
