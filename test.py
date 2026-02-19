import json
import math
import os
import random

import arcade

from core.config import (
    AUDIO_PATH, BATTLE_THEME_PATH, CAPA_JSON, DRESSEUR_JSON, EVOLUTION_JSON,
    OBJET_PATH, POKEMON_DATA_JSON, SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH,
    SPRITE_PATH, STATUS_DATA, TYPE_ICON_PATH,
)
from core.engines import CombatEngine, ExperienceEngine, ItemEngine, LevelEngine, StatusEngine
from core.models import Pokemon
from core.pokedex import PokedexManager
from core.utils import normaliser
from core.capture import CaptureEngine
from core.turn_manager import TurnManager
from core.nature import NatureEngine


class PokeFantasyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.WHITE)

        self.etat        = "PRINCIPAL"
        self.index_sel   = 0
        self.message     = ""
        self.show_boosts = False
        self.item_en_cours = None

        self.ui_text = arcade.Text("", 50, 100, arcade.color.BLACK, 16, multiline=True, width=700)

        # Animation Poké Ball
        self.ball_x, self.ball_y         = 0, 0
        self.ball_dest_x, self.ball_dest_y = 575, 445
        self.ball_angle  = 0
        self.ball_active = False
        self.tex_ball_anim = None

        # Animation évolution
        self.evo_target_name = None
        self.evo_timer = 0
        self.evo_flash = True
        self.tex_evo_old = None
        self.tex_evo_new = None

        self.type_textures: dict = {}
        self.tour_num = 1  # Compteur de tours (utilisé par CaptureEngine)

        self.charger_donnees()
        for p in self.equipe:
            PokedexManager.enregistrer(p, capture=True)
        self.generer_ennemi_aleatoire()
        self.charger_sprites()

        try:
            self.bgm        = arcade.load_sound(BATTLE_THEME_PATH)
            self.bgm_player = arcade.play_sound(self.bgm, volume=0.5, loop=True)
        except Exception:
            self.bgm = None

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def charger_donnees(self):
        self.poke_data_map = {}
        if os.path.exists(POKEMON_DATA_JSON):
            with open(POKEMON_DATA_JSON, 'r', encoding='utf-8') as f:
                self.poke_data_map = json.load(f)

        self.evolution_config = {}
        if os.path.exists(EVOLUTION_JSON):
            with open(EVOLUTION_JSON, 'r', encoding='utf-8') as f:
                self.evolution_config = json.load(f)

        with open(DRESSEUR_JSON, 'r', encoding='utf-8') as f:
            self.data_full = json.load(f)
        with open(CAPA_JSON, 'r', encoding='utf-8') as f:
            self.db_capas = json.load(f)

        self.equipe   = [Pokemon(p, self.db_capas, self.poke_data_map) for p in self.data_full.get("equipe", [])]
        self.active_p = self.equipe[0]

        self.inventaire = []
        inv = self.data_full.get("inventaire", {})
        for cat in inv:
            for n, q in inv[cat].items():
                if q > 0:
                    self.inventaire.append({"nom": n, "qty": q, "cat": cat})

    def sauvegarder_donnees(self):
        self.data_full["equipe"] = [p.to_dict() for p in self.equipe]
        new_inv = {"potions": {}, "balls": {}}
        for it in self.inventaire:
            cat = it["cat"]
            if cat not in new_inv:
                new_inv[cat] = {}
            new_inv[cat][it["nom"]] = it["qty"]
        self.data_full["inventaire"] = new_inv
        with open(DRESSEUR_JSON, 'w', encoding='utf-8') as f:
            json.dump(self.data_full, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Sprites & textures
    # ------------------------------------------------------------------

    def charger_sprites(self):
        self.tex_joueur = self._get_tex(self.active_p.nom, "dos")
        self.tex_ennemi = self._get_tex(self.ennemi.nom, "face")

    def _get_tex(self, nom, mode):
        nom_net = nom.lower()
        is_shiny = "shiny" in nom_net
        base_name_search = normaliser(nom.replace("Shiny", "").replace("shiny", ""))

        for root, _, files in os.walk(SPRITE_PATH):
            for f in files:
                f_norm = normaliser(f)
                if base_name_search in f_norm and mode in f_norm:
                    if is_shiny:
                        if "shiny" in f_norm:
                            return arcade.load_texture(os.path.join(root, f))
                    else:
                        if "shiny" not in f_norm:
                            return arcade.load_texture(os.path.join(root, f))

        return arcade.make_soft_square_texture(200, arcade.color.GRAY)

    def _get_type_icon(self, type_nom):
        t_raw = normaliser(type_nom)
        mapping = {
            "water": "eau", "fire": "feu", "grass": "plante",
            "electric": "electrick", "ice": "glace", "fighting": "combat",
            "poison": "poison", "ground": "sol", "flying": "vol",
            "psychic": "psy", "bug": "insecte", "rock": "roche",
            "ghost": "spectre", "dragon": "dragon", "dark": "tenebres",
            "steel": "acier", "fairy": "fee", "normal": "normal",
        }
        filename = mapping.get(t_raw, t_raw)
        if filename in self.type_textures:
            return self.type_textures[filename]
        path = os.path.join(TYPE_ICON_PATH, f"{filename}.png")
        if os.path.exists(path):
            tex = arcade.load_texture(path)
            self.type_textures[filename] = tex
            return tex
        return None

    def _get_ball_tex(self, ball_nom):
        target = normaliser(ball_nom)
        if os.path.exists(OBJET_PATH):
            for f in os.listdir(OBJET_PATH):
                if target in normaliser(f):
                    return arcade.load_texture(os.path.join(OBJET_PATH, f))
        return arcade.make_soft_circle_texture(30, arcade.color.RED)

    # ------------------------------------------------------------------
    # Combat — génération d'ennemi
    # ------------------------------------------------------------------

    def generer_ennemi_aleatoire(self):
        """Génère un ennemi aléatoire avec une nature et un set d'attaques cohérents."""
        possibles = []
        for root, _, files in os.walk(SPRITE_PATH):
            for f in files:
                if "_face" in f.lower() and "shiny" not in f.lower():
                    nom_net = f.split("_face")[0].replace("_", " ")
                    if nom_net not in possibles:
                        possibles.append(nom_net)

        nom_choisi = random.choice(possibles) if possibles else "Pikachu"
        lvl        = max(1, self.active_p.niveau + random.randint(-1, 2))

        # Récupère les types du pokémon depuis la base de données
        types_ennemi = ["Normal"]
        for k, v in self.poke_data_map.items():
            if normaliser(k) == normaliser(nom_choisi):
                types_ennemi = v.get("types", ["Normal"])
                break

        # Choisit des attaques cohérentes avec les types du Pokémon
        # Priorité aux capacités du même type (STAB), complétées par des capacités aléatoires
        moves_stab = [
            m for m in self.db_capas
            if any(
                normaliser(m.get("type", "")) in [normaliser(t), t.lower()]
                for t in types_ennemi
            ) and m.get("puissance")
        ]
        moves_autres = [
            m for m in self.db_capas
            if m not in moves_stab and m.get("puissance")
        ]
        moves_statut = [
            m for m in self.db_capas
            if not m.get("puissance") or m.get("categorie") == "Statut"
        ]

        # Compose le set : 2 STAB + 1 autre + 1 statut (si dispo), sinon complète aléatoirement
        pool_stab   = random.sample(moves_stab, min(2, len(moves_stab)))
        pool_autres = random.sample(moves_autres, min(1, len(moves_autres)))
        pool_statut = random.sample(moves_statut, min(1, len(moves_statut)))
        moves_pool  = pool_stab + pool_autres + pool_statut
        # Complète à 4 si nécessaire
        if len(moves_pool) < 4:
            reste = [m for m in self.db_capas if m not in moves_pool]
            moves_pool += random.sample(reste, min(4 - len(moves_pool), len(reste)))
        moves_pool = moves_pool[:4]

        # Nature aléatoire
        nature_choisie = random.choice(list(NatureEngine.DATA.keys()))

        # Stats de base depuis pokemon_data ou valeurs par défaut
        stats_base = {"attaque": 40 + lvl, "defense": 40 + lvl, "vitesse": 40 + lvl,
                      "attaque_spe": 40 + lvl, "defense_spe": 40 + lvl}
        for k, v in self.poke_data_map.items():
            if normaliser(k) == normaliser(nom_choisi):
                raw = v.get("stats", {})
                stats_base = {
                    "attaque":      max(1, int(((2 * raw.get("attaque", 50)) * lvl / 100) + 5)),
                    "defense":      max(1, int(((2 * raw.get("defense", 50)) * lvl / 100) + 5)),
                    "vitesse":      max(1, int(((2 * raw.get("vitesse", 50)) * lvl / 100) + 5)),
                    "attaque_spe":  max(1, int(((2 * raw.get("attaque_spe", 50)) * lvl / 100) + 5)),
                    "defense_spe":  max(1, int(((2 * raw.get("defense_spe", 50)) * lvl / 100) + 5)),
                }
                break

        # Applique la nature aux stats
        stats_avec_nature = NatureEngine.apply_nature_to_stats(nature_choisie, stats_base)
        hp_base = int(((2 * 60) * lvl / 100) + lvl + 10)

        data_ennemi = {
            "nom":       nom_choisi.capitalize(),
            "niveau":    lvl,
            "nature":    nature_choisie,
            "types":     types_ennemi,
            "hp_base":   hp_base,
            "hp_actuel": hp_base,
            "stats":     stats_avec_nature,
            "capacites": [m["nom_attaque"] for m in moves_pool],
        }
        self.ennemi    = Pokemon(data_ennemi, self.db_capas, self.poke_data_map)
        self.tour_num  = 1  # réinitialise le compteur de tours pour la capture
        PokedexManager.enregistrer(self.ennemi, capture=False)

    # ------------------------------------------------------------------
    # Évolution
    # ------------------------------------------------------------------

    def verifier_evolution(self, pokemon):
        nom_id = normaliser(pokemon.nom.replace("Shiny", "").replace("shiny", ""))
        if nom_id in self.evolution_config:
            evo_data = self.evolution_config[nom_id]
            options  = evo_data if isinstance(evo_data, list) else [evo_data]
            for opt in options:
                if opt["methode"] == "level" and pokemon.niveau >= opt["valeur"]:
                    return opt["cible"]
        return None

    def lancer_evolution(self, cible_nom):
        is_shiny          = "shiny" in self.active_p.nom.lower()
        nom_complet_cible = f"{cible_nom} Shiny" if is_shiny else cible_nom
        self.evo_target_name = nom_complet_cible
        self.tex_evo_old     = self._get_tex(self.active_p.nom, "dos")
        self.tex_evo_new     = self._get_tex(nom_complet_cible, "dos")
        self.evo_timer       = 0
        self.etat            = "ANIM_EVO"

    def finaliser_evolution(self):
        old_nom        = self.active_p.nom
        is_shiny       = "shiny" in old_nom.lower()
        base_target_norm = normaliser(self.evo_target_name.replace("Shiny", "").replace("shiny", ""))
        vrai_nom_base    = base_target_norm.capitalize()

        for k, v in self.poke_data_map.items():
            if normaliser(k) == base_target_norm:
                vrai_nom_base       = k
                self.active_p.types = v.get("types", ["Normal"])
                break

        self.active_p.nom = f"{vrai_nom_base} Shiny" if is_shiny else vrai_nom_base

        p_tmp = self.active_p.to_dict()
        LevelEngine.recalculer_stats(p_tmp, self.poke_data_map)
        self.active_p.hp_base = p_tmp['hp_base']
        self.active_p.hp      = p_tmp['hp_actuel']
        self.active_p.stats   = p_tmp['stats']

        self.charger_sprites()
        self.sauvegarder_donnees()
        PokedexManager.enregistrer(self.active_p, capture=True)
        self.message = f"Félicitations ! {old_nom} a évolué en {self.active_p.nom} !"
        self.etat    = "MESSAGE_V"

    # ------------------------------------------------------------------
    # Boucle de jeu
    # ------------------------------------------------------------------

    def on_update(self, delta_time):
        if self.etat == "ANIM_BALL":
            dx, dy = self.ball_dest_x - self.ball_x, self.ball_dest_y - self.ball_y
            dist   = math.sqrt(dx**2 + dy**2)
            if dist > 10:
                self.ball_x    += dx * 0.15
                self.ball_y    += dy * 0.15
                self.ball_angle += 20
            else:
                self.ball_active = False
                self.finaliser_capture()

        elif self.etat == "ANIM_EVO":
            self.evo_timer += delta_time
            speed = 0.3 - (self.evo_timer * 0.05)
            self.evo_flash = (int(self.evo_timer / max(0.05, speed)) % 2 == 0)
            if self.evo_timer > 4.0:
                self.finaliser_evolution()

    def on_draw(self):
        self.clear()

        if self.etat == "GAME_OVER":
            arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                             arcade.color.RED, 40, anchor_x="center")
            return

        if self.etat == "ANIM_EVO":
            tex = self.tex_evo_old if self.evo_flash else self.tex_evo_new
            arcade.draw_texture_rect(tex, arcade.rect.LBWH(100, 200, 250, 250))
        else:
            if self.active_p.hp > 0:
                arcade.draw_texture_rect(self.tex_joueur, arcade.rect.LBWH(100, 200, 250, 250))
            arcade.draw_texture_rect(self.tex_ennemi, arcade.rect.LBWH(450, 320, 250, 250))

        if self.ball_active and self.tex_ball_anim:
            arcade.draw_texture_rect(
                self.tex_ball_anim,
                arcade.rect.XYWH(self.ball_x, self.ball_y, 45, 45),
                angle=self.ball_angle,
            )

        # Panneau du bas
        arcade.draw_rect_filled(arcade.rect.LBWH(0, 0, 800, 200), arcade.color.WHITE)
        arcade.draw_rect_outline(arcade.rect.LBWH(0, 0, 800, 200), arcade.color.BLACK, 5)

        self.draw_status_bar(50, 500, self.active_p, show_xp=True)
        self.draw_status_bar(450, 500, self.ennemi, show_xp=False)

        if self.show_boosts:
            self.draw_boost_overlay()
        else:
            self.render_menu()

    # ------------------------------------------------------------------
    # Dessin UI
    # ------------------------------------------------------------------

    def draw_status_bar(self, x, y, p, show_xp=False):
        BARRE_WIDTH = 150
        arcade.draw_text(f"{p.nom} Lv.{p.niveau}", x, y + 35, arcade.color.BLACK, 14, bold=True)

        for i, t in enumerate(p.types):
            icon = self._get_type_icon(t)
            if icon:
                arcade.draw_texture_rect(icon, arcade.rect.XYWH(x + 120 + (i * 35), y + 36, 30, 30))

        arcade.draw_rect_filled(arcade.rect.LBWH(x, y + 5, BARRE_WIDTH, 12), arcade.color.GRAY)
        hp_ratio = max(0, min(1.0, p.hp / p.hp_base))
        hp_clr   = (arcade.color.GREEN if hp_ratio > 0.5
                    else arcade.color.ORANGE if hp_ratio > 0.2
                    else arcade.color.RED)
        arcade.draw_rect_filled(arcade.rect.LBWH(x, y + 5, BARRE_WIDTH * hp_ratio, 12), hp_clr)
        arcade.draw_rect_outline(arcade.rect.LBWH(x, y + 5, BARRE_WIDTH, 12), arcade.color.BLACK, 2)
        arcade.draw_text(f"{int(p.hp)}/{p.hp_base}", x, y - 15, arcade.color.BLACK, 10)

        if p.statut in STATUS_DATA:
            s = STATUS_DATA[p.statut]
            arcade.draw_rect_filled(arcade.rect.XYWH(x + BARRE_WIDTH + 25, y + 10, 30, 15), (40, 40, 40))
            arcade.draw_text(s["label"], x + BARRE_WIDTH + 25, y + 10,
                             s["color"], 9, bold=True, anchor_x="center", anchor_y="center")

        if show_xp:
            arcade.draw_rect_filled(arcade.rect.LBWH(x, y - 25, BARRE_WIDTH, 6), arcade.color.DARK_GRAY)
            xp_ratio = max(0, min(1.0, p.xp / p.xp_max))
            arcade.draw_rect_filled(arcade.rect.LBWH(x, y - 25, BARRE_WIDTH * xp_ratio, 6), arcade.color.SKY_BLUE)
            arcade.draw_rect_outline(arcade.rect.LBWH(x, y - 25, BARRE_WIDTH, 6), arcade.color.BLACK, 1)

    def draw_boost_overlay(self):
        """Affiche les stages (boosts/debuffs) des deux Pokémon + leur nature."""
        arcade.draw_rect_filled(arcade.rect.XYWH(400, 300, 780, 280), (20, 20, 20, 230))
        arcade.draw_rect_outline(arcade.rect.XYWH(400, 300, 780, 280), arcade.color.GOLD, 2)
        arcade.draw_text("[ V ] Fermer", 400, 425, arcade.color.GOLD, 11, anchor_x="center")

        # --- Joueur (gauche) ---
        arcade.draw_text(f"⚔ {self.active_p.nom} — Nature: {self.active_p.nature}",
                         120, 400, arcade.color.CYAN, 12, bold=True, anchor_x="center")
        y_j = 378
        for stat, val in self.active_p.stages.items():
            color = arcade.color.LIGHT_GREEN if val > 0 else arcade.color.RED if val < 0 else arcade.color.LIGHT_GRAY
            fleche = "▲" * abs(val) if val > 0 else "▼" * abs(val) if val < 0 else "—"
            arcade.draw_text(f"{stat.replace('_',' ').capitalize():<14} {fleche:>6}",
                             60, y_j, color, 11)
            y_j -= 22

        # --- Séparateur ---
        arcade.draw_line(400, 175, 400, 425, arcade.color.GRAY, 1)

        # --- Ennemi (droite) ---
        arcade.draw_text(f"⚔ {self.ennemi.nom} — Nature: {self.ennemi.nature}",
                         590, 400, arcade.color.ORANGE, 12, bold=True, anchor_x="center")
        y_e = 378
        for stat, val in self.ennemi.stages.items():
            color = arcade.color.LIGHT_GREEN if val > 0 else arcade.color.RED if val < 0 else arcade.color.LIGHT_GRAY
            fleche = "▲" * abs(val) if val > 0 else "▼" * abs(val) if val < 0 else "—"
            arcade.draw_text(f"{stat.replace('_',' ').capitalize():<14} {fleche:>6}",
                             440, y_e, color, 11)
            y_e -= 22

    def draw_selector(self, x, y, width=180, height=40):
        arcade.draw_rect_outline(arcade.rect.LBWH(x - 10, y - 5, width, height), arcade.color.RED, 3)

    def render_menu(self):
        if self.etat == "PRINCIPAL":
            opts = ["ATTAQUE", "SAC", "POKEMON", "FUITE"]
            for i, o in enumerate(opts):
                tx, ty = 150 + (i % 2) * 400, 140 - (i // 2) * 70
                if i == self.index_sel:
                    self.draw_selector(tx, ty, 200, 45)
                arcade.draw_text(o, tx, ty, arcade.color.BLACK, 22, bold=True)

        elif self.etat == "ATTAQUE":
            for i, m in enumerate(self.active_p.moves_obj):
                tx, ty = 100 + (i % 2) * 400, 140 - (i // 2) * 70
                if i == self.index_sel:
                    self.draw_selector(tx, ty, 300, 45)
                t_atk = m.get("type", "Normal")
                icon  = self._get_type_icon(t_atk)
                if icon:
                    arcade.draw_texture_rect(icon, arcade.rect.XYWH(tx + 20, ty + 12, 60, 22))
                arcade.draw_text(m["nom_attaque"].upper(), tx + 60, ty, arcade.color.BLACK, 18)

        elif self.etat in ["EQUIPE", "CHOIX_SOIN"]:
            for i, p in enumerate(self.equipe):
                tx, ty = 80 + (i % 2) * 400, 140 - (i // 2) * 60
                if i == self.index_sel:
                    self.draw_selector(tx, ty, 350, 35)
                arcade.draw_text(f"{p.nom} {int(p.hp)}/{p.hp_base}", tx, ty, arcade.color.BLACK, 14)

        elif self.etat == "SAC":
            visible = self.inventaire[self.index_sel // 4 * 4 : self.index_sel // 4 * 4 + 4]
            for i, it in enumerate(visible):
                tx, ty = 100 + (i % 2) * 400, 140 - (i // 2) * 60
                if i == self.index_sel % 4:
                    self.draw_selector(tx, ty, 300, 35)
                arcade.draw_text(f"{it['nom']} x{it['qty']}", tx, ty, arcade.color.BLACK, 16)

        elif self.etat == "DEMANDE_EVO":
            arcade.draw_text(f"Quoi ? {self.active_p.nom} évolue !",
                             400, 140, arcade.color.BLACK, 20, anchor_x="center")
            arcade.draw_text("Appuyez sur Entrée pour continuer",
                             400, 80, arcade.color.GRAY, 14, anchor_x="center")

        elif self.etat.startswith("MESSAGE") or self.etat in ["ANIM_BALL", "ANIM_EVO"]:
            self.ui_text.text = self.message
            self.ui_text.draw()

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    def on_key_press(self, key, modifiers):
        if key == arcade.key.V:
            self.show_boosts = not self.show_boosts
            return
        if self.show_boosts or self.etat in ["GAME_OVER", "ANIM_BALL", "ANIM_EVO"]:
            return
        if key == arcade.key.X:
            if self.etat == "CHOIX_SOIN":
                self.etat = "SAC"
                return
            if not (self.etat == "EQUIPE" and self.active_p.hp <= 0):
                self.etat      = "PRINCIPAL"
                self.index_sel = 0
                return

        nb_max = 4
        if self.etat == "SAC":
            nb_max = len(self.inventaire)
        elif self.etat in ["EQUIPE", "CHOIX_SOIN"]:
            nb_max = len(self.equipe)

        if nb_max > 0:
            if key == arcade.key.RIGHT: self.index_sel = (self.index_sel + 1) % nb_max
            elif key == arcade.key.LEFT:  self.index_sel = (self.index_sel - 1) % nb_max
            elif key == arcade.key.UP:    self.index_sel = (self.index_sel - 2) % nb_max
            elif key == arcade.key.DOWN:  self.index_sel = (self.index_sel + 2) % nb_max

        if key in [arcade.key.ENTER, arcade.key.SPACE]:
            self.valider_selection()

    def valider_selection(self):
        if self.etat == "PRINCIPAL":
            actions = {0: "ATTAQUE", 1: "SAC", 2: "EQUIPE"}
            if self.index_sel in actions:
                self.etat = actions[self.index_sel]
            elif self.index_sel == 3:
                self.message = "Fuite reussie !"
                self.etat    = "MESSAGE_V"
            self.index_sel = 0

        elif self.etat == "ATTAQUE":
            m = self.active_p.moves_obj[self.index_sel]
            # Phase joueur via TurnManager
            msg_joueur = TurnManager.executer_attaque(self.active_p, self.ennemi, m)
            # Effets de fin de tour côté joueur
            msg_eot_j  = TurnManager.appliquer_effets_fin_de_tour(self.active_p)
            self.message = f"{msg_joueur}\n{msg_eot_j}".strip()
            self.tour_num = getattr(self, 'tour_num', 1) + 1
            self.etat = "MESSAGE_J"

        elif self.etat == "SAC":
            self.item_en_cours = self.inventaire[self.index_sel]
            if "ball" in self.item_en_cours["nom"].lower():
                self.tex_ball_anim = self._get_ball_tex(self.item_en_cours["nom"])
                self.ball_x, self.ball_y, self.ball_active = 225, 325, True
                self.etat    = "ANIM_BALL"
                self.message = f"Lancement de {self.item_en_cours['nom']}..."
            else:
                self.etat      = "CHOIX_SOIN"
                self.index_sel = 0

        elif self.etat == "CHOIX_SOIN":
            ok, msg = ItemEngine.utiliser_objet(self.item_en_cours["nom"], self.equipe[self.index_sel])
            if ok:
                self.item_en_cours["qty"] -= 1
                if self.item_en_cours["qty"] <= 0:
                    self.inventaire.remove(self.item_en_cours)
                self.sauvegarder_donnees()
                self.message = msg
                self.etat    = "MESSAGE_V"
            else:
                self.message = msg
                self.etat    = "MESSAGE_J"

        elif self.etat == "EQUIPE":
            s = self.equipe[self.index_sel]
            if s.hp > 0:
                self.active_p = s
                self.charger_sprites()
                self.message = f"Go {s.nom} !"
                self.etat    = "MESSAGE_J"

        elif self.etat == "MESSAGE_J":
            if self.ennemi.hp <= 0:
                self.message = f"{self.ennemi.nom} est KO !"
                self.attribuer_xp()
            else:
                # Riposte de l'ennemi via TurnManager
                m_ennemi   = random.choice(self.ennemi.moves_obj)
                msg_ennemi = TurnManager.executer_attaque(self.ennemi, self.active_p, m_ennemi)
                msg_eot_e  = TurnManager.appliquer_effets_fin_de_tour(self.ennemi)
                self.message = f"{msg_ennemi}\n{msg_eot_e}".strip()
                self.etat    = "MESSAGE_E"

        elif self.etat == "MESSAGE_E":
            if self.active_p.hp <= 0:
                if all(p.hp <= 0 for p in self.equipe):
                    self.etat = "GAME_OVER"
                else:
                    self.message = "Pokemon KO ! Changez !"
                    self.etat    = "EQUIPE"
            else:
                self.etat = "PRINCIPAL"

        elif self.etat == "MESSAGE_V":
            cible = self.verifier_evolution(self.active_p)
            if cible:
                self.evo_target_name = cible
                self.etat            = "DEMANDE_EVO"
            else:
                if self.ennemi.hp <= 0:
                    self.generer_ennemi_aleatoire()
                    self.charger_sprites()
                self.etat      = "PRINCIPAL"
                self.index_sel = 0

        elif self.etat == "DEMANDE_EVO":
            self.lancer_evolution(self.evo_target_name)

    # ------------------------------------------------------------------
    # Capture & XP
    # ------------------------------------------------------------------

    def finaliser_capture(self):
        self.item_en_cours["qty"] -= 1
        if self.item_en_cours["qty"] <= 0 and self.item_en_cours in self.inventaire:
            self.inventaire.remove(self.item_en_cours)

        tour = getattr(self, 'tour_num', 1)
        succes, msg_capture = CaptureEngine.tenter_capture(
            self.item_en_cours["nom"], self.ennemi, tour=tour
        )

        if succes:
            self.equipe.append(self.ennemi)
            PokedexManager.enregistrer(self.ennemi, capture=True)
            self.sauvegarder_donnees()
            self.message = msg_capture
            self.generer_ennemi_aleatoire()
            self.charger_sprites()
            self.etat = "MESSAGE_V"
        else:
            self.message = msg_capture
            self.etat    = "MESSAGE_J"

    def attribuer_xp(self):
        xp_gain = ExperienceEngine.calculer_xp_gagne(self.ennemi)
        logs    = self.active_p.gain_xp(xp_gain)
        self.sauvegarder_donnees()
        log_txt      = "\n".join(logs)
        self.message = f"{self.ennemi.nom} est KO !\n+{xp_gain} XP.\n{log_txt}"
        self.etat    = "MESSAGE_V"


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    game = PokeFantasyGame()
    arcade.run()