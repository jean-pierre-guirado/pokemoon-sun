"""
dresseur.py — IA Dresseur pour Poke Fantasy.

Apparition : 20% par stage.
Equipe     : 3 Pokemon filtres par niveau (coherence evolution).
IA         : attaque optimale par type, 2 soins intelligents.
Visuel     : image dresseur.png, phrases cultes, animation glissement.
"""

import os
import random
import math

from core.nature import NatureEngine
from core.utils import normaliser
from core.table_type import TypeChart


# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
_BASE_PATH  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_NPC_PATH   = os.path.join(_BASE_PATH, "asset", "NPC")

# 5 variantes d'images dresseur (choisie aléatoirement à l'apparition)
DRESSEUR_IMGS = [
    os.path.join(_NPC_PATH, "dresseur.png"),
    os.path.join(_NPC_PATH, "dresseur_2.png"),
    os.path.join(_NPC_PATH, "dresseur_3.png"),
    os.path.join(_NPC_PATH, "dresseur_4.png"),
    os.path.join(_NPC_PATH, "dresseur_5.png"),
]


# ---------------------------------------------------------------------------
# Données narratives
# ---------------------------------------------------------------------------
NOMS_DRESSEURS = [
    "Sacha", "Pierre", "Ondine", "Brice", "Regis", "Lea",
    "Titouan", "Ayumi", "Marco", "Fleur", "Remi", "Jade",
    "Victor", "Nora", "Theo", "Camille", "Bastien", "Ines",
]

TITRES = [
    "Dresseur", "Rivale", "Champion", "As", "Maitre",
    "Expert", "Challenger", "Dompteur", "Ace Trainer",
]

# Les 3 phrases cultes du dresseur
PHRASES_DRESSEUR = [
    "Bonjour, j'aime les shorts.",

    "Salut tu n'aurais pas une clope ?",

    (
        "Bonjour je suis Eddy Malou, le premier savant de toute la republique "
        "democratique du Congo, Eddy Malou !\n"
        "E, double D, Y, M, A, L, O, U\n"
        "Hein c'est a dire... Ca veut dire imposer la force vers L'Ovalium, "
        "c'est a dire l'estime du savoir. Les gens qui connaissent beaucoup de choses, "
        "incristaliser, imposer, iiiiiiiiiiintentionner ca dans toute la republique "
        "democratique du Congo pour que nous puissions avoir la congolexicomatisation "
        "des lois du marche propres aux congolais, je vous en prie."
    ),
]


# ---------------------------------------------------------------------------
# Natures par role
# ---------------------------------------------------------------------------
NATURES_PAR_ROLE = {
    "attaquant_physique": ["Brave", "Rigide", "Solo", "Mauvais"],
    "attaquant_special":  ["Modeste", "Foufou", "Discret"],
    "tank":               ["Assure", "Lache", "Relax", "Malin"],
    "speedster":          ["Timide", "Naif", "Presse", "Jovial"],
}


# ---------------------------------------------------------------------------
# DresseurIA
# ---------------------------------------------------------------------------

class DresseurIA:
    """Dresseur ennemi avec IA avancee, visuel anime et phrases cultes."""

    PROBA_APPARITION  = 0.20
    VITESSE_GLISSEMENT = 18   # pixels par frame pendant l'animation de sortie

    def __init__(self, stage: int, poke_data_map: dict, db_capas: list,
                 evolution_config: dict = None):
        self.stage            = max(1, stage)
        self.poke_data_map    = poke_data_map
        self.db_capas         = db_capas
        self.evolution_config = evolution_config or {}

        self.nom    = random.choice(NOMS_DRESSEURS)
        self.titre  = random.choice(TITRES)
        self.phrase = random.choice(PHRASES_DRESSEUR)
        self.equipe = self._construire_equipe()

        # IA state
        self.soins_restants = 2
        self.pokemon_actif  = self.equipe[0]
        self.seuil_soin     = 0.35

        # Animation visuelle
        # Phase "DIALOGUE"  : dresseur affiché au centre, texte en bas
        # Phase "GLISSEMENT": dresseur glisse vers la droite et sort
        # Phase "COMBAT"    : combat normal
        self.anim_phase    = "DIALOGUE"
        self.sprite_x      = 400          # centré sur l'écran (800px de large)
        self.sprite_cible  = 1050         # position X de sortie (hors écran droite)
        self.dialogue_page = 0
        self._lignes_cache = None         # cache du texte wrappé

        # Texture
        self._tex = None
        self._charger_texture()

    # ------------------------------------------------------------------
    # Texture
    # ------------------------------------------------------------------

    def _charger_texture(self):
        """Choisit une image dresseur aléatoire parmi les 5 disponibles."""
        try:
            import arcade
            # Filtrer les images qui existent réellement
            disponibles = [p for p in DRESSEUR_IMGS if os.path.exists(p)]
            if disponibles:
                img_choisie = random.choice(disponibles)
                self._tex   = arcade.load_texture(img_choisie)
        except Exception as e:
            print(f"[WARN] dresseur texture : {e}")

    # ------------------------------------------------------------------
    # Apparition
    # ------------------------------------------------------------------

    @staticmethod
    def doit_apparaitre() -> bool:
        return random.random() < DresseurIA.PROBA_APPARITION

    # ------------------------------------------------------------------
    # Dialogue helpers
    # ------------------------------------------------------------------

    def _wrap(self, texte: str, max_chars: int = 52) -> list:
        """Découpe le texte en lignes pour la boite de dialogue."""
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
        """Retourne les 3 lignes de la page courante."""
        lignes = self._wrap(self.phrase)
        debut  = self.dialogue_page * 3
        return lignes[debut: debut + 3]

    def page_count(self) -> int:
        return max(1, math.ceil(len(self._wrap(self.phrase)) / 3))

    def avancer_dialogue(self) -> bool:
        """Avance d'une page. Retourne True si le dialogue est terminé."""
        if self.dialogue_page < self.page_count() - 1:
            self.dialogue_page += 1
            return False
        # Dialogue fini → lancer le glissement
        self.anim_phase = "GLISSEMENT"
        return True

    def update_glissement(self) -> bool:
        """Déplace le sprite vers la droite. Retourne True quand hors écran."""
        self.sprite_x += self.VITESSE_GLISSEMENT
        if self.sprite_x >= self.sprite_cible:
            self.anim_phase = "COMBAT"
            return True
        return False

    # ------------------------------------------------------------------
    # Dessin (appelé depuis test.py)
    # ------------------------------------------------------------------

    def draw(self, screen_w: int, screen_h: int):
        """Dessine le sprite dresseur centré + boite de dialogue."""
        import arcade

        if self.anim_phase == "COMBAT":
            return

        # Zone portrait : centré horizontalement, milieu-haut de l'écran
        sprite_y = screen_h // 2 + 70

        if self._tex:
            # Hauteur max 300px, largeur max 220px, ratio conservé
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
            # Placeholder coloré centré
            arcade.draw_rect_filled(
                arcade.rect.XYWH(self.sprite_x, sprite_y, 140, 260),
                (80, 120, 200)
            )
            arcade.draw_text("DRESSEUR", self.sprite_x, sprite_y,
                             arcade.color.WHITE, 12, anchor_x="center", anchor_y="center")

        # Boite de dialogue (uniquement en phase DIALOGUE)
        if self.anim_phase == "DIALOGUE":
            bx1, bx2 = 20, screen_w - 20
            by1, by2 = 20, 160
            arcade.draw_rect_filled(
                arcade.rect.LBWH(bx1, by1, bx2 - bx1, by2 - by1),
                (240, 240, 255, 235)
            )
            arcade.draw_rect_outline(
                arcade.rect.LBWH(bx1, by1, bx2 - bx1, by2 - by1),
                (80, 80, 160), 3
            )
            # Nom du dresseur
            arcade.draw_text(f"{self.titre} {self.nom} :",
                             bx1 + 20, by2 - 25, (60, 60, 160), 14, bold=True)
            # Lignes de texte
            for i, ligne in enumerate(self.lignes_courantes()):
                arcade.draw_text(ligne, bx1 + 20, by2 - 55 - i * 28,
                                 (20, 20, 60), 15)
            # Indicateur page
            arcade.draw_text(
                f"{self.dialogue_page + 1}/{self.page_count()}",
                bx2 - 55, by1 + 8, (120, 120, 160), 12
            )
            # Flèche "continuer"
            arcade.draw_text("[ ESPACE ] continuer",
                             screen_w // 2, 10, (100, 100, 160), 12,
                             anchor_x="center")

    # ------------------------------------------------------------------
    # Construction équipe (Pokémon cohérents par niveau)
    # ------------------------------------------------------------------

    def _niveau_pour_stage(self) -> int:
        base = max(2, min(95, int(2 + (self.stage - 1) * (95 / 98))))
        return base + random.randint(0, 1)

    def _seuil_evolution(self, nom_fr: str):
        """Niveau minimal pour ce Pokemon via évolution par niveau."""
        nom_norm = normaliser(nom_fr)
        for base, evo_data in self.evolution_config.items():
            options = evo_data if isinstance(evo_data, list) else [evo_data]
            for opt in options:
                if (normaliser(opt.get("cible", "")) == nom_norm
                        and opt.get("methode") == "level"):
                    return opt["valeur"]
        return None

    def _choisir_pokemon_candidats(self, niveau_cible: int, n: int = 12) -> list:
        """Pokemon filtrés : exclut les formes trop évoluées pour le niveau."""
        candidats = []
        for nom_fr, data in self.poke_data_map.items():
            seuil = self._seuil_evolution(nom_fr)
            if seuil and niveau_cible < seuil:
                continue  # exclut Mammochon niv 5, etc.
            candidats.append((nom_fr, data))
        if not candidats:
            candidats = list(self.poke_data_map.items())
        return random.sample(candidats, min(n, len(candidats)))

    def _determiner_role(self, data: dict) -> str:
        stats = data.get("stats", {})
        atk, spa = stats.get("attaque", 50), stats.get("attaque_spe", 50)
        spd      = stats.get("vitesse", 50)
        defense  = stats.get("defense", 50)
        if spd > 90:
            return "speedster"
        if defense > 85:
            return "tank"
        if spa > atk + 10:
            return "attaquant_special"
        return "attaquant_physique"

    def _choisir_nature(self, role: str) -> str:
        pool = NATURES_PAR_ROLE.get(role, list(NatureEngine.DATA.keys()))
        return random.choice(pool)

    def _calculer_stats(self, data: dict, niveau: int, nature: str) -> dict:
        raw   = data.get("stats", {})
        stats = {}
        for s in ["attaque", "defense", "vitesse", "attaque_spe", "defense_spe"]:
            base    = raw.get(s, 50)
            valeur  = max(1, int(((2 * base) * niveau / 100) + 5))
            stats[s] = valeur
        return NatureEngine.apply_nature_to_stats(nature, stats)

    def _choisir_attaques_strategiques(self, types_pokemon: list, role: str) -> list:
        stab = [m for m in self.db_capas
                if any(normaliser(m.get("type","")) == normaliser(t) for t in types_pokemon)
                and (m.get("puissance") or 0) >= 60]

        couverture = [m for m in self.db_capas
                      if not any(normaliser(m.get("type","")) == normaliser(t) for t in types_pokemon)
                      and (m.get("puissance") or 0) >= 70]

        statuts = [m for m in self.db_capas
                   if m.get("effet") in ("PARALYZE", "SLEEP", "BOOST_SELF", "TOXIC")
                   and not m.get("puissance")]

        soins = [m for m in self.db_capas if m.get("effet") == "HEAL_SELF"]

        pool = []
        if role == "attaquant_special":
            spe = [m for m in stab if m.get("categorie") in ("Special", "Speciale")]
            pool += random.sample(spe, min(2, len(spe)))
        elif role == "tank":
            pool += random.sample(statuts, min(1, len(statuts)))
            pool += random.sample(soins,   min(1, len(soins)))
        else:
            pool += random.sample(stab, min(2, len(stab)))

        reste_couv = [m for m in couverture if m not in pool]
        pool += random.sample(reste_couv, min(4 - len(pool), len(reste_couv)))

        if len(pool) < 4:
            reste = [m for m in self.db_capas if m not in pool and m.get("puissance")]
            pool += random.sample(reste, min(4 - len(pool), len(reste)))

        return pool[:4]

    def _creer_pokemon(self, nom_fr: str, data: dict, niveau: int):
        from core.models import Pokemon
        role    = self._determiner_role(data)
        nature  = self._choisir_nature(role)
        types   = data.get("types", ["Normal"])
        stats   = self._calculer_stats(data, niveau, nature)
        hp_raw  = data.get("stats", {}).get("hp", 60)
        hp_base = int(((2 * hp_raw) * niveau / 100) + niveau + 10)
        attaques = self._choisir_attaques_strategiques(types, role)
        data_poke = {
            "nom": nom_fr, "niveau": niveau, "nature": nature, "types": types,
            "hp_base": hp_base, "hp_actuel": hp_base, "stats": stats,
            "capacites": [m["nom_attaque"] for m in attaques],
            "statut": None, "compteur_toxic": 0,
            "stages": {"attaque":0,"defense":0,"attaque_spe":0,"defense_spe":0,"vitesse":0},
        }
        return Pokemon(data_poke, self.db_capas, self.poke_data_map)

    def _construire_equipe(self) -> list:
        niveau  = self._niveau_pour_stage()
        candid  = self._choisir_pokemon_candidats(niveau, n=12)
        choisis = random.sample(candid, min(3, len(candid)))
        return [self._creer_pokemon(nom, data, niveau) for nom, data in choisis]

    # ------------------------------------------------------------------
    # IA de combat
    # ------------------------------------------------------------------

    def choisir_action(self, ennemi_joueur) -> dict:
        pk       = self.pokemon_actif
        ratio_pv = pk.hp / pk.hp_base if pk.hp_base > 0 else 1.0
        if ratio_pv < self.seuil_soin and self.soins_restants > 0:
            return {"type": "soin"}
        return {"type": "attaque", "move": self._meilleure_attaque(pk, ennemi_joueur)}

    def _meilleure_attaque(self, attaquant, defenseur) -> dict:
        meilleur_score = -1
        meilleure      = attaquant.moves_obj[0] if attaquant.moves_obj else None
        for move in attaquant.moves_obj:
            puissance = move.get("puissance") or 0
            if puissance == 0:
                effet = move.get("effet", "")
                if defenseur.statut is None and effet in ("PARALYZE", "SLEEP", "TOXIC"):
                    score = 80
                elif effet == "BOOST_SELF":
                    score = 60
                else:
                    score = 10
            else:
                mult  = TypeChart.get_multiplier(move.get("type", "Normal"), defenseur.types)
                stab  = 1.5 if move.get("type", "Normal") in attaquant.types else 1.0
                score = puissance * mult * stab
            if score > meilleur_score:
                meilleur_score = score
                meilleure      = move
        return meilleure or attaquant.moves_obj[0]

    def utiliser_soin(self) -> str:
        pk   = self.pokemon_actif
        soin = max(30, pk.hp_base // 2)
        pk.hp = min(pk.hp_base, pk.hp + soin)
        self.soins_restants -= 1
        return f"{self.label} utilise une Potion Super sur {pk.nom} ! (+{soin} PV)"

    def changer_pokemon(self) -> bool:
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
