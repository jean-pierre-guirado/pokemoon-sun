"""
boss.py — Combat Boss pour Poke Fantasy.

Le Boss est un adversaire unique avec :
  - Une equipe fixe de 6 Pokemon legendaires/puissants avec natures et attaques ultra-strategiques
  - 3 guerisons intelligentes (soin prioritaire si PV < 40%)
  - Changement de Pokemon strategique (switch vers le Pokemon le plus efficace contre l'adversaire)
  - Musique : final.mp3 (dossier audio)
  - Background : arene.jpg (dossier fonts)
  - Image : boss.png (dossier NPC)

Usage :
    from core.boss import BossIA
    boss = BossIA(poke_data_map, db_capas)
"""

import os
import random

from core.nature import NatureEngine
from core.utils import normaliser
from core.table_type import TypeChart


# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
_BASE_PATH  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_NPC_PATH   = os.path.join(_BASE_PATH, "asset", "NPC")
_AUDIO_PATH = os.path.join(_BASE_PATH, "asset", "audio")
_FONT_PATH  = os.path.join(_BASE_PATH, "asset", "fonts")

BOSS_IMG         = os.path.join(_NPC_PATH, "boss.png")
BOSS_MUSIC_PATH  = os.path.join(_AUDIO_PATH, "final.mp3")
BOSS_BG_PATH     = os.path.join(_FONT_PATH, "arene.jpg")

# Background dresseur aussi (pour les combats dresseur normaux)
DRESSEUR_BG_PATH = os.path.join(_FONT_PATH, "arene.jpg")


# ---------------------------------------------------------------------------
# Phrases du boss
# ---------------------------------------------------------------------------
PHRASES_BOSS = [
    (
        "ca dit quoi l'equipe ?\n"
        "Alors tu es arrive au stade final de ce projet pokemon. C'est bien ouais.\n"
        "Par contre je te previens si tu perds ca part sur un 0 etoile sur le projet.\n"
        "Dans ce cas, je vais te montrer ce qu'est du machine learning !"
    ),
]


# ---------------------------------------------------------------------------
# Equipe fixe du boss (6 Pokemon)
# ---------------------------------------------------------------------------
# Chaque entrée : (nom_fr, types, stats_base, nature, attaques_prioritaires, role)
# Les attaques seront choisies stratégiquement depuis db_capas

BOSS_EQUIPE_CONFIG = [
    {
        "nom":    "Metalosse",
        "shiny":  True,
        "types":  ["Steel", "Psychic"],
        "stats":  {"attaque": 135, "defense": 130, "vitesse": 70,
                   "attaque_spe": 95, "defense_spe": 90, "hp": 80},
        "nature": "Brave",    # ATK+ SPD-
        "role":   "attaquant_physique",
    },
    {
        "nom":    "Drattak",
        "shiny":  False,
        "types":  ["Dragon", "Flying"],
        "stats":  {"attaque": 134, "defense": 95, "vitesse": 80,
                   "attaque_spe": 100, "defense_spe": 100, "hp": 91},
        "nature": "Rigide",   # ATK+ SPA-
        "role":   "attaquant_physique",
    },
    {
        "nom":    "Trioxyde",
        "shiny":  False,
        "types":  ["Fire", "Flying"],
        "stats":  {"attaque": 110, "defense": 80, "vitesse": 90,
                   "attaque_spe": 130, "defense_spe": 80, "hp": 78},
        "nature": "Modeste",  # SPA+ ATK-
        "role":   "attaquant_special",
    },
    {
        "nom":    "Kyogre",
        "shiny":  False,
        "types":  ["Water"],
        "stats":  {"attaque": 100, "defense": 90, "vitesse": 90,
                   "attaque_spe": 150, "defense_spe": 140, "hp": 100},
        "nature": "Modeste",  # SPA+ ATK-
        "role":   "attaquant_special",
    },
    {
        "nom":    "Groudon",
        "shiny":  False,
        "types":  ["Ground"],
        "stats":  {"attaque": 150, "defense": 140, "vitesse": 90,
                   "attaque_spe": 100, "defense_spe": 90, "hp": 100},
        "nature": "Brave",    # ATK+ SPD-
        "role":   "attaquant_physique",
    },
    {
        "nom":    "Gardevoir",
        "shiny":  True,
        "types":  ["Psychic", "Fairy"],
        "stats":  {"attaque": 65, "defense": 65, "vitesse": 80,
                   "attaque_spe": 125, "defense_spe": 115, "hp": 68},
        "nature": "Modeste",  # SPA+ ATK-
        "role":   "attaquant_special",
    },
]

NIVEAU_BOSS = 85   # Niveau fixe de l'équipe du boss


# ---------------------------------------------------------------------------
# BossIA
# ---------------------------------------------------------------------------

class BossIA:
    """Boss final ultra-strategique avec 6 Pokemon legendaires."""

    def __init__(self, poke_data_map: dict, db_capas: list):
        self.poke_data_map = poke_data_map
        self.db_capas      = db_capas

        self.nom    = "Champion"
        self.titre  = "Boss"
        self.phrase = random.choice(PHRASES_BOSS)
        self.equipe = self._construire_equipe()

        # IA state
        self.soins_restants  = 3
        self.pokemon_actif   = self.equipe[0]
        self.seuil_soin      = 0.40   # soin si < 40% PV

        # Animation dialogue
        self.anim_phase    = "DIALOGUE"
        self.sprite_x      = 400
        self.sprite_cible  = 1050
        self.dialogue_page = 0
        self._lignes_cache = None
        self.VITESSE_GLISSEMENT = 18

        # Texture
        self._tex = None
        self._charger_texture()

    # ------------------------------------------------------------------
    # Texture
    # ------------------------------------------------------------------

    def _charger_texture(self):
        try:
            import arcade
            if os.path.exists(BOSS_IMG):
                self._tex = arcade.load_texture(BOSS_IMG)
        except Exception as e:
            print(f"[WARN] boss.png : {e}")

    # ------------------------------------------------------------------
    # Construction équipe
    # ------------------------------------------------------------------

    def _calculer_stats(self, stats_base: dict, nature: str) -> dict:
        niveau = NIVEAU_BOSS
        stats  = {}
        for s in ["attaque", "defense", "vitesse", "attaque_spe", "defense_spe"]:
            base   = stats_base.get(s, 80)
            valeur = max(1, int(((2 * base) * niveau / 100) + 5))
            stats[s] = valeur
        return NatureEngine.apply_nature_to_stats(nature, stats)

    def _choisir_attaques(self, types_pokemon: list, role: str) -> list:
        """Sélection ultra-stratégique des 4 meilleures attaques."""
        # STAB haute puissance
        stab_physique = [m for m in self.db_capas
                         if any(normaliser(m.get("type","")) == normaliser(t) for t in types_pokemon)
                         and m.get("categorie") in ("Physique","Physical","Physique")
                         and (m.get("puissance") or 0) >= 70]

        stab_special = [m for m in self.db_capas
                        if any(normaliser(m.get("type","")) == normaliser(t) for t in types_pokemon)
                        and m.get("categorie") in ("Special","Spéciale","Speciale")
                        and (m.get("puissance") or 0) >= 70]

        # Couverture forte (types differents, puissance ≥ 80)
        couverture = [m for m in self.db_capas
                      if not any(normaliser(m.get("type","")) == normaliser(t) for t in types_pokemon)
                      and (m.get("puissance") or 0) >= 80]

        # Statuts debilitants
        statuts = [m for m in self.db_capas
                   if m.get("effet") in ("PARALYZE", "SLEEP", "TOXIC", "BURN")
                   and not m.get("puissance")]

        pool = []

        if role == "attaquant_special":
            top_stab = sorted(stab_special, key=lambda m: m.get("puissance", 0), reverse=True)
            pool += top_stab[:2]
        else:
            top_stab = sorted(stab_physique, key=lambda m: m.get("puissance", 0), reverse=True)
            pool += top_stab[:2]

        # Couverture (1 ou 2 slots restants)
        reste_couv = sorted([m for m in couverture if m not in pool],
                            key=lambda m: m.get("puissance", 0), reverse=True)
        pool += reste_couv[:max(0, 3 - len(pool))]

        # Un statut pour contrôler
        reste_stat = [m for m in statuts if m not in pool]
        if reste_stat and len(pool) < 4:
            pool.append(random.choice(reste_stat))

        # Compléter à 4
        if len(pool) < 4:
            reste = sorted([m for m in self.db_capas if m not in pool and m.get("puissance")],
                           key=lambda m: m.get("puissance", 0), reverse=True)
            pool += reste[:4 - len(pool)]

        return pool[:4]

    def _creer_pokemon(self, cfg: dict):
        from core.models import Pokemon
        niveau  = NIVEAU_BOSS
        nature  = cfg["nature"]
        types   = cfg["types"]
        stats   = self._calculer_stats(cfg["stats"], nature)
        hp_base = int(((2 * cfg["stats"].get("hp", 80)) * niveau / 100) + niveau + 10)
        attaques = self._choisir_attaques(types, cfg["role"])
        nom_complet = cfg["nom"] + (" Shiny" if cfg.get("shiny") else "")
        data_poke = {
            "nom":       nom_complet,
            "niveau":    niveau,
            "nature":    nature,
            "types":     types,
            "hp_base":   hp_base,
            "hp_actuel": hp_base,
            "stats":     stats,
            "capacites": [m["nom_attaque"] for m in attaques],
            "statut":    None,
            "compteur_toxic": 0,
            "stages": {"attaque":0,"defense":0,"attaque_spe":0,"defense_spe":0,"vitesse":0},
        }
        return Pokemon(data_poke, self.db_capas, self.poke_data_map)

    def _construire_equipe(self) -> list:
        return [self._creer_pokemon(cfg) for cfg in BOSS_EQUIPE_CONFIG]

    # ------------------------------------------------------------------
    # IA de combat ultra-stratégique
    # ------------------------------------------------------------------

    def choisir_action(self, ennemi_joueur) -> dict:
        """
        Logique boss :
        1. Si Pokemon actif est le moins efficace contre l'adversaire → switch strategique
        2. Si PV < seuil et soins restants → soigne
        3. Sinon → meilleure attaque
        """
        pk = self.pokemon_actif

        # Switch stratégique : si un autre Pokemon ferait bien mieux
        meilleur_switch = self._evaluer_switch(ennemi_joueur)
        if meilleur_switch and meilleur_switch is not pk:
            return {"type": "switch", "pokemon": meilleur_switch}

        # Soin si en danger
        ratio_pv = pk.hp / pk.hp_base if pk.hp_base > 0 else 1.0
        if ratio_pv < self.seuil_soin and self.soins_restants > 0:
            return {"type": "soin"}

        return {"type": "attaque", "move": self._meilleure_attaque(pk, ennemi_joueur)}

    def _evaluer_switch(self, ennemi):
        """Vérifie si un autre Pokemon en réserve ferait significativement mieux."""
        pk_actif  = self.pokemon_actif
        score_actif = self._score_matchup(pk_actif, ennemi)

        meilleur_pk    = None
        meilleur_score = score_actif * 1.5  # seuil : 50% mieux

        for pk in self.equipe:
            if pk is pk_actif or pk.hp <= 0:
                continue
            score = self._score_matchup(pk, ennemi)
            if score > meilleur_score:
                meilleur_score = score
                meilleur_pk    = pk

        return meilleur_pk  # None si pas de switch intéressant

    def _score_matchup(self, attaquant, defenseur) -> float:
        """Score global d'un Pokemon contre un adversaire (type + puissance)."""
        if not attaquant.moves_obj:
            return 0.0
        meilleur = max(
            (
                (m.get("puissance") or 0)
                * TypeChart.get_multiplier(m.get("type","Normal"), defenseur.types)
                * (1.5 if m.get("type","Normal") in attaquant.types else 1.0)
            )
            for m in attaquant.moves_obj
        )
        # Bonus si notre type résiste au type ennemi
        resistance = min(
            TypeChart.get_multiplier(t, attaquant.types)
            for t in defenseur.types
        ) if defenseur.types else 1.0
        return meilleur / max(0.1, resistance)

    def _meilleure_attaque(self, attaquant, defenseur) -> dict:
        meilleur_score = -1
        meilleure      = attaquant.moves_obj[0] if attaquant.moves_obj else None
        for move in attaquant.moves_obj:
            puissance = move.get("puissance") or 0
            if puissance == 0:
                effet = move.get("effet", "")
                score = 80 if (defenseur.statut is None and effet in ("PARALYZE","SLEEP","TOXIC","BURN")) else 10
            else:
                mult  = TypeChart.get_multiplier(move.get("type","Normal"), defenseur.types)
                stab  = 1.5 if move.get("type","Normal") in attaquant.types else 1.0
                score = puissance * mult * stab
            if score > meilleur_score:
                meilleur_score = score
                meilleure      = move
        return meilleure or attaquant.moves_obj[0]

    def utiliser_soin(self) -> str:
        pk   = self.pokemon_actif
        soin = max(50, int(pk.hp_base * 0.6))  # soigne 60% des PV max
        pk.hp = min(pk.hp_base, pk.hp + soin)
        self.soins_restants -= 1
        return f"Boss utilise une Hyper Potion sur {pk.nom} ! (+{soin} PV)"

    def effectuer_switch(self, nouveau_pk) -> str:
        ancien = self.pokemon_actif.nom
        self.pokemon_actif = nouveau_pk
        return f"Boss rappelle {ancien} et envoie {nouveau_pk.nom} !"

    def changer_pokemon(self) -> bool:
        """Change pour le prochain Pokemon vivant (utilisé quand le courant est KO)."""
        for pk in self.equipe:
            if pk.hp > 0 and pk is not self.pokemon_actif:
                self.pokemon_actif = pk
                return True
        return False

    @property
    def est_vaincu(self) -> bool:
        return all(p.hp <= 0 for p in self.equipe)

    @property
    def label(self) -> str:
        return f"{self.titre} {self.nom}"

    # ------------------------------------------------------------------
    # Dialogue (identique à DresseurIA)
    # ------------------------------------------------------------------

    def _wrap(self, texte: str, max_chars: int = 52) -> list:
        import math
        if self._lignes_cache is not None:
            return self._lignes_cache
        lignes = []
        for para in texte.split("\n"):
            mots, courante = para.split(), ""
            for mot in mots:
                if len(courante) + len(mot) + (1 if courante else 0) <= max_chars:
                    courante += (" " if courante else "") + mot
                else:
                    if courante:
                        lignes.append(courante)
                    courante = mot
            if courante:
                lignes.append(courante)
        self._lignes_cache = lignes
        return lignes

    def lignes_courantes(self) -> list:
        lignes = self._wrap(self.phrase)
        debut  = self.dialogue_page * 3
        return lignes[debut: debut + 3]

    def page_count(self) -> int:
        import math
        return max(1, math.ceil(len(self._wrap(self.phrase)) / 3))

    def avancer_dialogue(self) -> bool:
        if self.dialogue_page < self.page_count() - 1:
            self.dialogue_page += 1
            return False
        self.anim_phase = "GLISSEMENT"
        return True

    def update_glissement(self) -> bool:
        self.sprite_x += self.VITESSE_GLISSEMENT
        if self.sprite_x >= self.sprite_cible:
            self.anim_phase = "COMBAT"
            return True
        return False

    # ------------------------------------------------------------------
    # Dessin
    # ------------------------------------------------------------------

    def draw(self, screen_w: int, screen_h: int):
        import arcade
        if self.anim_phase == "COMBAT":
            return

        sprite_y = screen_h // 2 + 70

        if self._tex:
            h_max  = min(300, screen_h - 230)
            w_max  = 220
            scale  = min(w_max / self._tex.width, h_max / self._tex.height)
            w_draw = int(self._tex.width  * scale)
            h_draw = int(self._tex.height * scale)
            arcade.draw_texture_rect(
                self._tex,
                arcade.rect.XYWH(self.sprite_x, sprite_y, w_draw, h_draw)
            )
        else:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(self.sprite_x, sprite_y, 140, 260), (120, 20, 20)
            )
            arcade.draw_text("BOSS", self.sprite_x, sprite_y,
                             arcade.color.WHITE, 14, anchor_x="center", anchor_y="center", bold=True)

        if self.anim_phase == "DIALOGUE":
            bx1, bx2 = 20, screen_w - 20
            by1, by2 = 20, 170
            arcade.draw_rect_filled(arcade.rect.LBWH(bx1, by1, bx2-bx1, by2-by1), (40, 10, 10, 240))
            arcade.draw_rect_outline(arcade.rect.LBWH(bx1, by1, bx2-bx1, by2-by1), (200, 50, 50), 3)
            arcade.draw_text(f"{self.label} :",
                             bx1+20, by2-28, (220, 60, 60), 15, bold=True)
            for i, ligne in enumerate(self.lignes_courantes()):
                arcade.draw_text(ligne, bx1+20, by2-58-i*30, (240, 200, 200), 14)
            arcade.draw_text(f"{self.dialogue_page+1}/{self.page_count()}",
                             bx2-55, by1+8, (160, 80, 80), 12)
            arcade.draw_text("[ ESPACE ] continuer",
                             screen_w//2, 10, (160, 60, 60), 12, anchor_x="center")
