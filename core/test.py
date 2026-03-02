"""
test.py — PokeFantasyGame : boucle de jeu principale.

Nouveautés v2 :
  - Système de stages avec niveaux cohérents (stage 1 → niv 2-3, stage 99 → niv 95-96)
  - Dresseur IA (20% par stage) via core.dresseur.DresseurIA
  - Récompenses monétaires via core.monnaie.MonnaieEngine (POO)
  - Boutique inter-stage (balls + soins à prix cohérents)
  - Affichage stage en haut à gauche
  - Pokémon filtrés par niveau (pas de Mammochon niv 5)
  - Musique de l'intro conservée en jeu
"""

import json
import math
import os
import random

import arcade

from core.config import (
    AUDIO_PATH, BATTLE_THEME_PATH, CAPA_JSON, DRESSEUR_JSON, EVOLUTION_JSON,
    OBJET_PATH, POKEMON_DATA_JSON, SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH,
    SPRITE_PATH, STATUS_DATA, TYPE_ICON_PATH, SAVES_PATH,
)
from core.engines import CombatEngine, ExperienceEngine, ItemEngine, LevelEngine, StatusEngine
from core.models import Pokemon
from core.pokedex import PokedexManager
from core.utils import normaliser
from core.capture import CaptureEngine
from core.turn_manager import TurnManager
from core.nature import NatureEngine
from core.monnaie import MonnaieEngine
from core.dresseur import DresseurIA
from core.boss import BossIA, BOSS_MUSIC_PATH, BOSS_BG_PATH


# ---------------------------------------------------------------------------
# Chemins assets backgrounds & pokedex
# ---------------------------------------------------------------------------
_BASE_PATH   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_FONT_PATH   = os.path.join(_BASE_PATH, "asset", "fonts")

# Fichier pokedex JSON (cree par PokedexManager)
_POKEDEX_JSON = os.path.join(_BASE_PATH, "data", "pokedex.json")

# Mapping type → fichier background (dans asset/fonts/)
# Basé sur les types disponibles : acier, combat, dragon, eau, electrick, fee,
# feu, glace, insecte, normal, plante, poison, psy, roche, sol, spectre, tenebres, vol
TYPE_BACKGROUNDS = {
    # Eau / Glace → glace.png
    "water": "glace.png", "ice": "glace.png",
    # Psy / Electrik → labo.jpg
    "psychic": "labo.jpg", "electric": "labo.jpg",
    # Normal / Fée → prairie.jpg
    "normal": "prairie.jpg", "fairy": "prairie.jpg",
    # Sol / Feu / Roche / Acier → volcan.jpg
    "ground": "volcan.jpg", "fire": "volcan.jpg",
    "rock": "volcan.jpg", "steel": "volcan.jpg",
    # Insecte / Plante → jungle.png
    "bug": "jungle.png", "grass": "jungle.png",
    # Combat / Dragon / Vol → sommet.png
    "fighting": "sommet.png", "dragon": "sommet.png", "flying": "sommet.png",
    # Spectre / Tenebre / Poison → manoir.png
    "ghost": "manoir.png", "dark": "manoir.png", "poison": "manoir.png",
}
BG_DEFAUT = "prairie.jpg"
# Background dresseur/boss (arene)
BG_ARENE  = "arene.jpg"

# ---------------------------------------------------------------------------
# Catalogue boutique
# ---------------------------------------------------------------------------
BOUTIQUE_CATALOGUE = [
    {"nom": "poke-ball",    "cat": "balls",   "prix": 200,  "desc": "Ball standard"},
    {"nom": "great-ball",   "cat": "balls",   "prix": 600,  "desc": "Ball amelioree (x1.5)"},
    {"nom": "ultra-ball",   "cat": "balls",   "prix": 1200, "desc": "Ball puissante (x2)"},
    {"nom": "master-ball",  "cat": "balls",   "prix": 9999, "desc": "Capture garantie !"},
    {"nom": "potion",       "cat": "potions", "prix": 300,  "desc": "Restore 20 PV"},
    {"nom": "super-potion", "cat": "potions", "prix": 700,  "desc": "Restore 50 PV"},
    {"nom": "hyper-potion", "cat": "potions", "prix": 1500, "desc": "Restore 200 PV"},
    {"nom": "max-potion",   "cat": "potions", "prix": 2500, "desc": "Restore tous les PV"},
    {"nom": "rappel",       "cat": "potions", "prix": 1500, "desc": "Revive un Pokemon KO"},
    {"nom": "max-rappel",   "cat": "potions", "prix": 4000, "desc": "Revive avec PV max"},
]


# ---------------------------------------------------------------------------
# PokeFantasyGame
# ---------------------------------------------------------------------------

class PokeFantasyGame(arcade.Window):

    def __init__(self, save_data: dict = None, slot_num: int = None,
                 bgm=None, bgm_player=None):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.WHITE)

        # --- Save / slot ---
        self._save_data_init = save_data
        self.slot_num = (slot_num
                         or (save_data.get("slot_num") if save_data else None)
                         or 1)

        # --- Musique (héritée de l'intro si disponible) ---
        self.bgm        = bgm
        self.bgm_player = bgm_player

        # --- États ---
        self.etat        = "INTER_STAGE"   # démarre toujours par le menu inter-stage
        self.index_sel   = 0
        self.message     = ""
        self.show_boosts = False
        self.item_en_cours  = None
        self.est_dresseur   = False       # True quand on combat un dresseur IA
        self.dresseur_actif = None        # Instance DresseurIA en cours
        self.ennemi         = None        # Pokemon adverse actuel (sauvage ou dresseur)

        self.ui_text = arcade.Text("", 50, 100, arcade.color.BLACK, 16,
                                   multiline=True, width=700)

        # --- Animation Poké Ball ---
        self.ball_x, self.ball_y           = 0, 0
        self.ball_dest_x, self.ball_dest_y = 575, 445
        self.ball_angle  = 0
        self.ball_active = False
        self.tex_ball_anim = None

        # --- Animation évolution ---
        self.evo_target_name = None
        self.evo_timer = 0
        self.evo_flash = True
        self.tex_evo_old = None
        self.tex_evo_new = None

        # --- Textures types ---
        self.type_textures: dict = {}
        self.tour_num = 1

        # --- Textures boutique ---
        self.tex_joueur = None
        self.tex_ennemi = None

        # --- Background combat ---
        self._bg_cache: dict = {}   # {filename: texture}
        self._bg_actuel = None      # texture fond actuel

        # --- Pokédex inter-stage ---
        self.pokedex_page = 0       # page courante de l'écran pokédex

        # --- Boss stage 100 ---
        self.est_boss        = False    # True pendant un combat boss
        self.boss_actif      = None     # Instance BossIA
        self.boss_victoire   = False    # True après avoir battu le boss

        # --- Capture : gestion équipe pleine (6 max) ---
        self._pokemon_capture_temp = None   # Pokemon capturé en attente de décision
        self.index_sacrifice       = 0      # index sélectionné pour sacrifice

        self.charger_donnees()
        for p in self.equipe:
            PokedexManager.enregistrer(p, capture=True)

        # --- Musique de bataille (toujours lancée : l'intro arrête la sienne) ---
        try:
            self.bgm        = arcade.load_sound(BATTLE_THEME_PATH)
            self.bgm_player = arcade.play_sound(self.bgm, volume=0.5, loop=True)
        except Exception:
            self.bgm        = None
            self.bgm_player = None

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

        with open(CAPA_JSON, 'r', encoding='utf-8') as f:
            self.db_capas = json.load(f)

        if self._save_data_init is not None:
            self.data_full = self._save_data_init
        else:
            with open(DRESSEUR_JSON, 'r', encoding='utf-8') as f:
                self.data_full = json.load(f)

        self.stage    = self.data_full.get("stage", 1)
        self.equipe   = [Pokemon(p, self.db_capas, self.poke_data_map)
                         for p in self.data_full.get("equipe", [])]
        self.active_p = self.equipe[0]

        self.inventaire = []
        inv = self.data_full.get("inventaire", {})
        for cat in inv:
            for n, q in inv[cat].items():
                if q > 0:
                    self.inventaire.append({"nom": n, "qty": q, "cat": cat})

    def sauvegarder_donnees(self):
        self.data_full["equipe"]    = [p.to_dict() for p in self.equipe]
        self.data_full["stage"]     = self.stage
        self.data_full["slot_num"]  = self.slot_num
        new_inv = {"potions": {}, "balls": {}}
        for it in self.inventaire:
            cat = it["cat"]
            if cat not in new_inv:
                new_inv[cat] = {}
            new_inv[cat][it["nom"]] = it["qty"]
        self.data_full["inventaire"] = new_inv

        # Sauvegarde slot
        os.makedirs(SAVES_PATH, exist_ok=True)
        with open(os.path.join(SAVES_PATH, f"slot_{self.slot_num}.json"),
                  'w', encoding='utf-8') as f:
            json.dump(self.data_full, f, indent=4, ensure_ascii=False)
        # Sync DRESSEUR_JSON
        with open(DRESSEUR_JSON, 'w', encoding='utf-8') as f:
            json.dump(self.data_full, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Niveau cohérent par stage
    # ------------------------------------------------------------------

    def _niveau_range_pour_stage(self) -> tuple:
        """Retourne (niv_min, niv_max) cohérent avec le stage actuel.
        Stage 1 → (2,3), Stage 99 → (95,96).
        """
        base = max(2, min(95, int(2 + (self.stage - 1) * (95 / 98))))
        return base, base + 1

    # ------------------------------------------------------------------
    # Sprites & textures
    # ------------------------------------------------------------------

    def charger_sprites(self):
        if self.ennemi:
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

    def _get_background(self, type_principal: str = "normal"):
        """Retourne la texture de fond selon le type du Pokémon ennemi."""
        type_norm = normaliser(type_principal).lower()
        filename  = TYPE_BACKGROUNDS.get(type_norm, BG_DEFAUT)
        return self._get_background_fichier(filename)

    def _get_background_fichier(self, filename: str):
        """Charge une texture de fond par nom de fichier (avec cache)."""
        if filename in self._bg_cache:
            return self._bg_cache[filename]
        path = os.path.join(_FONT_PATH, filename)
        if os.path.exists(path):
            try:
                tex = arcade.load_texture(path)
                self._bg_cache[filename] = tex
                return tex
            except Exception as e:
                print(f"[WARN] background {filename}: {e}")
        return None

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
    # Génération d'ennemis cohérents par niveau
    # ------------------------------------------------------------------

    def _seuil_evolution(self, nom_fr: str) -> int:
        """Niveau minimal pour obtenir ce Pokemon par évolution."""
        nom_norm = normaliser(nom_fr)
        for base, evo_data in self.evolution_config.items():
            options = evo_data if isinstance(evo_data, list) else [evo_data]
            for opt in options:
                if (normaliser(opt.get("cible", "")) == nom_norm
                        and opt.get("methode") == "level"):
                    return opt["valeur"]
        return None

    def generer_ennemi_aleatoire(self):
        """Génère un ennemi cohérent avec le stage actuel."""
        niv_min, niv_max = self._niveau_range_pour_stage()
        lvl = random.randint(niv_min, niv_max)

        # Liste des Pokémon disponibles via sprites + filtrés par niveau
        possibles_noms = []
        for root, _, files in os.walk(SPRITE_PATH):
            for f in files:
                if "_face" in f.lower() and "shiny" not in f.lower():
                    nom_net = f.split("_face")[0].replace("_", " ")
                    if nom_net not in possibles_noms:
                        possibles_noms.append(nom_net)

        # Filtrer les formes évoluées trop puissantes pour le niveau
        possibles_filtres = []
        for nom in possibles_noms:
            seuil = self._seuil_evolution(nom)
            if seuil is None or lvl >= seuil:
                possibles_filtres.append(nom)

        if not possibles_filtres:
            possibles_filtres = possibles_noms

        nom_choisi = random.choice(possibles_filtres)

        # Types depuis poke_data_map
        types_ennemi = ["Normal"]
        for k, v in self.poke_data_map.items():
            if normaliser(k) == normaliser(nom_choisi):
                types_ennemi = v.get("types", ["Normal"])
                break

        # Attaques cohérentes
        moves_stab = [
            m for m in self.db_capas
            if any(normaliser(m.get("type", "")) in [normaliser(t), t.lower()]
                   for t in types_ennemi)
            and m.get("puissance")
        ]
        moves_autres = [m for m in self.db_capas
                        if m not in moves_stab and m.get("puissance")]
        moves_statut = [m for m in self.db_capas
                        if not m.get("puissance") or m.get("categorie") == "Statut"]

        pool_stab   = random.sample(moves_stab,   min(2, len(moves_stab)))
        pool_autres = random.sample(moves_autres,  min(1, len(moves_autres)))
        pool_statut = random.sample(moves_statut,  min(1, len(moves_statut)))
        moves_pool  = pool_stab + pool_autres + pool_statut
        if len(moves_pool) < 4:
            reste = [m for m in self.db_capas if m not in moves_pool]
            moves_pool += random.sample(reste, min(4 - len(moves_pool), len(reste)))
        moves_pool = moves_pool[:4]

        nature_choisie = random.choice(list(NatureEngine.DATA.keys()))

        stats_base = {"attaque": 40+lvl, "defense": 40+lvl, "vitesse": 40+lvl,
                      "attaque_spe": 40+lvl, "defense_spe": 40+lvl}
        for k, v in self.poke_data_map.items():
            if normaliser(k) == normaliser(nom_choisi):
                raw = v.get("stats", {})
                stats_base = {
                    "attaque":     max(1, int(((2 * raw.get("attaque", 50)) * lvl / 100) + 5)),
                    "defense":     max(1, int(((2 * raw.get("defense", 50)) * lvl / 100) + 5)),
                    "vitesse":     max(1, int(((2 * raw.get("vitesse", 50)) * lvl / 100) + 5)),
                    "attaque_spe": max(1, int(((2 * raw.get("attaque_spe", 50)) * lvl / 100) + 5)),
                    "defense_spe": max(1, int(((2 * raw.get("defense_spe", 50)) * lvl / 100) + 5)),
                }
                break

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
        self.tour_num  = 1
        self.est_dresseur   = False
        self.dresseur_actif = None
        PokedexManager.enregistrer(self.ennemi, capture=False)
        # Mettre à jour le background selon le type du nouvel ennemi
        type_principal = types_ennemi[0] if types_ennemi else "normal"
        self._bg_actuel = self._get_background(type_principal)

    def demarrer_combat_dresseur(self):
        """Initialise un DresseurIA et passe en phase DIALOGUE du dresseur."""
        d = DresseurIA(self.stage, self.poke_data_map, self.db_capas, self.evolution_config)
        self.dresseur_actif = d
        self.est_dresseur   = True
        self.tour_num       = 1
        # L'ennemi n'est PAS encore visible : on attend la fin du dialogue
        self.ennemi = None
        self.etat   = "DRESSEUR_DIALOGUE"

    # ------------------------------------------------------------------
    # Inter-stage : menu Combattre / Boutique
    # ------------------------------------------------------------------

    def afficher_inter_stage(self):
        self.etat      = "INTER_STAGE"
        self.index_sel = 0

    def demarrer_combat_boss(self):
        """Lance le combat du boss (stage 100)."""
        from core.boss import BossIA
        b = BossIA(self.poke_data_map, self.db_capas)
        self.boss_actif    = b
        self.dresseur_actif = b          # réutilise la même interface dialogue
        self.est_dresseur  = True
        self.est_boss      = True
        self.tour_num      = 1
        self.ennemi        = None
        # Charger la musique boss
        try:
            if self.bgm_player:
                arcade.stop_sound(self.bgm_player)
            if os.path.exists(BOSS_MUSIC_PATH):
                self.bgm        = arcade.load_sound(BOSS_MUSIC_PATH)
                self.bgm_player = arcade.play_sound(self.bgm, volume=0.6, loop=True)
        except Exception as e:
            print(f"[WARN] musique boss: {e}")
        # Background arène pour le boss
        self._bg_actuel = self._get_background_fichier(BG_ARENE)
        self.etat = "DRESSEUR_DIALOGUE"

    def entrer_en_combat(self):
        """Stage 100 → boss. Sinon décide sauvage ou dresseur."""
        if self.stage >= 100:
            self.demarrer_combat_boss()
            return
        if DresseurIA.doit_apparaitre():
            self.demarrer_combat_dresseur()
        else:
            self.generer_ennemi_aleatoire()
            self.charger_sprites()
            self.etat = "PRINCIPAL"

    # ------------------------------------------------------------------
    # Boutique
    # ------------------------------------------------------------------

    def _get_item_inventaire(self, nom: str):
        for it in self.inventaire:
            if it["nom"] == nom:
                return it
        return None

    def acheter_item(self, item: dict) -> tuple:
        """Achète un item. Retourne (succes, message)."""
        prix  = item["prix"]
        solde = self.data_full.get("argent", 0)
        if solde < prix:
            return False, f"Pas assez d'argent ! ({solde}P / {prix}P)"
        ok, nouveau_solde = MonnaieEngine.debiter(self.data_full, prix)
        if ok:
            existing = self._get_item_inventaire(item["nom"])
            if existing:
                existing["qty"] += 1
            else:
                self.inventaire.append({"nom": item["nom"], "qty": 1, "cat": item["cat"]})
            self.sauvegarder_donnees()
            return True, f"Achete {item['nom']} ! Solde : {nouveau_solde}P"
        return False, "Erreur lors de l'achat."

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
        old_nom          = self.active_p.nom
        is_shiny         = "shiny" in old_nom.lower()
        base_target_norm = normaliser(self.evo_target_name.replace("Shiny","").replace("shiny",""))
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
        self.message = f"Felicitations ! {old_nom} a evolue en {self.active_p.nom} !"
        self.etat    = "MESSAGE_V"

    # ------------------------------------------------------------------
    # XP & Monnaie
    # ------------------------------------------------------------------

    def attribuer_xp(self):
        xp_gain = ExperienceEngine.calculer_xp_gagne(self.ennemi)
        logs    = self.active_p.gain_xp(xp_gain)

        # Gain monétaire via MonnaieEngine (POO)
        gain_argent = MonnaieEngine.calculer_gain(
            self.ennemi, est_dresseur=self.est_dresseur, stage=self.stage
        )
        MonnaieEngine.crediter(self.data_full, gain_argent)

        self.sauvegarder_donnees()
        log_txt      = "\n".join(logs)
        msg_argent   = MonnaieEngine.formater_message(gain_argent, self.est_dresseur)
        self.message = f"{self.ennemi.nom} est KO !\n+{xp_gain} XP.\n{msg_argent}\n{log_txt}"
        self.etat    = "MESSAGE_V"

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    def finaliser_capture(self):
        self.item_en_cours["qty"] -= 1
        if self.item_en_cours["qty"] <= 0 and self.item_en_cours in self.inventaire:
            self.inventaire.remove(self.item_en_cours)

        succes, msg_capture = CaptureEngine.tenter_capture(
            self.item_en_cours["nom"], self.ennemi, tour=self.tour_num
        )
        if succes:
            PokedexManager.enregistrer(self.ennemi, capture=True)
            if len(self.equipe) < 6:
                # Équipe pas pleine : ajout direct
                self.equipe.append(self.ennemi)
                self._avancer_stage_apres_capture(msg_capture)
            else:
                # Équipe pleine (6) : demander conserver ou libérer
                self._pokemon_capture_temp = self.ennemi
                self.message    = (f"{msg_capture}\n"
                                   f"Equipe pleine ! Garder {self.ennemi.nom} ?\n"
                                   f"ENTREE=Choisir un sacrifice   X=Liberer")
                self.index_sacrifice = 0
                self.etat = "CAPTURE_PLEIN"
        else:
            self.message = msg_capture
            self.etat    = "MESSAGE_J"

    def _avancer_stage_apres_capture(self, msg=""):
        """Passe au stage suivant après une capture réussie."""
        self.stage += 1
        self.data_full["stage"] = self.stage
        self.sauvegarder_donnees()
        self.message = (msg + f"\nSTAGE {self.stage} atteint !").strip()
        self.etat = "MESSAGE_STAGE"

    # ------------------------------------------------------------------
    # Fin de combat
    # ------------------------------------------------------------------

    def _fin_combat_victoire(self):
        """Appelé quand l'ennemi courant est vaincu. Gère suite dresseur/boss ou passage de stage."""
        if self.est_dresseur and self.dresseur_actif:
            # Vérifie si le dresseur a encore des Pokémon
            if self.dresseur_actif.est_vaincu:
                if self.est_boss:
                    # VICTOIRE BOSS → déclencher le dialogue de victoire
                    self.boss_victoire = True
                    self.boss_actif.phrase = (
                        "ca dit quoi l'equipe ? Bravo c'est bien, gg, tu as fini ce jeu.\n"
                        "voici ton ecran de victoire."
                    )
                    self.boss_actif._lignes_cache = None
                    self.boss_actif.dialogue_page = 0
                    self.boss_actif.anim_phase    = "DIALOGUE"
                    self.boss_actif.sprite_x      = 400
                    self.dresseur_actif            = self.boss_actif
                    self.ennemi                    = None
                    self.etat = "VICTOIRE_BOSS_DIALOGUE"
                    return
                # Gain total dresseur normal
                gain = MonnaieEngine.calculer_gain_dresseur(
                    self.dresseur_actif.equipe, self.stage
                )
                MonnaieEngine.crediter(self.data_full, gain)
                self.stage += 1
                self.data_full["stage"] = self.stage
                self.sauvegarder_donnees()
                self.message += f"\n{self.dresseur_actif.label} est vaincu !\n+{gain}P\nSTAGE {self.stage} atteint !"
                self.dresseur_actif = None
                self.est_dresseur   = False
                self.est_boss       = False
                self.etat = "MESSAGE_STAGE"
            else:
                # Le dresseur change de Pokémon
                self.dresseur_actif.changer_pokemon()
                self.ennemi = self.dresseur_actif.pokemon_actif
                PokedexManager.enregistrer(self.ennemi, capture=False)
                self.charger_sprites()
                type_p = self.ennemi.types[0] if self.ennemi.types else "normal"
                self._bg_actuel = self._get_background(type_p)
        else:
            # Combat sauvage victorieux → prochain stage
            self.stage += 1
            self.data_full["stage"] = self.stage
            self.sauvegarder_donnees()

    # ------------------------------------------------------------------
    # Game Over
    # ------------------------------------------------------------------

    def _game_over_retour_menu(self):
        """Supprime la save du slot courant et retourne au menu principal."""
        # Arrêter la musique
        try:
            if self.bgm_player:
                arcade.stop_sound(self.bgm_player)
        except Exception:
            pass

        # Supprimer la sauvegarde du slot
        try:
            slot_path = os.path.join(SAVES_PATH, f"slot_{self.slot_num}.json")
            if os.path.exists(slot_path):
                os.remove(slot_path)
                print(f"[INFO] Save slot {self.slot_num} supprimée.")
        except Exception as e:
            print(f"[WARN] Suppression save : {e}")

        # Supprimer dresseur_config.json pour repartir proprement
        try:
            if os.path.exists(DRESSEUR_JSON):
                os.remove(DRESSEUR_JSON)
        except Exception:
            pass

        # Relancer le menu principal
        try:
            import main as main_module
            self.close()
            win = main_module.MainMenuView  # type: ignore
            # On recrée la fenêtre principale
            main_module.main()
        except Exception as e:
            print(f"[WARN] Retour menu : {e}")
            self.close()

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
        elif self.etat == "DRESSEUR_GLISSEMENT":
            # Animation : le dresseur glisse vers la droite et disparaît
            if self.dresseur_actif:
                sorti = self.dresseur_actif.update_glissement()
                if sorti:
                    # Glissement terminé → afficher le 1er Pokemon
                    self.ennemi = self.dresseur_actif.pokemon_actif
                    PokedexManager.enregistrer(self.ennemi, capture=False)
                    self.charger_sprites()
                    # Background arène pour tous les combats dresseur/boss
                    self._bg_actuel = self._get_background_fichier(BG_ARENE)
                    self.etat = "PRINCIPAL"

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def on_draw(self):
        self.clear()

        # === GAME OVER ===
        if self.etat == "GAME_OVER":
            arcade.draw_rect_filled(arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                                    (15, 5, 5))
            arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40,
                             arcade.color.RED, 48, anchor_x="center", bold=True)
            arcade.draw_text("Votre aventure s'arrete ici...",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 10,
                             (200, 80, 80), 18, anchor_x="center")
            arcade.draw_text("[ ENTREE ] Retour au menu  (sauvegarde supprimee)",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60,
                             arcade.color.GRAY, 14, anchor_x="center")
            return

        # === INTER-STAGE : menu Combattre / Boutique / Pokédex ===
        if self.etat in ("INTER_STAGE", "BOUTIQUE", "POKEDEX"):
            self._draw_inter_stage()
            return

        # === DIALOGUE DRESSEUR/BOSS (avant le combat ou victoire) ===
        if self.etat in ("DRESSEUR_DIALOGUE", "DRESSEUR_GLISSEMENT",
                         "VICTOIRE_BOSS_DIALOGUE"):
            self._draw_dresseur_pre_combat()
            return

        # === VICTOIRE BOSS (attente espace) ===
        if self.etat == "VICTOIRE_BOSS":
            self._draw_victoire_boss()
            return

        # === ÉCRAN FINAL (wing.png + congratulations) ===
        if self.etat == "ECRAN_FIN":
            self._draw_ecran_fin()
            return

        # === ÉCRAN DE COMBAT ===
        # Background selon le type du pokemon ennemi
        if self._bg_actuel:
            arcade.draw_texture_rect(
                self._bg_actuel,
                arcade.rect.LBWH(0, 200, SCREEN_WIDTH, SCREEN_HEIGHT - 200)
            )

        # Badge stage en haut à gauche
        self._draw_stage_badge()

        if self.etat == "ANIM_EVO":
            tex = self.tex_evo_old if self.evo_flash else self.tex_evo_new
            arcade.draw_texture_rect(tex, arcade.rect.LBWH(100, 200, 250, 250))
        else:
            if self.active_p.hp > 0 and self.tex_joueur:
                arcade.draw_texture_rect(self.tex_joueur, arcade.rect.LBWH(100, 200, 250, 250))
            if self.tex_ennemi:
                arcade.draw_texture_rect(self.tex_ennemi, arcade.rect.LBWH(450, 320, 250, 250))

        # Indicateur dresseur
        if self.est_dresseur and self.dresseur_actif:
            arcade.draw_text(f"DRESSEUR : {self.dresseur_actif.label}",
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20,
                             arcade.color.GOLD, 14, anchor_x="center", bold=True)
            soins_txt = f"Soins restants : {self.dresseur_actif.soins_restants}"
            arcade.draw_text(soins_txt, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20,
                             arcade.color.ORANGE, 12, anchor_x="right")

        if self.ball_active and self.tex_ball_anim:
            arcade.draw_texture_rect(
                self.tex_ball_anim,
                arcade.rect.XYWH(self.ball_x, self.ball_y, 45, 45),
                angle=self.ball_angle,
            )

        # Panneau bas
        arcade.draw_rect_filled(arcade.rect.LBWH(0, 0, 800, 200), arcade.color.WHITE)
        arcade.draw_rect_outline(arcade.rect.LBWH(0, 0, 800, 200), arcade.color.BLACK, 5)

        if self.active_p and self.ennemi:
            self.draw_status_bar(50, 500, self.active_p, show_xp=True)
            self.draw_status_bar(450, 500, self.ennemi, show_xp=False)

        # Argent en bas à droite
        arcade.draw_text(f"{self.data_full.get('argent', 0)}P",
                         SCREEN_WIDTH - 15, 10, arcade.color.DARK_GREEN,
                         14, anchor_x="right", bold=True)

        if self.show_boosts:
            self.draw_boost_overlay()
        else:
            self.render_menu()

    def _draw_stage_badge(self):
        """Affiche le numéro de stage en haut à gauche."""
        arcade.draw_rect_filled(arcade.rect.LBWH(5, SCREEN_HEIGHT - 42, 130, 36),
                                (20, 20, 60, 210))
        arcade.draw_rect_outline(arcade.rect.LBWH(5, SCREEN_HEIGHT - 42, 130, 36),
                                 arcade.color.GOLD, 2)
        arcade.draw_text(f"STAGE  {self.stage}",
                         70, SCREEN_HEIGHT - 30,
                         arcade.color.GOLD, 16,
                         anchor_x="center", anchor_y="center", bold=True)

    def _draw_dresseur_pre_combat(self):
        """Affiche le dresseur + son dialogue, puis l'animation de sortie."""
        # Fond sobre
        arcade.draw_rect_filled(
            arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (200, 220, 255)
        )
        # Badge stage
        self._draw_stage_badge()
        # Délègue le dessin du sprite + boite de dialogue au DresseurIA
        if self.dresseur_actif:
            self.dresseur_actif.draw(SCREEN_WIDTH, SCREEN_HEIGHT)

    def _draw_victoire_boss(self):
        """Écran intermédiaire après la victoire boss (avant wing.png)."""
        arcade.draw_rect_filled(arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (5, 20, 5))
        arcade.draw_text("VICTOIRE !",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80,
                         (80, 255, 80), 52, anchor_x="center", bold=True)
        arcade.draw_text("Tu as battu le Boss !",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20,
                         arcade.color.GOLD, 22, anchor_x="center")
        arcade.draw_text("[ ESPACE ] Voir l'ecran de fin",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                         arcade.color.LIGHT_GRAY, 16, anchor_x="center")

    def _draw_ecran_fin(self):
        """Écran final : wing.png + CONGRATULATIONS."""
        # Charger wing.png (dans asset/fonts/ comme les backgrounds)
        if not hasattr(self, '_tex_wing') or self._tex_wing is None:
            wing_path = os.path.join(_FONT_PATH, "wing.png")
            try:
                if os.path.exists(wing_path):
                    self._tex_wing = arcade.load_texture(wing_path)
                else:
                    self._tex_wing = False
            except Exception:
                self._tex_wing = False

        if self._tex_wing:
            arcade.draw_texture_rect(
                self._tex_wing,
                arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        else:
            arcade.draw_rect_filled(
                arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (10, 10, 40)
            )

        # Texte CONGRATULATIONS avec effet
        arcade.draw_text("CONGRATULATIONS !",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30,
                         arcade.color.GOLD, 42, anchor_x="center", bold=True)
        arcade.draw_text("Vous avez complete Poke Fantasy !",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30,
                         arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[ ESPACE ] Quitter",
                         SCREEN_WIDTH // 2, 40,
                         arcade.color.LIGHT_GRAY, 14, anchor_x="center")

    def _draw_inter_stage(self):
        """Affiche le menu entre chaque stage (Combattre / Boutique)."""
        # Fond
        arcade.draw_rect_filled(
            arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (15, 15, 40)
        )

        # Titre stage
        arcade.draw_text(f"— STAGE  {self.stage} —",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
                         arcade.color.GOLD, 36, anchor_x="center", bold=True)

        nom_dresseur = self.data_full.get("nom_dresseur", "Dresseur")
        arcade.draw_text(f"Dresseur : {nom_dresseur}",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 130,
                         arcade.color.LIGHT_GRAY, 18, anchor_x="center")

        # Argent
        arcade.draw_text(f"Argent : {self.data_full.get('argent', 0)}P",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 165,
                         arcade.color.YELLOW, 16, anchor_x="center")

        if self.etat == "INTER_STAGE":
            # Menu principal inter-stage : 3 boutons
            options = [
                ("COMBATTRE", (60, 60, 120)),
                ("BOUTIQUE",  (60, 100, 60)),
                ("POKEDEX",   (80, 50, 100)),
            ]
            total_h = len(options) * 80
            start_y = SCREEN_HEIGHT // 2 + total_h // 2 - 30
            for i, (opt, base_col) in enumerate(options):
                y      = start_y - i * 80
                is_sel = (i == self.index_sel)
                r, g, b = base_col
                bg_col = (min(255, r+40), min(255, g+40), min(255, b+40), 220) if is_sel else (*base_col, 160)
                arcade.draw_rect_filled(arcade.rect.XYWH(SCREEN_WIDTH // 2, y, 320, 58), bg_col)
                arcade.draw_rect_outline(arcade.rect.XYWH(SCREEN_WIDTH // 2, y, 320, 58),
                                         arcade.color.GOLD if is_sel else arcade.color.GRAY, 2)
                col = arcade.color.GOLD if is_sel else arcade.color.WHITE
                arcade.draw_text(opt, SCREEN_WIDTH // 2, y, col, 22,
                                 anchor_x="center", anchor_y="center", bold=is_sel)
            arcade.draw_text("Haut/Bas : naviguer   Entree : valider",
                             SCREEN_WIDTH // 2, 30, arcade.color.GRAY, 13,
                             anchor_x="center")

        elif self.etat == "BOUTIQUE":
            self._draw_boutique()

        elif self.etat == "POKEDEX":
            self._draw_pokedex()

    def _draw_boutique(self):
        """Affiche la boutique inter-stage."""
        arcade.draw_text("— BOUTIQUE —",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200,
                         arcade.color.CYAN, 22, anchor_x="center", bold=True)

        solde = self.data_full.get("argent", 0)
        arcade.draw_text(f"Votre argent : {solde}P",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 235,
                         arcade.color.YELLOW, 15, anchor_x="center")

        cols   = 2
        start_x, start_y = 120, SCREEN_HEIGHT - 280
        espacement_x, espacement_y = 320, 52

        for i, item in enumerate(BOUTIQUE_CATALOGUE):
            col = i % cols
            row = i // cols
            x   = start_x + col * espacement_x
            y   = start_y - row * espacement_y
            is_sel = (i == self.index_sel)

            bg = (60, 80, 60, 200) if is_sel else (30, 30, 50, 180)
            arcade.draw_rect_filled(arcade.rect.LBWH(x - 10, y - 6, 295, 40), bg)
            if is_sel:
                arcade.draw_rect_outline(arcade.rect.LBWH(x - 10, y - 6, 295, 40),
                                         arcade.color.GOLD, 2)

            col_txt = arcade.color.GOLD if is_sel else arcade.color.WHITE
            arcade.draw_text(f"{item['nom']}", x, y + 14, col_txt, 13, bold=is_sel)
            arcade.draw_text(f"{item['prix']}P  {item['desc']}",
                             x, y - 2, arcade.color.LIGHT_GRAY, 11)

        arcade.draw_text("Haut/Bas/Gauche/Droit : naviguer   Entree : acheter   X : retour",
                         SCREEN_WIDTH // 2, 30, arcade.color.GRAY, 12,
                         anchor_x="center")

        # Message d'achat si présent
        if self.message:
            arcade.draw_text(self.message,
                             SCREEN_WIDTH // 2, 70,
                             arcade.color.LIGHT_GREEN, 14, anchor_x="center")

    def _draw_pokedex(self):
        """Affiche le Pokédex (Pokémon capturés) depuis le JSON pokedex.
        Structure JSON : {"pokemon_rencontres": [{nom, possede, vu, hp_base, ...}, ...]}
        """
        from core.config import POKEDEX_JSON as _PDX_PATH
        entrees = []
        if os.path.exists(_PDX_PATH):
            try:
                with open(_PDX_PATH, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                # Gestion des deux structures possibles
                if isinstance(raw, dict):
                    entrees = raw.get("pokemon_rencontres", [])
                elif isinstance(raw, list):
                    entrees = raw
            except Exception as e:
                print(f"[WARN] pokedex: {e}")

        # Filtrer uniquement les capturés (possede=True)
        captures = [e for e in entrees if isinstance(e, dict) and e.get("possede", False)]
        captures.sort(key=lambda x: x.get("nom", ""))

        # --- Fond ---
        arcade.draw_rect_filled(
            arcade.rect.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (10, 10, 30)
        )

        # Titre
        arcade.draw_text("— POKEDEX —",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60,
                         (180, 80, 220), 26, anchor_x="center", bold=True)
        arcade.draw_text(f"{len(captures)} Pokemon capture(s)",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 95,
                         arcade.color.LIGHT_GRAY, 14, anchor_x="center")

        if not captures:
            arcade.draw_text("Aucun Pokemon capture pour l'instant !",
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                             arcade.color.GRAY, 16, anchor_x="center")
        else:
            # Pagination : 12 par page (grille 3 colonnes x 4 lignes)
            par_page = 12
            nb_pages = max(1, (len(captures) + par_page - 1) // par_page)
            page     = max(0, min(self.pokedex_page, nb_pages - 1))
            self.pokedex_page = page  # reclamper
            debut     = page * par_page
            page_data = captures[debut: debut + par_page]

            cols   = 3
            cell_w = 245
            cell_h = 50
            start_x = (SCREEN_WIDTH - cols * cell_w) // 2 + cell_w // 2
            start_y = SCREEN_HEIGHT - 130

            for idx, entree in enumerate(page_data):
                c   = idx % cols
                row = idx // cols
                cx  = start_x + c * cell_w
                cy  = start_y - row * cell_h

                possede = entree.get("possede", False)
                nom     = entree.get("nom", "???")

                bg = (40, 20, 60, 200) if possede else (20, 20, 40, 150)
                bd = (140, 80, 200) if possede else (60, 60, 80)
                arcade.draw_rect_filled(arcade.rect.XYWH(cx, cy, cell_w - 6, cell_h - 4), bg)
                arcade.draw_rect_outline(arcade.rect.XYWH(cx, cy, cell_w - 6, cell_h - 4), bd, 1)

                col_nom = arcade.color.WHITE if possede else (100, 100, 100)
                atk     = entree.get("attaque", "-")
                def_    = entree.get("defense", "-")
                arcade.draw_text(f"{nom[:20]}",
                                 cx - cell_w // 2 + 8, cy + 8,
                                 col_nom, 12, bold=possede)
                arcade.draw_text(f"ATK:{atk}  DEF:{def_}",
                                 cx - cell_w // 2 + 8, cy - 8,
                                 arcade.color.LIGHT_GRAY, 10)

            arcade.draw_text(f"Page {page + 1} / {nb_pages}",
                             SCREEN_WIDTH // 2, 55,
                             arcade.color.GRAY, 13, anchor_x="center")

        arcade.draw_text("Gauche/Droite : changer page   X : retour",
                         SCREEN_WIDTH // 2, 30, arcade.color.GRAY, 12,
                         anchor_x="center")

    # ------------------------------------------------------------------
    # UI Combat
    # ------------------------------------------------------------------

    def draw_status_bar(self, x, y, p, show_xp=False):
        BARRE_WIDTH = 150
        arcade.draw_text(f"{p.nom} Lv.{p.niveau}", x, y + 35,
                         arcade.color.BLACK, 14, bold=True)
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
            arcade.draw_rect_filled(arcade.rect.XYWH(x + BARRE_WIDTH + 25, y + 10, 30, 15),
                                    (40, 40, 40))
            arcade.draw_text(s["label"], x + BARRE_WIDTH + 25, y + 10,
                             s["color"], 9, bold=True, anchor_x="center", anchor_y="center")
        if show_xp:
            arcade.draw_rect_filled(arcade.rect.LBWH(x, y - 25, BARRE_WIDTH, 6),
                                    arcade.color.DARK_GRAY)
            xp_ratio = max(0, min(1.0, p.xp / p.xp_max))
            arcade.draw_rect_filled(arcade.rect.LBWH(x, y - 25, BARRE_WIDTH * xp_ratio, 6),
                                    arcade.color.SKY_BLUE)
            arcade.draw_rect_outline(arcade.rect.LBWH(x, y - 25, BARRE_WIDTH, 6),
                                     arcade.color.BLACK, 1)

    def draw_boost_overlay(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(400, 300, 780, 280), (20, 20, 20, 230))
        arcade.draw_rect_outline(arcade.rect.XYWH(400, 300, 780, 280), arcade.color.GOLD, 2)
        arcade.draw_text("[ V ] Fermer", 400, 425, arcade.color.GOLD, 11, anchor_x="center")
        arcade.draw_text(f">> {self.active_p.nom} — Nature: {self.active_p.nature}",
                         120, 400, arcade.color.CYAN, 12, bold=True, anchor_x="center")
        y_j = 378
        for stat, val in self.active_p.stages.items():
            color  = (arcade.color.LIGHT_GREEN if val > 0
                      else arcade.color.RED if val < 0
                      else arcade.color.LIGHT_GRAY)
            fleche = "^" * abs(val) if val > 0 else "v" * abs(val) if val < 0 else "-"
            arcade.draw_text(f"{stat.replace('_',' ').capitalize():<14} {fleche:>6}",
                             60, y_j, color, 11)
            y_j -= 22
        arcade.draw_line(400, 175, 400, 425, arcade.color.GRAY, 1)
        arcade.draw_text(f">> {self.ennemi.nom} — Nature: {self.ennemi.nature}",
                         590, 400, arcade.color.ORANGE, 12, bold=True, anchor_x="center")
        y_e = 378
        for stat, val in self.ennemi.stages.items():
            color  = (arcade.color.LIGHT_GREEN if val > 0
                      else arcade.color.RED if val < 0
                      else arcade.color.LIGHT_GRAY)
            fleche = "^" * abs(val) if val > 0 else "v" * abs(val) if val < 0 else "-"
            arcade.draw_text(f"{stat.replace('_',' ').capitalize():<14} {fleche:>6}",
                             440, y_e, color, 11)
            y_e -= 22

    def draw_selector(self, x, y, width=180, height=40):
        arcade.draw_rect_outline(arcade.rect.LBWH(x - 10, y - 5, width, height),
                                 arcade.color.RED, 3)

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
                arcade.draw_text(m["nom_attaque"].upper(), tx + 60, ty,
                                 arcade.color.BLACK, 18)

        elif self.etat in ["EQUIPE", "CHOIX_SOIN"]:
            for i, p in enumerate(self.equipe):
                tx, ty = 80 + (i % 2) * 400, 140 - (i // 2) * 60
                if i == self.index_sel:
                    self.draw_selector(tx, ty, 350, 35)
                arcade.draw_text(f"{p.nom} {int(p.hp)}/{p.hp_base}",
                                 tx, ty, arcade.color.BLACK, 14)

        elif self.etat == "SAC":
            visible = self.inventaire[self.index_sel // 4 * 4: self.index_sel // 4 * 4 + 4]
            for i, it in enumerate(visible):
                tx, ty = 100 + (i % 2) * 400, 140 - (i // 2) * 60
                if i == self.index_sel % 4:
                    self.draw_selector(tx, ty, 300, 35)
                arcade.draw_text(f"{it['nom']} x{it['qty']}", tx, ty,
                                 arcade.color.BLACK, 16)

        elif self.etat == "DEMANDE_EVO":
            arcade.draw_text(f"Quoi ? {self.active_p.nom} evolue !",
                             400, 140, arcade.color.BLACK, 20, anchor_x="center")
            arcade.draw_text("Appuyez sur Entree pour continuer",
                             400, 80, arcade.color.GRAY, 14, anchor_x="center")

        elif self.etat == "CAPTURE_PLEIN":
            # Affiche le choix : sacrifice ou libérer
            pk_cap = self._pokemon_capture_temp
            if pk_cap:
                arcade.draw_text(f"Garder {pk_cap.nom} ?",
                                 400, 170, (0, 180, 0), 16, anchor_x="center", bold=True)
            arcade.draw_text("Choisissez le Pokemon a sacrifier :",
                             400, 148, arcade.color.BLACK, 13, anchor_x="center")
            for i, p in enumerate(self.equipe):
                tx = 60 + (i % 3) * 240
                ty = 115 - (i // 3) * 50
                is_sel = (i == self.index_sacrifice)
                if is_sel:
                    self.draw_selector(tx - 5, ty - 5, 215, 42)
                col = arcade.color.RED if is_sel else arcade.color.BLACK
                arcade.draw_text(f"{p.nom} Lv.{p.niveau} {int(p.hp)}/{p.hp_base}",
                                 tx, ty, col, 12)
            arcade.draw_text("ENTREE : remplacer   X : liberer le capture",
                             400, 15, arcade.color.GRAY, 11, anchor_x="center")

        elif self.etat == "VICTOIRE_BOSS":
            pass  # géré dans on_draw principal

        elif self.etat.startswith("MESSAGE") or self.etat in ["ANIM_BALL", "ANIM_EVO"]:
            self.ui_text.text = self.message
            self.ui_text.draw()

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    def on_key_press(self, key, modifiers):
        # Boosts overlay
        if key == arcade.key.V and self.etat not in ("INTER_STAGE", "BOUTIQUE"):
            self.show_boosts = not self.show_boosts
            return
        if self.etat == "GAME_OVER":
            if key in (arcade.key.ENTER, arcade.key.SPACE):
                self._game_over_retour_menu()
            return
        if self.show_boosts or self.etat in ["ANIM_BALL", "ANIM_EVO"]:
            return

        # Espace/Entrée pendant le dialogue dresseur ou boss
        if self.etat in ("DRESSEUR_DIALOGUE", "VICTOIRE_BOSS_DIALOGUE"):
            if key in (arcade.key.SPACE, arcade.key.ENTER):
                if self.dresseur_actif:
                    fini = self.dresseur_actif.avancer_dialogue()
                    if fini:
                        if self.etat == "VICTOIRE_BOSS_DIALOGUE":
                            self.etat = "VICTOIRE_BOSS"
                        else:
                            self.etat = "DRESSEUR_GLISSEMENT"
            return

        # Retour / annulation
        if key == arcade.key.X:
            if self.etat in ("BOUTIQUE", "POKEDEX"):
                self.message      = ""
                self.etat         = "INTER_STAGE"
                self.index_sel    = 0
                self.pokedex_page = 0
                return
            if self.etat == "CHOIX_SOIN":
                self.etat = "SAC"
                return
            if not (self.etat == "EQUIPE" and self.active_p.hp <= 0):
                self.etat      = "PRINCIPAL"
                self.index_sel = 0
                return

        # Navigation Pokédex (pagination latérale)
        if self.etat == "POKEDEX":
            if key == arcade.key.LEFT:
                self.pokedex_page = max(0, self.pokedex_page - 1)
            elif key == arcade.key.RIGHT:
                self.pokedex_page += 1   # clampé dans _draw_pokedex
            return

        # Navigation CAPTURE_PLEIN (choix sacrifice)
        if self.etat == "CAPTURE_PLEIN":
            nb = len(self.equipe)
            if key in (arcade.key.RIGHT, arcade.key.DOWN):
                self.index_sacrifice = (self.index_sacrifice + 1) % nb
            elif key in (arcade.key.LEFT, arcade.key.UP):
                self.index_sacrifice = (self.index_sacrifice - 1) % nb
            elif key == arcade.key.ENTER or key == arcade.key.SPACE:
                # Remplacer le Pokemon sacrifié par le capturé
                pk_cap = self._pokemon_capture_temp
                ancien = self.equipe[self.index_sacrifice]
                self.equipe[self.index_sacrifice] = pk_cap
                # Si le sacrifié était le pokemon actif, basculer
                if self.active_p is ancien:
                    self.active_p = pk_cap
                self._pokemon_capture_temp = None
                self._avancer_stage_apres_capture(f"{ancien.nom} a ete libere ! {pk_cap.nom} rejoint l'equipe !")
            elif key == arcade.key.X:
                # Libérer le capturé (déjà enregistré au Pokédex, pas ajouté à l'équipe)
                pk_cap = self._pokemon_capture_temp
                self._pokemon_capture_temp = None
                self._avancer_stage_apres_capture(f"{pk_cap.nom} a ete libere dans la nature !")
            return

        # Victoire boss : espace → écran final wing.png
        if self.etat == "VICTOIRE_BOSS":
            if key in (arcade.key.SPACE, arcade.key.ENTER):
                self.etat = "ECRAN_FIN"
            return

        # Écran fin (wing.png) : espace pour fermer
        if self.etat == "ECRAN_FIN":
            if key in (arcade.key.SPACE, arcade.key.ENTER, arcade.key.ESCAPE):
                self.close()
            return

        # Navigation
        nb_max = 4
        if self.etat == "SAC":
            nb_max = max(1, len(self.inventaire))
        elif self.etat in ["EQUIPE", "CHOIX_SOIN"]:
            nb_max = max(1, len(self.equipe))
        elif self.etat == "BOUTIQUE":
            nb_max = len(BOUTIQUE_CATALOGUE)
        elif self.etat == "INTER_STAGE":
            nb_max = 3   # COMBATTRE, BOUTIQUE, POKEDEX

        if nb_max > 0:
            if self.etat == "INTER_STAGE":
                # Menu vertical à 3 options : toutes les flèches naviguent de 1
                if key in (arcade.key.UP, arcade.key.LEFT):
                    self.index_sel = (self.index_sel - 1) % nb_max
                elif key in (arcade.key.DOWN, arcade.key.RIGHT):
                    self.index_sel = (self.index_sel + 1) % nb_max
            else:
                # Navigation standard en grille 2 colonnes
                if key == arcade.key.RIGHT:
                    self.index_sel = (self.index_sel + 1) % nb_max
                elif key == arcade.key.LEFT:
                    self.index_sel = (self.index_sel - 1) % nb_max
                elif key == arcade.key.UP:
                    step = 2 if self.etat == "BOUTIQUE" else 2
                    self.index_sel = (self.index_sel - step) % nb_max
                elif key == arcade.key.DOWN:
                    step = 2 if self.etat == "BOUTIQUE" else 2
                    self.index_sel = (self.index_sel + step) % nb_max

        if key in [arcade.key.ENTER, arcade.key.SPACE]:
            self.valider_selection()

    def valider_selection(self):

        # --- Dialogue dresseur/boss (géré dans on_key_press, pas ici) ---
        if self.etat in ("DRESSEUR_DIALOGUE", "DRESSEUR_GLISSEMENT",
                         "VICTOIRE_BOSS_DIALOGUE", "VICTOIRE_BOSS", "ECRAN_FIN",
                         "CAPTURE_PLEIN"):
            return

        # --- Menu inter-stage ---
        if self.etat == "INTER_STAGE":
            if self.index_sel == 0:   # Combattre
                self.message = ""
                self.entrer_en_combat()
            elif self.index_sel == 1: # Boutique
                self.etat      = "BOUTIQUE"
                self.index_sel = 0
                self.message   = ""
            elif self.index_sel == 2: # Pokédex
                self.etat         = "POKEDEX"
                self.pokedex_page = 0
            return

        # --- Boutique ---
        if self.etat == "BOUTIQUE":
            item = BOUTIQUE_CATALOGUE[self.index_sel]
            ok, msg = self.acheter_item(item)
            self.message = msg
            return

        # --- Message passage de stage ---
        if self.etat == "MESSAGE_STAGE":
            self.afficher_inter_stage()
            return

        # --- Menu principal combat ---
        if self.etat == "PRINCIPAL":
            actions = {0: "ATTAQUE", 1: "SAC", 2: "EQUIPE"}
            if self.index_sel in actions:
                self.etat = actions[self.index_sel]
            elif self.index_sel == 3:
                # Fuite → inter-stage (sans avancer de stage)
                self.message = "Fuite reussie !"
                self.etat    = "MESSAGE_FUITE"
            self.index_sel = 0

        elif self.etat == "MESSAGE_FUITE":
            self.afficher_inter_stage()

        elif self.etat == "ATTAQUE":
            m = self.active_p.moves_obj[self.index_sel]
            msg_joueur = TurnManager.executer_attaque(self.active_p, self.ennemi, m)
            msg_eot_j  = TurnManager.appliquer_effets_fin_de_tour(self.active_p)
            self.message  = f"{msg_joueur}\n{msg_eot_j}".strip()
            self.tour_num = getattr(self, 'tour_num', 1) + 1
            self.etat     = "MESSAGE_J"

        elif self.etat == "SAC":
            if not self.inventaire:
                self.etat = "PRINCIPAL"
                return
            self.item_en_cours = self.inventaire[self.index_sel]
            if "ball" in self.item_en_cours["nom"].lower():
                if self.est_dresseur:
                    self.message   = "On ne peut pas capturer le Pokemon d'un dresseur !"
                    self.etat      = "MESSAGE_J"
                else:
                    self.tex_ball_anim = self._get_ball_tex(self.item_en_cours["nom"])
                    self.ball_x, self.ball_y, self.ball_active = 225, 325, True
                    self.etat    = "ANIM_BALL"
                    self.message = f"Lancement de {self.item_en_cours['nom']}..."
            else:
                self.etat      = "CHOIX_SOIN"
                self.index_sel = 0

        elif self.etat == "CHOIX_SOIN":
            ok, msg = ItemEngine.utiliser_objet(self.item_en_cours["nom"],
                                                 self.equipe[self.index_sel])
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
                self.attribuer_xp()
                self._fin_combat_victoire()
                # Si victoire finale, le message_V gérera la suite
            else:
                # Riposte (IA dresseur/boss ou sauvage)
                if self.est_dresseur and self.dresseur_actif:
                    action = self.dresseur_actif.choisir_action(self.active_p)
                    if action["type"] == "soin":
                        msg_ennemi = self.dresseur_actif.utiliser_soin()
                        msg_eot_e  = ""
                    elif action["type"] == "switch" and self.est_boss:
                        # Boss effectue un switch stratégique
                        nouveau = action["pokemon"]
                        msg_ennemi = self.boss_actif.effectuer_switch(nouveau)
                        self.ennemi = self.boss_actif.pokemon_actif
                        PokedexManager.enregistrer(self.ennemi, capture=False)
                        self.charger_sprites()
                        msg_eot_e = ""
                    else:
                        m_ennemi   = action["move"]
                        msg_ennemi = TurnManager.executer_attaque(self.ennemi, self.active_p, m_ennemi)
                        msg_eot_e  = TurnManager.appliquer_effets_fin_de_tour(self.ennemi)
                else:
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
                # Si l'ennemi est encore vivant (suite dresseur), on continue le combat
                if self.ennemi and self.ennemi.hp > 0:
                    self.etat = "PRINCIPAL"
                else:
                    # Combat terminé → inter-stage
                    self.etat      = "MESSAGE_STAGE"
                    if not self.message.endswith("!"):
                        self.message += f"\nSTAGE {self.stage} atteint !"
            self.index_sel = 0

        elif self.etat == "DEMANDE_EVO":
            self.lancer_evolution(self.evo_target_name)


# ---------------------------------------------------------------------------
# Utilitaires module
# ---------------------------------------------------------------------------

def niveau_pour_stage(stage: int) -> int:
    return max(2, min(95, int(2 + (max(1, stage) - 1) * (95 / 98))))


if __name__ == "__main__":
    game = PokeFantasyGame()
    arcade.run()
