import os
import sys
import json
import math
import arcade

# ---------------------------------------------------------------------------
# Chemins (main.py est à la racine du projet)
# ---------------------------------------------------------------------------
BASE_PATH  = os.path.abspath(os.path.dirname(__file__))
ASSET_PATH = os.path.join(BASE_PATH, "asset")
FONTS_PATH = os.path.join(ASSET_PATH, "fonts")
DATA_PATH  = os.path.join(BASE_PATH, "data")
SAVES_PATH = os.path.join(BASE_PATH, "saves")

os.makedirs(SAVES_PATH, exist_ok=True)

# S'assure que la racine ET core/ sont dans sys.path pour les imports
for _p in [BASE_PATH, os.path.join(BASE_PATH, "core")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Paramètres écran
# ---------------------------------------------------------------------------
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, DRESSEUR_JSON

# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
LOGO_IMG       = os.path.join(FONTS_PATH, "logo.jpg")
BACKGROUND_IMG = os.path.join(FONTS_PATH, "main.png")

# ---------------------------------------------------------------------------
# Couleurs
# ---------------------------------------------------------------------------
GOLD  = (255, 215, 0)
WHITE = (255, 255, 255)
GRAY  = (120, 120, 120)
RED   = (220, 60, 60)


# ---------------------------------------------------------------------------
# Utilitaire slots
# ---------------------------------------------------------------------------

def get_save_slots() -> list:
    """Retourne une liste de 3 éléments : None si vide, dict sinon."""
    slots = []
    for i in range(1, 4):
        path = os.path.join(SAVES_PATH, f"slot_{i}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    slots.append(json.load(f))
            except Exception:
                slots.append(None)
        else:
            slots.append(None)
    return slots


# ---------------------------------------------------------------------------
# États du menu
# ---------------------------------------------------------------------------
STATE_MAIN      = "main"
STATE_NEW_SLOTS = "new_slots"
STATE_CONTINUE  = "continue"
STATE_CONFIRM   = "confirm"


# ---------------------------------------------------------------------------
# MainMenuView
# ---------------------------------------------------------------------------

class MainMenuView(arcade.View):
    """Vue du menu principal (Nouvelle Partie / Continuer)."""

    def __init__(self):
        super().__init__()
        self.state        = STATE_MAIN
        self.selected     = 0
        self.slots        = get_save_slots()
        self.confirm_slot = None
        self.anim_timer   = 0.0

        # Textures
        self.bg_texture   = None
        self.logo_texture = None
        if os.path.exists(BACKGROUND_IMG):
            try:
                self.bg_texture = arcade.load_texture(BACKGROUND_IMG)
            except Exception:
                pass
        if os.path.exists(LOGO_IMG):
            try:
                self.logo_texture = arcade.load_texture(LOGO_IMG)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.slots = get_save_slots()   # rafraîchit les slots à chaque affichage

    def on_update(self, delta_time):
        self.anim_timer += delta_time

    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        # --- Background ---
        if self.bg_texture:
            arcade.draw_texture_rect(
                self.bg_texture,
                arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                  SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        else:
            arcade.draw_rect_filled(
                arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                arcade.color.DARK_BLUE
            )

        # Overlay sombre
        arcade.draw_rect_filled(
            arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            (0, 0, 0, 100)
        )

        # --- Logo ---
        if self.logo_texture:
            scale = min(400 / self.logo_texture.width, 160 / self.logo_texture.height)
            arcade.draw_texture_rect(
                self.logo_texture,
                arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90,
                                  int(self.logo_texture.width  * scale),
                                  int(self.logo_texture.height * scale))
            )
        else:
            arcade.draw_text("POKE FANTASY",
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
                             arcade.color.GOLD, 48,
                             anchor_x="center", bold=True)

        # Sous-titre animé
        alpha = int(abs(128 + 127 * math.sin(self.anim_timer * 2)))
        arcade.draw_text("SHINY EDITION",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 130,
                         (255, 215, 0, alpha), 18,
                         anchor_x="center", bold=True)

        # --- Contenu selon l'état ---
        if self.state == STATE_MAIN:
            self._draw_main_menu()
        elif self.state in (STATE_NEW_SLOTS, STATE_CONTINUE):
            titre = ("Nouvelle Partie — Choisir un slot"
                     if self.state == STATE_NEW_SLOTS
                     else "Continuer — Choisir un slot")
            self._draw_slot_selection(titre)
        elif self.state == STATE_CONFIRM:
            self._draw_confirm()

        # --- Aide bas d'écran ---
        arcade.draw_text(
            "↑↓ : Naviguer      Entrée : Valider      Échap : Retour",
            SCREEN_WIDTH // 2, 18, (200, 200, 200), 13, anchor_x="center"
        )

    # ------------------------------------------------------------------
    def _draw_main_menu(self):
        options = ["NOUVELLE PARTIE", "CONTINUER"]
        start_y = SCREEN_HEIGHT // 2 + 20

        for i, opt in enumerate(options):
            y     = start_y - i * 60
            color = GOLD  if i == self.selected else WHITE
            size  = 30    if i == self.selected else 24

            if i == self.selected:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(SCREEN_WIDTH // 2, y + 6, 320, 44),
                    (255, 255, 255, 30)
                )
                arcade.draw_text("▶", SCREEN_WIDTH // 2 - 145, y - 6,
                                  arcade.color.GOLD, 20, anchor_x="center")

            arcade.draw_text(opt, SCREEN_WIDTH // 2, y, color, size,
                             anchor_x="center", bold=(i == self.selected))

    # ------------------------------------------------------------------
    def _draw_slot_selection(self, titre: str):
        arcade.draw_text(titre,
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 130,
                         GOLD, 22, anchor_x="center", bold=True)

        for i, slot_data in enumerate(self.slots):
            y      = SCREEN_HEIGHT // 2 + 60 - i * 70
            is_sel = (i == self.selected)
            border = GOLD if is_sel else GRAY

            arcade.draw_rect_filled(
                arcade.rect.XYWH(SCREEN_WIDTH // 2, y, 480, 56),
                (255, 255, 255, 40) if is_sel else (0, 0, 0, 120)
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(SCREEN_WIDTH // 2, y, 480, 56),
                border, 2
            )

            label = f"SLOT {i + 1}"
            if slot_data:
                nom    = slot_data.get("nom_dresseur", "???")
                stage  = slot_data.get("stage", 1)
                argent = slot_data.get("argent", 0)
                # Fallback si PokeFantasyGame n'exporte pas encore niveau_pour_stage
                try:
                    from test import niveau_pour_stage
                    niv = niveau_pour_stage(stage)
                except (ImportError, AttributeError):
                    niv = stage * 5  # estimation simple : 5 niveaux par stage
                info   = f"{nom}  —  Stage {stage} (niv.{niv})  —  {argent}₽"
            else:
                info = "— Vide —"

            arcade.draw_text(label,
                             SCREEN_WIDTH // 2 - 220, y + 6,
                             GOLD if is_sel else WHITE, 16, bold=True)
            arcade.draw_text(info,
                             SCREEN_WIDTH // 2 - 40, y + 6,
                             WHITE if is_sel else GRAY, 13,
                             anchor_x="center")

    # ------------------------------------------------------------------
    def _draw_confirm(self):
        arcade.draw_rect_filled(
            arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 480, 160),
            (20, 20, 40, 230)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 480, 160),
            RED, 2
        )
        arcade.draw_text("⚠  ÉCRASER CETTE SAUVEGARDE ?",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 45,
                         RED, 20, anchor_x="center", bold=True)
        arcade.draw_text("Ce slot contient déjà une partie.",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10,
                         WHITE, 15, anchor_x="center")

        options = ["OUI — Écraser", "NON — Annuler"]
        for i, opt in enumerate(options):
            y     = SCREEN_HEIGHT // 2 - 25 - i * 35
            color = RED if (i == self.selected) else GRAY
            arcade.draw_text(
                ("▶ " if i == self.selected else "  ") + opt,
                SCREEN_WIDTH // 2, y, color, 17, anchor_x="center"
            )

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def on_key_press(self, key, modifiers):
        if self.state == STATE_MAIN:
            self._handle_main(key)
        elif self.state in (STATE_NEW_SLOTS, STATE_CONTINUE):
            self._handle_slots(key)
        elif self.state == STATE_CONFIRM:
            self._handle_confirm(key)

    def _handle_main(self, key):
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % 2
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % 2
        elif key in (arcade.key.RETURN, arcade.key.ENTER):
            if self.selected == 0:
                self.state    = STATE_NEW_SLOTS
                self.selected = 0
                self.slots    = get_save_slots()
            else:
                self.state    = STATE_CONTINUE
                self.selected = 0
                self.slots    = get_save_slots()

    def _handle_slots(self, key):
        if key == arcade.key.ESCAPE:
            self.state    = STATE_MAIN
            self.selected = 0
            return
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % 3
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % 3
        elif key in (arcade.key.RETURN, arcade.key.ENTER):
            slot_data = self.slots[self.selected]
            if self.state == STATE_CONTINUE:
                if slot_data:
                    self._lancer_jeu(slot_data, slot_num=self.selected + 1)
            else:  # STATE_NEW_SLOTS
                if slot_data:
                    self.confirm_slot = self.selected
                    self.selected     = 1
                    self.state        = STATE_CONFIRM
                else:
                    self._demarrer_nouvelle_partie(self.selected + 1)

    def _handle_confirm(self, key):
        if key == arcade.key.ESCAPE:
            self.state    = STATE_NEW_SLOTS
            self.selected = self.confirm_slot
            return
        if key in (arcade.key.UP, arcade.key.DOWN):
            self.selected = (self.selected + 1) % 2
        elif key in (arcade.key.RETURN, arcade.key.ENTER):
            if self.selected == 0:
                self._demarrer_nouvelle_partie(self.confirm_slot + 1)
            else:
                self.state    = STATE_NEW_SLOTS
                self.selected = self.confirm_slot

    # ------------------------------------------------------------------
    # Lancement
    # ------------------------------------------------------------------
    def _demarrer_nouvelle_partie(self, slot_num: int):
        """Lance l'IntroView pour créer une nouvelle partie."""
        from core.intro import IntroView
        self.window.show_view(IntroView(slot_num=slot_num))

    def _lancer_jeu(self, save_data: dict, slot_num: int = None):
        """Charge une sauvegarde et lance PokeFantasyGame.

        PokeFantasyGame est une arcade.Window autonome :
        on ferme la fenêtre menu et on démarre le jeu.
        """
        # Récupère slot_num depuis save_data si non fourni explicitement
        if slot_num is None:
            slot_num = save_data.get("slot_num", 1)

        # S'assure que slot_num est stocké dans la sauvegarde (pour les autosaves)
        save_data["slot_num"] = slot_num

        # Synchronise DRESSEUR_JSON
        try:
            with open(DRESSEUR_JSON, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[WARN] Sync DRESSEUR_JSON : {e}")

        import test as game_module
        self.window.close()
        game_module.PokeFantasyGame(save_data=save_data, slot_num=slot_num)
        arcade.run()


# ---------------------------------------------------------------------------
# MainWindow + point d'entrée
# ---------------------------------------------------------------------------

class MainWindow(arcade.Window):
    """Fenêtre racine qui héberge MainMenuView et IntroView."""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
        self.show_view(MainMenuView())


def main():
    MainWindow()
    arcade.run()


if __name__ == "__main__":
    main()