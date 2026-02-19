import random


class CaptureEngine:
    """Moteur de capture Pokémon avec taux différenciés par type de Ball."""

    # Taux de base par type de ball (multiplicateur sur la chance)
    BALL_RATES = {
        "master-ball":  2.0,   # Capture garantie (flag spécial)
        "ultra-ball":   2.0,
        "hyper-ball":   2.0,   # alias
        "great-ball":   1.5,
        "super-ball":   1.5,   # alias
        "poke-ball":    1.0,
        "premier-ball": 1.0,
        "luxury-ball":  1.0,
        "quick-ball":   2.0,   # bonus tour 1 (géré séparément si besoin)
        "timer-ball":   1.0,   # augmente avec les tours (simplifié à 1.0)
        "net-ball":     1.0,   # bonus Eau/Insecte (simplifié)
        "dusk-ball":    1.0,
    }

    @classmethod
    def _get_ball_rate(cls, ball_nom: str) -> float:
        """Retourne le multiplicateur de la ball, avec fallback à 1.0."""
        nom = ball_nom.lower().strip()
        # Recherche exacte d'abord
        if nom in cls.BALL_RATES:
            return cls.BALL_RATES[nom]
        # Recherche par mot-clé
        if "master" in nom: return 2.0
        if "ultra" in nom or "hyper" in nom: return 2.0
        if "great" in nom or "super" in nom: return 1.5
        return 1.0

    @classmethod
    def tenter_capture(cls, ball_nom: str, ennemi, tour: int = 1) -> tuple[bool, str]:
        """Tente de capturer l'ennemi avec la ball donnée.

        La formule tient compte de :
        - Le type de ball (multiplicateur)
        - Les PV restants de l'ennemi (moins il a de PV, plus c'est facile)
        - Le statut de l'ennemi (Sommeil/Gelé = +bonus)
        - Le niveau de l'ennemi (plus il est haut, plus c'est difficile)

        Args:
            ball_nom: Nom de la ball utilisée.
            ennemi: Instance Pokemon de l'ennemi.
            tour: Numéro du tour actuel (utile pour Timer Ball, Quick Ball).

        Returns:
            tuple: (succès: bool, message: str)
        """
        nom = ball_nom.lower().strip()

        # Master Ball : capture garantie
        if "master" in nom:
            return True, "La Master Ball ne rate jamais !"

        ball_mult = cls._get_ball_rate(nom)

        # Bonus Quick Ball au tour 1
        if "quick" in nom and tour == 1:
            ball_mult = 4.0

        # Bonus Timer Ball (augmente avec les tours, max x4)
        if "timer" in nom:
            ball_mult = min(4.0, 1.0 + (tour * 0.3))

        # Ratio PV : 0 PV restant = max bonus, PV max = aucun bonus
        hp_ratio = max(0.0, ennemi.hp / max(1, ennemi.hp_base))
        # Formule inspirée des jeux : plus le ratio est bas, mieux c'est
        pv_bonus = 1.0 - (hp_ratio * 0.7)  # entre 0.3 (full PV) et 1.0 (0 PV)

        # Bonus de statut
        statut_bonus = 1.0
        if ennemi.statut in ("Sommeil", "Gelé"):
            statut_bonus = 2.0
        elif ennemi.statut in ("Paralysie", "Brûlure", "Poison", "Toxique"):
            statut_bonus = 1.5

        # Malus de niveau (pokémons haut niveau = plus dur à capturer)
        niveau_malus = max(0.4, 1.0 - (ennemi.niveau * 0.005))

        # Chance finale (capped à 95%)
        chance = min(0.95, 0.25 * ball_mult * pv_bonus * statut_bonus * niveau_malus)

        succes = random.random() < chance

        if succes:
            msg = f"Gotcha ! {ennemi.nom} a été capturé !"
        else:
            # Nombre de secousses (1-3) pour le feedback visuel
            secousses = max(1, int(chance / 0.25 * 3))
            secousses = min(3, secousses)
            msg = f"{'...' * secousses} Zut ! {ennemi.nom} s'est libéré !"

        return succes, msg

    @classmethod
    def bonus_net_ball(cls, ball_nom: str, ennemi) -> float:
        """Retourne le multiplicateur spécial de la Filet Ball (x3 sur Eau et Insecte)."""
        if "net" in ball_nom.lower():
            types_fr = [t.capitalize() for t in ennemi.types]
            if "Eau" in types_fr or "Insecte" in types_fr:
                return 3.0
        return 1.0
