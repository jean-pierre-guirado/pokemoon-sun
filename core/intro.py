"""
intro.py — Séquence d'introduction avec le Professeur.

Enchaîne :
  1. Discours du professeur (texte défilant, espace pour avancer)
  2. Choix du sexe (garçon / fille)
  3. Saisie du nom (10 caractères max)
  4. Choix du starter (Flamiaou / Grenousse / Arcko) avec taux shiny
  5. Dernier discours + création de la sauvegarde → lancement de PokeFantasyGame

Utilise arcade.View pour s'intégrer dans la MainWindow de main.py.
Les paramètres écran proviennent de core.config.
"""

import os
import json
import math
import random
import arcade

# Paramètres écran depuis core.config
from core.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE,
    DRESSEUR_JSON, CAPA_JSON, POKEMON_DATA_JSON,
)

# ---------------------------------------------------------------------------
# Chemins assets
# ---------------------------------------------------------------------------
BASE_PATH  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSET_PATH = os.path.join(BASE_PATH, "asset")
NPC_PATH   = os.path.join(ASSET_PATH, "NPC")
DATA_PATH  = os.path.join(BASE_PATH, "data")
SAVES_PATH = os.path.join(BASE_PATH, "saves")

os.makedirs(SAVES_PATH, exist_ok=True)

PROFESSOR_IMG = os.path.join(NPC_PATH, "professor.png")
BOY_IMG       = os.path.join(NPC_PATH, "garcon.png")
GIRL_IMG      = os.path.join(NPC_PATH, "fille.png")

# ---------------------------------------------------------------------------
# Données de jeu
# ---------------------------------------------------------------------------

SHINY_RATE = 1 / 4096

# Natures depuis core.natur
try:
    from core.natur import NATURES
except ImportError:
    NATURES = [
        "Assuré", "Brave", "Calme", "Docile", "Foufou", "Gentil", "Hardi",
        "Jovial", "Lâche", "Malin", "Malpoli", "Modeste", "Naïf", "Presse",
        "Prudent", "Pudique", "Relax", "Rigide", "Sérieux", "Solo",
        "Timide", "Bizarre", "Discret", "Mauvais"
    ]

STARTER_LIST = ["Flamiaou", "Grenousse", "Arcko"]

STARTER_MOVES = {
    "Flamiaou":  ["Griffe", "Flammèche", "Rugissement"],
    "Grenousse": ["Charge", "Pistolet à O", "Rugissement"],
    "Arcko":     ["Charge", "Fouet Lianes", "Rugissement"],
}

STARTER_COLORS = {
    "Flamiaou":  (255, 100, 50),
    "Grenousse": (50, 150, 255),
    "Arcko":     (80, 200, 80),
}

# Types lus depuis pokemon_data.json (fallback si absent)
_STARTER_TYPES_FALLBACK = {
    "Flamiaou":  ["Feu"],
    "Grenousse": ["Eau"],
    "Arcko":     ["Plante"],
}

def _charger_starter_types() -> dict:
    try:
        from core.config import POKEMON_DATA_JSON as _pdj
        with open(_pdj, "r", encoding="utf-8") as _f:
            _pdata = json.load(_f)
        return {nom: _pdata[nom].get("types", _STARTER_TYPES_FALLBACK[nom])
                for nom in STARTER_LIST if nom in _pdata}
    except Exception:
        return _STARTER_TYPES_FALLBACK.copy()

STARTER_TYPES     = _charger_starter_types()
STARTER_TYPE_LABEL = {
    nom: "Type : " + " / ".join(types)
    for nom, types in STARTER_TYPES.items()
}

# ---------------------------------------------------------------------------
# États de l'intro
# ---------------------------------------------------------------------------
S_TALK_1  = "talk_1"
S_GENDER  = "gender"
S_TALK_2  = "talk_2"
S_NAME    = "name"
S_TALK_3  = "talk_3"
S_STARTER = "starter"
S_TALK_4  = "talk_4"
S_DONE    = "done"

DIALOGUES = {
    S_TALK_1: [
        "Oh bonjour et bienvenue, BIENVENUE dans ce pokemon sur python.",
        "Tu t'ennuies sur les derniers pokemons et Z-A est tout simplement décevant ?",
        "Ne t'en fait jeune dresseur, j'ai la solution pour toi !",
        "Mais avant ça j'ai des questions à te poser.",
        "Es-tu un garçon ou une fille ?",
    ],
    S_TALK_2: [
        "Oh ok, même si, en regardant ton visage via la webcam tu as l'air plus moche que ça,",
        "comment t'appelles-tu ?",
    ],
    S_TALK_3: [
        "D'accord, c'est un prénom nul mais passons,",
        "je ne vais pas te faire une présentation de 30 minutes afin de te dire ce qu'est un Pokémon,",
        "du coup choisis ton starter !",
    ],
    S_TALK_4: [
        "Un choix de mauvais goût si tu veux mon avis mais bon,",
        "tiens voici 5 Pokéballs et 1000 Pokédollars.",
        "Maintenant sort et va toucher de l'herbe !",
    ],
}

TEXT_SPEED = 2  # caractères animés par frame

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wrap_text(text: str, max_chars: int = 46) -> list:
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + (1 if current else 0) <= max_chars:
            current += (" " if current else "") + word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def calc_stat(base: int, niveau: int, is_hp: bool = False) -> int:
    if is_hp:
        return math.floor(((2 * base) * niveau) / 100) + niveau + 10
    return math.floor(((2 * base) * niveau) / 100) + 5


def charger_pokemon_data() -> dict:
    if os.path.exists(POKEMON_DATA_JSON):
        with open(POKEMON_DATA_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def charger_capacites() -> list:
    if os.path.exists(CAPA_JSON):
        with open(CAPA_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def creer_starter(nom: str, poke_data: dict) -> dict:
    """Crée le dictionnaire d'un starter niveau 5.

    Stats et types lus depuis pokemon_data.json (clé = nom FR exact).
    Nature choisie dans core.natur.NATURES. Taux shiny : 1/4096.
    """
    niveau   = 5
    nature   = random.choice(NATURES)
    is_shiny = random.random() < SHINY_RATE

    # Lecture directe par nom (clé FR dans pokemon_data.json)
    entry      = poke_data.get(nom, {})
    base_stats = entry.get("stats", {
        "hp": 45, "attaque": 50, "defense": 45,
        "attaque_spe": 50, "defense_spe": 45, "vitesse": 45
    })
    types_pokemon = entry.get("types", STARTER_TYPES.get(nom, ["Normal"]))

    hp_base     = calc_stat(base_stats.get("hp", 45), niveau, is_hp=True)
    nom_affiche = f"{nom} ★" if is_shiny else nom

    return {
        "nom":       nom_affiche,
        "nature":    nature,
        "niveau":    niveau,
        "hp_base":   hp_base,
        "hp_actuel": hp_base,
        "xp":        0,
        "shiny":     is_shiny,
        "stats": {
            "attaque":     calc_stat(base_stats.get("attaque", 50), niveau),
            "defense":     calc_stat(base_stats.get("defense", 45), niveau),
            "vitesse":     calc_stat(base_stats.get("vitesse", 45), niveau),
            "attaque_spe": calc_stat(base_stats.get("attaque_spe", 50), niveau),
            "defense_spe": calc_stat(base_stats.get("defense_spe", 45), niveau),
        },
        "statut":         None,
        "types":          types_pokemon,
        "capacites":      STARTER_MOVES.get(nom, ["Charge"]),
        "compteur_toxic": 0,
        "stages": {
            "attaque": 0, "defense": 0,
            "attaque_spe": 0, "defense_spe": 0, "vitesse": 0,
        },
    }


def creer_sauvegarde(nom_joueur: str, sexe: str, starter: dict) -> dict:
    """Génère la structure de sauvegarde initiale (format dresseur_config.json)."""
    return {
        "nom_dresseur": nom_joueur,
        "sexe":         sexe,
        "argent":       1000,
        "stage":        1,
        "equipe":       [starter],
        "inventaire": {
            "potions": {},
            "balls": {
                "poke-ball": 5
            }
        }
    }


# ---------------------------------------------------------------------------
# Vue d'introduction
# ---------------------------------------------------------------------------

class IntroView(arcade.View):
    """Séquence d'introduction complète avec le professeur."""

    def __init__(self, slot_num: int = 1):
        super().__init__()
        self.slot_num      = slot_num
        self.state         = S_TALK_1

        # Données joueur
        self.player_gender  = "garçon"
        self.player_name    = ""
        self.starter_choice = 0
        self.starter_data   = None

        # Données Pokémon
        self.poke_data = charger_pokemon_data()

        # Textures NPC
        self.tex_prof   = self._load_tex(PROFESSOR_IMG)
        self.tex_boy    = self._load_tex(BOY_IMG)
        self.tex_girl   = self._load_tex(GIRL_IMG)
        self.tex_player = self.tex_boy

        # Dialogue
        self.dialogue_lines  = []
        self.current_page    = 0
        self.displayed_chars = 0
        self.anim_timer      = 0.0
        self.cursor_timer    = 0.0

        self._rebuild_dialogue(S_TALK_1)

        # Musique d'intro : intro.mp3 (meme dossier que battle_theme)
        # Transmise ensuite au jeu principal pour continuite audio
        self.bgm        = None
        self.bgm_player = None
        try:
            from core.config import AUDIO_PATH as _AP
            intro_path = os.path.join(_AP, "intro.mp3")
            if os.path.exists(intro_path):
                self.bgm        = arcade.load_sound(intro_path)
                self.bgm_player = arcade.play_sound(self.bgm, volume=0.6, loop=True)
        except Exception as e:
            print(f"[WARN] Musique intro : {e}")

    # ------------------------------------------------------------------
    def _load_tex(self, path):
        if os.path.exists(path):
            try:
                return arcade.load_texture(path)
            except Exception:
                pass
        return None

    def _rebuild_dialogue(self, state_key: str):
        raw   = DIALOGUES.get(state_key, [])
        lines = []
        for line in raw:
            lines.extend(wrap_text(line, 46))
        self.dialogue_lines  = lines
        self.current_page    = 0
        self.displayed_chars = 0

    def _current_lines(self):
        start = self.current_page * 2
        return self.dialogue_lines[start: start + 2]

    def _page_count(self):
        return max(1, math.ceil(len(self.dialogue_lines) / 2))

    def _is_last_page(self):
        return self.current_page >= self._page_count() - 1

    def _chars_on_page(self):
        return sum(len(l) for l in self._current_lines())

    def _anim_done(self):
        return self.displayed_chars >= self._chars_on_page()

    # ------------------------------------------------------------------
    def on_show_view(self):
        arcade.set_background_color((200, 230, 255))

    def on_update(self, delta_time):
        self.anim_timer  += delta_time
        self.cursor_timer += delta_time

        if self.state in (S_TALK_1, S_TALK_2, S_TALK_3, S_TALK_4):
            if not self._anim_done():
                self.displayed_chars = min(
                    self._chars_on_page(),
                    self.displayed_chars + TEXT_SPEED
                )

    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        # Fond dégradé simple
        arcade.draw_rect_filled(
            arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            (200, 230, 255)
        )

        self._draw_professor()
        self._draw_dialogue_box()

        if self.state == S_GENDER:
            self._draw_gender_choice()
        elif self.state == S_NAME:
            self._draw_name_input()
        elif self.state == S_STARTER:
            self._draw_starter_choice()

        # Indicateur espace
        if self.state in (S_TALK_1, S_TALK_2, S_TALK_3, S_TALK_4):
            if self._anim_done():
                alpha = int(128 + 127 * math.sin(self.anim_timer * 3))
                arcade.draw_text("▼  Espace pour continuer",
                                 SCREEN_WIDTH // 2, 55,
                                 (0, 0, 0, alpha), 15, anchor_x="center")

    # ------------------------------------------------------------------
    def _draw_professor(self):
        if self.tex_prof:
            scale = min(220 / self.tex_prof.width, 280 / self.tex_prof.height)
            arcade.draw_texture_rect(
                self.tex_prof,
                arcade.rect.XYWH(160, SCREEN_HEIGHT // 2 + 60,
                                  int(self.tex_prof.width * scale),
                                  int(self.tex_prof.height * scale))
            )

        # Sprite joueur (dès le choix du sexe)
        if self.state in (S_GENDER, S_TALK_2, S_NAME, S_TALK_3, S_STARTER, S_TALK_4):
            tex = self.tex_player
            if tex:
                scale = min(120 / tex.width, 160 / tex.height)
                arcade.draw_texture_rect(
                    tex,
                    arcade.rect.XYWH(SCREEN_WIDTH - 160, SCREEN_HEIGHT // 2 + 60,
                                      int(tex.width * scale),
                                      int(tex.height * scale))
                )

    # ------------------------------------------------------------------
    def _draw_dialogue_box(self):
        bx1, bx2 = 20, SCREEN_WIDTH - 20
        by1, by2 = 20, 160

        arcade.draw_rect_filled(
            arcade.rect.LBWH(bx1, by1, bx2 - bx1, by2 - by1),
            (240, 240, 255, 230)
        )
        arcade.draw_rect_outline(
            arcade.rect.LBWH(bx1, by1, bx2 - bx1, by2 - by1),
            (80, 80, 160), 3
        )

        if self.state in (S_TALK_1, S_TALK_2, S_TALK_3, S_TALK_4):
            lines      = self._current_lines()
            chars_left = self.displayed_chars
            for i, line in enumerate(lines):
                shown      = line[:chars_left]
                chars_left = max(0, chars_left - len(line))
                y          = by2 - 30 - i * 30
                arcade.draw_text(shown, bx1 + 20, y, (20, 20, 60), 17)

            arcade.draw_text(
                f"{self.current_page + 1}/{self._page_count()}",
                bx2 - 60, by1 + 8, (120, 120, 160), 12
            )

    # ------------------------------------------------------------------
    def _draw_gender_choice(self):
        arcade.draw_text("Qui es-tu ?", 40, 130, (20, 20, 60), 16, bold=True)

        options = ["Garçon", "Fille"]
        texs    = [self.tex_boy, self.tex_girl]

        for i, (opt, tex) in enumerate(zip(options, texs)):
            x      = 220 + i * 200
            y_box  = 85
            is_sel = (i == self.starter_choice)

            arcade.draw_rect_filled(
                arcade.rect.XYWH(x, y_box, 120, 60),
                (180, 220, 255) if is_sel else (230, 230, 255)
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(x, y_box, 120, 60),
                (80, 80, 160) if is_sel else (160, 160, 200), 2
            )

            if tex:
                scale = min(50 / tex.width, 50 / tex.height)
                arcade.draw_texture_rect(
                    tex,
                    arcade.rect.XYWH(x, y_box + 10,
                                      int(tex.width * scale),
                                      int(tex.height * scale))
                )

            arcade.draw_text(opt, x, y_box - 25, (20, 20, 60), 14,
                             anchor_x="center", bold=is_sel)

        arcade.draw_text("← → pour choisir  |  Entrée pour valider",
                         SCREEN_WIDTH // 2, 30, (100, 100, 140), 13,
                         anchor_x="center")

    # ------------------------------------------------------------------
    def _draw_name_input(self):
        arcade.draw_text("Quel est ton nom ? (10 car. max)",
                         40, 130, (20, 20, 60), 15, bold=True)

        fx = SCREEN_WIDTH // 2 - 100
        fy = 70
        arcade.draw_rect_filled(
            arcade.rect.LBWH(fx, fy - 4, 200, 28),
            (255, 255, 255)
        )
        arcade.draw_rect_outline(
            arcade.rect.LBWH(fx, fy - 4, 200, 28),
            (80, 80, 160), 2
        )
        cursor = "_" if int(self.cursor_timer * 2) % 2 == 0 else " "
        arcade.draw_text(self.player_name + cursor,
                         fx + 8, fy + 2, (20, 20, 60), 18)

        arcade.draw_text("Entrée pour valider",
                         SCREEN_WIDTH // 2, 30, (100, 100, 140), 13,
                         anchor_x="center")

    # ------------------------------------------------------------------
    def _draw_starter_choice(self):
        arcade.draw_text("Choisis ton starter !",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40,
                         (20, 20, 60), 22, anchor_x="center", bold=True)

        spacing = 220
        start_x = SCREEN_WIDTH // 2 - spacing

        for i, nom in enumerate(STARTER_LIST):
            x      = start_x + i * spacing
            y      = SCREEN_HEIGHT // 2 + 10
            is_sel = (i == self.starter_choice)
            color  = STARTER_COLORS.get(nom, (200, 200, 200))
            bg     = (*color, 80) if is_sel else (200, 200, 220, 60)

            arcade.draw_rect_filled(
                arcade.rect.XYWH(x, y, 200, 200),
                bg
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(x, y, 200, 200),
                color if is_sel else (160, 160, 180),
                3 if is_sel else 1
            )

            # Sprite du starter (cherche dans les dossiers sprite)
            sprite_path = self._find_sprite(nom)
            if sprite_path:
                try:
                    tex   = arcade.load_texture(sprite_path)
                    scale = min(90 / tex.width, 90 / tex.height)
                    arcade.draw_texture_rect(
                        tex,
                        arcade.rect.XYWH(x, y + 55,
                                          int(tex.width * scale),
                                          int(tex.height * scale))
                    )
                except Exception:
                    self._draw_placeholder(x, y + 55, color)
            else:
                self._draw_placeholder(x, y + 55, color)

            arcade.draw_text(nom, x, y - 10, (20, 20, 60), 16,
                             anchor_x="center", bold=is_sel)
            arcade.draw_text(STARTER_TYPE_LABEL.get(nom, ""),
                             x, y - 35, (60, 60, 100), 13,
                             anchor_x="center")
            if is_sel:
                arcade.draw_text("▼", x, y - 60, color, 18, anchor_x="center")

        arcade.draw_text("← → pour choisir  |  Entrée pour valider",
                         SCREEN_WIDTH // 2, 30, (100, 100, 140), 13,
                         anchor_x="center")

    def _find_sprite(self, nom: str) -> str | None:
        """Cherche le sprite face d'un starter dans asset/sprite/.
        
        Format attendu : NomPokemon_face.png  (ex: Flamiaou_face.png)
        Shiny ignoré ici (on affiche la version normale au choix du starter).
        """
        sprite_root = os.path.join(ASSET_PATH, "sprite")
        if not os.path.exists(sprite_root):
            return None

        # Cherche d'abord le fichier exact : Nom_face.png
        chemin_exact = os.path.join(sprite_root, f"{nom}_face.png")
        if os.path.exists(chemin_exact):
            return chemin_exact

        # Fallback : parcours récursif au cas où le sprite est dans un sous-dossier
        nom_lower = nom.lower()
        for root, _, files in os.walk(sprite_root):
            for f in files:
                f_lower = f.lower()
                # Doit contenir le nom + "_face" et ne pas être shiny
                if (f_lower.startswith(nom_lower) and
                        "_face" in f_lower and
                        "shiny" not in f_lower):
                    return os.path.join(root, f)
        return None

    def _draw_placeholder(self, x, y, color):
        arcade.draw_circle_filled(x, y, 40, (*color, 160))
        arcade.draw_circle_outline(x, y, 40, color, 2)

    # ------------------------------------------------------------------
    # Gestion des touches
    # ------------------------------------------------------------------
    def on_key_press(self, key, modifiers):
        if self.state in (S_TALK_1, S_TALK_2, S_TALK_3, S_TALK_4):
            self._handle_talk(key)
        elif self.state == S_GENDER:
            self._handle_gender(key)
        elif self.state == S_NAME:
            self._handle_name(key, modifiers)
        elif self.state == S_STARTER:
            self._handle_starter(key)

    def _handle_talk(self, key):
        if key != arcade.key.SPACE:
            return
        if not self._anim_done():
            self.displayed_chars = self._chars_on_page()
            return
        if not self._is_last_page():
            self.current_page    += 1
            self.displayed_chars  = 0
            return

        # Transitions selon l'état courant
        if self.state == S_TALK_1:
            self.starter_choice = 0
            self.state          = S_GENDER
        elif self.state == S_TALK_2:
            self.player_name = ""
            self.cursor_timer = 0.0
            self.state        = S_NAME
        elif self.state == S_TALK_3:
            self.starter_choice = 0
            self.state          = S_STARTER
        elif self.state == S_TALK_4:
            self._finish()

    def _handle_gender(self, key):
        if key == arcade.key.LEFT:
            self.starter_choice = (self.starter_choice - 1) % 2
        elif key == arcade.key.RIGHT:
            self.starter_choice = (self.starter_choice + 1) % 2
        elif key in (arcade.key.RETURN, arcade.key.ENTER):
            if self.starter_choice == 0:
                self.player_gender = "garçon"
                self.tex_player    = self.tex_boy
            else:
                self.player_gender = "fille"
                self.tex_player    = self.tex_girl
            self.starter_choice = 0
            self._rebuild_dialogue(S_TALK_2)
            self.state = S_TALK_2

    def _handle_name(self, key, modifiers):
        if key == arcade.key.BACKSPACE:
            self.player_name = self.player_name[:-1]
        elif key in (arcade.key.RETURN, arcade.key.ENTER):
            if self.player_name.strip():
                self._rebuild_dialogue(S_TALK_3)
                self.state = S_TALK_3
        else:
            char = self._key_to_char(key, modifiers)
            if char and len(self.player_name) < 10:
                self.player_name += char

    def _key_to_char(self, key, modifiers) -> str:
        shift = modifiers & arcade.key.MOD_SHIFT
        if arcade.key.A <= key <= arcade.key.Z:
            c = chr(key)
            return c.upper() if shift else c.lower()
        if arcade.key.KEY_0 <= key <= arcade.key.KEY_9:
            return chr(key)
        return {
            arcade.key.SPACE: " ",
            arcade.key.MINUS: "-",
        }.get(key, "")

    def _handle_starter(self, key):
        if key == arcade.key.LEFT:
            self.starter_choice = (self.starter_choice - 1) % 3
        elif key == arcade.key.RIGHT:
            self.starter_choice = (self.starter_choice + 1) % 3
        elif key in (arcade.key.RETURN, arcade.key.ENTER):
            nom = STARTER_LIST[self.starter_choice]
            self.starter_data = creer_starter(nom, self.poke_data)
            self._rebuild_dialogue(S_TALK_4)
            self.state = S_TALK_4

    # ------------------------------------------------------------------
    # Finalisation : sauvegarde + lancement du jeu
    # ------------------------------------------------------------------
    def _finish(self):
        nom  = self.player_name.strip() or "Joueur"
        save = creer_sauvegarde(nom, self.player_gender, self.starter_data)

        # Sauvegarde dans le slot
        slot_path = os.path.join(SAVES_PATH, f"slot_{self.slot_num}.json")
        with open(slot_path, "w", encoding="utf-8") as f:
            json.dump(save, f, ensure_ascii=False, indent=4)

        # Sauvegarde dans data/{nom}.json (format dresseur_config.json)
        player_path = os.path.join(DATA_PATH, f"{nom}.json")
        with open(player_path, "w", encoding="utf-8") as f:
            json.dump(save, f, ensure_ascii=False, indent=4)

        # Synchronise dresseur_config.json (utilisé par PokeFantasyGame)
        with open(DRESSEUR_JSON, "w", encoding="utf-8") as f:
            json.dump(save, f, ensure_ascii=False, indent=4)

        print(f"[INFO] Partie créée → {nom}.json (slot {self.slot_num})")
        print(f"[INFO] Starter : {self.starter_data['nom']} | "
              f"Nature : {self.starter_data['nature']}")

        # Ferme la fenêtre View et lance PokeFantasyGame (test.py à la racine)
        # Arreter la musique intro avant de lancer le jeu
        try:
            if getattr(self, 'bgm_player', None) is not None:
                arcade.stop_sound(self.bgm_player)
        except Exception:
            pass

        import test as game_module
        self.window.close()
        game_module.PokeFantasyGame(save_data=save, slot_num=self.slot_num)
        arcade.run()