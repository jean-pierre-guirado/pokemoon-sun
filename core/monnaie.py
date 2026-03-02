"""
monnaie.py — Moteur de récompenses monétaires (PokéDollars).

Calcule les gains d'argent après un combat en fonction :
  - du niveau du Pokémon vaincu
  - du type de combat (sauvage ou dresseur)
  - d'un multiplicateur de stage pour la progression

Usage (POO) :
    from core.monnaie import MonnaieEngine
    gain = MonnaieEngine.calculer_gain(ennemi, est_dresseur=False, stage=3)
    MonnaieEngine.crediter(dresseur_data, gain)
"""

import random


class MonnaieEngine:
    """Gère tous les calculs et crédits de PokéDollars."""

    BASE_PAR_NIVEAU = 15       # PokéDollars de base par niveau de l'ennemi
    MULT_DRESSEUR   = 2.5      # x2.5 pour un combat dresseur
    MULT_SAUVAGE    = 1.0      # x1.0 pour un sauvage
    BONUS_PAR_STAGE = 0.08     # +8% par stage de progression

    @classmethod
    def calculer_gain(cls, ennemi, est_dresseur: bool = False, stage: int = 1) -> int:
        niveau     = max(1, getattr(ennemi, 'niveau', 5))
        mult_type  = cls.MULT_DRESSEUR if est_dresseur else cls.MULT_SAUVAGE
        mult_stage = 1.0 + (max(1, stage) - 1) * cls.BONUS_PAR_STAGE
        gain_brut  = cls.BASE_PAR_NIVEAU * niveau * mult_type * mult_stage
        gain_final = max(10, int(gain_brut * random.uniform(0.80, 1.20)))
        return gain_final

    @classmethod
    def calculer_gain_dresseur(cls, equipe_dresseur: list, stage: int = 1) -> int:
        return sum(cls.calculer_gain(p, est_dresseur=True, stage=stage)
                   for p in equipe_dresseur)

    @classmethod
    def crediter(cls, dresseur_data: dict, montant: int) -> int:
        dresseur_data["argent"] = dresseur_data.get("argent", 0) + montant
        return dresseur_data["argent"]

    @classmethod
    def debiter(cls, dresseur_data: dict, montant: int) -> tuple:
        solde = dresseur_data.get("argent", 0)
        if solde >= montant:
            dresseur_data["argent"] = solde - montant
            return True, dresseur_data["argent"]
        return False, solde

    @classmethod
    def formater_message(cls, gain: int, est_dresseur: bool = False) -> str:
        source = "le dresseur" if est_dresseur else "le combat"
        return f"Vous remportez {gain}P grace a {source} !"
