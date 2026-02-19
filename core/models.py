import math

from core.utils import normaliser
from core.engines import LevelEngine


class Pokemon:
    """Représente un Pokémon avec ses stats, capacités et statut."""

    def __init__(self, data: dict, db_capas: list, poke_data_map: dict = None):
        self.poke_data_map = poke_data_map or {}
        self.db_capas      = db_capas

        self.nom     = data.get("nom", "Inconnu")
        self.nature  = data.get("nature", "Hardi")
        self.niveau  = data.get("niveau", 5)
        self.hp_base = data.get("hp_base", 100)
        self.hp      = data.get("hp_actuel", self.hp_base)
        self.xp      = data.get("xp", 0)
        self.xp_max  = self.niveau * 100
        self.statut  = data.get("statut", None)
        self.stages  = data.get("stages", {
            "attaque": 0, "defense": 0,
            "attaque_spe": 0, "defense_spe": 0, "vitesse": 0,
        })
        self.compteur_toxic = data.get("compteur_toxic", 0)

        # Types (priorité aux données de la base)
        self.types = data.get("types", ["Normal"])
        if self.poke_data_map:
            target = normaliser(self.nom)
            for key, value in self.poke_data_map.items():
                if normaliser(key) == target:
                    self.types = value.get("types", ["Normal"])
                    break

        self.stats          = data.get("stats", {"attaque": 50, "defense": 50, "vitesse": 50})
        self.capacites_noms = data.get("capacites", [])
        self.refresh_moves_obj()

    # ------------------------------------------------------------------
    # Capacités
    # ------------------------------------------------------------------

    def refresh_moves_obj(self):
        """Recharge la liste des objets-capacité à partir des noms."""
        self.moves_obj = []
        for c in self.capacites_noms:
            m = next(
                (m for m in self.db_capas if normaliser(m["nom_attaque"]) == normaliser(c)),
                None,
            )
            if m:
                self.moves_obj.append(m)
            else:
                self.moves_obj.append({
                    "nom_attaque": c, "puissance": 40,
                    "type": "Normal", "categorie": "Physique",
                })

    # ------------------------------------------------------------------
    # Expérience & level-up
    # ------------------------------------------------------------------

    def gain_xp(self, montant: int) -> list[str]:
        """Ajoute de l'XP et gère les montées de niveau.

        Returns:
            list[str]: Journal des montées de niveau.
        """
        self.xp += montant
        evolution_log = []

        while self.xp >= self.xp_max:
            self.xp     -= self.xp_max
            self.niveau += 1
            self.xp_max  = self.niveau * 100

            p_tmp = self.to_dict()
            gains = LevelEngine.recalculer_stats(p_tmp, self.poke_data_map)
            self.hp_base = p_tmp['hp_base']
            self.hp      = p_tmp['hp_actuel']
            self.stats   = p_tmp['stats']

            new_move = self.verifier_nouvelle_capacite()
            log = f"Niv {self.niveau}: +{gains['hp']} HP, +{gains['attaque']} ATK"
            if new_move:
                log += f" | Appris: {new_move}"
            evolution_log.append(log)

        return evolution_log

    def verifier_nouvelle_capacite(self) -> str | None:
        """Vérifie si le Pokémon apprend une capacité au niveau actuel.

        Returns:
            str | None: Nom de la capacité apprise, ou None.
        """
        target = normaliser(self.nom)
        p_info = None
        for k, v in self.poke_data_map.items():
            if normaliser(k) == target:
                p_info = v
                break

        if p_info and "learnset" in p_info:
            move_to_learn = p_info["learnset"].get(str(self.niveau))
            if move_to_learn and move_to_learn not in self.capacites_noms:
                if len(self.capacites_noms) >= 4:
                    self.capacites_noms.pop(0)
                self.capacites_noms.append(move_to_learn)
                self.refresh_moves_obj()
                return move_to_learn
        return None

    # ------------------------------------------------------------------
    # Sérialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Convertit le Pokémon en dictionnaire sauvegardable."""
        return {
            "nom":            self.nom,
            "nature":         self.nature,
            "niveau":         self.niveau,
            "hp_base":        self.hp_base,
            "hp_actuel":      self.hp,
            "xp":             self.xp,
            "stats":          self.stats,
            "statut":         self.statut,
            "types":          self.types,
            "capacites":      self.capacites_noms,
            "compteur_toxic": self.compteur_toxic,
            "stages":         self.stages,
        }
