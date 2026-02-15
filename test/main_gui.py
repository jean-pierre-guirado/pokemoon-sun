import arcade
import json
import os
import random
import sys
import unicodedata

# --- CONFIGURATION DES CHEMINS ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from core.table_type import TypeChart
    from core.nature import NatureEngine
    from core.combat import CombatEngine
    from core.exp import ExperienceEngine
    from core.level import LevelEngine
    print("✓ Modules core chargés avec succès !")
except ImportError as e:
    print(f"✗ Erreur d'importation : {e}")
    sys.exit()

DATA_PATH = os.path.join(ROOT_DIR, "data")
SPRITE_PATH = os.path.join(ROOT_DIR, "asset", "sprite")
TYPE_ICON_PATH = os.path.join(ROOT_DIR, "asset", "types")

def normaliser(nom):
    nom = str(nom).lower().strip()
    return "".join(c for c in unicodedata.normalize('NFD', nom) if unicodedata.category(c) != 'Mn')

class PokeFantasyGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Poke Fantasy - Version Finale")
        arcade.set_background_color(arcade.color.WHITE)
        
        # Chargement des bases de données
        with open(os.path.join(DATA_PATH, "pokemon_data.json"), 'r', encoding='utf-8') as f:
            self.pokedex = json.load(f)
        with open(os.path.join(DATA_PATH, "capacite_list.json"), 'r', encoding='utf-8') as f:
            self.all_moves = json.load(f)
            
        self.player_sprite_list = arcade.SpriteList()
        self.enemy_sprite_list = arcade.SpriteList()
        self.setup_combat()

    def piocher_moves(self, nom_pokemon):
        nom_cible = normaliser(nom_pokemon)
        pool = [m for m in self.all_moves if normaliser(m.get('pokemon', '')) == nom_cible]
        if not pool:
            pool = [{"nom_attaque": "Charge", "puissance": 40, "type": "Normal", "precision": 100}]
        return random.sample(pool, min(len(pool), 4))

    def calculer_stat_niveau(self, base, niveau, est_hp=False):
        if est_hp:
            return int(((base * 2) * niveau / 100) + niveau + 10)
        return int(((base * 2) * niveau / 100) + 5)

    def creer_entite_combat(self, nom):
        data = self.pokedex[nom]
        niveau = random.randint(15, 25) 
        stats_raw = data.get('stats', data)
        base_hp = stats_raw.get('hp') or stats_raw.get('pv') or 50
        
        hp_max = self.calculer_stat_niveau(base_hp, niveau, True)
        exp_actuelle = LevelEngine.exp_pour_niveau(niveau, "moyen")
        exp_suivante = LevelEngine.exp_pour_niveau(niveau + 1, "moyen")

        p = {
            "nom": nom,
            "types": data.get('types', ["Normal"]),
            "niveau": niveau,
            "stats_finales": {
                "attaque": self.calculer_stat_niveau(stats_raw.get('attaque', 50), niveau),
                "defense": self.calculer_stat_niveau(stats_raw.get('defense', 50), niveau)
            },
            "max_hp": hp_max,
            "pv_actuels": hp_max,
            "exp": exp_actuelle,
            "exp_max": exp_suivante,
            "exp_min": exp_actuelle, # Palier de base
            "capacites": self.piocher_moves(nom),
            "generation": str(data.get('generation', '1'))
        }
        return p

    def charger_sprite(self, nom, vue, x, y, scale):
        gen_initiale = str(self.pokedex[nom].get('generation', '1'))
        filename = f"{nom.capitalize()}_{vue}.png"
        
        # Test du chemin direct
        path = os.path.join(SPRITE_PATH, gen_initiale, filename)
        if os.path.exists(path):
            return arcade.Sprite(path, scale=scale, center_x=x, center_y=y)
            
        # Recherche récursive dans les autres dossiers de génération
        for g in range(1, 10):
            alt_path = os.path.join(SPRITE_PATH, str(g), filename)
            if os.path.exists(alt_path):
                return arcade.Sprite(alt_path, scale=scale, center_x=x, center_y=y)
        
        # Fallback si rien n'est trouvé
        print(f"⚠ Sprite introuvable : {filename}")
        return arcade.SpriteSolidColor(64, 64, arcade.color.GRAY, center_x=x, center_y=y)

    def setup_combat(self):
        self.player_sprite_list.clear()
        self.enemy_sprite_list.clear()
        
        n_j, n_a = random.sample(list(self.pokedex.keys()), 2)
        self.p1_data = self.creer_entite_combat(n_j)
        self.p2_data = self.creer_entite_combat(n_a)
        
        self.combat_logic = CombatEngine(self.p1_data, self.p2_data)
        
        self.sprite_joueur = self.charger_sprite(n_j, "dos", 220, 220, 2.8)
        self.sprite_ennemi = self.charger_sprite(n_a, "face", 580, 420, 2.2)
        
        self.player_sprite_list.append(self.sprite_joueur)
        self.enemy_sprite_list.append(self.sprite_ennemi)
        
        self.logs = [f"Un {n_a} sauvage apparaît !"]
        self.menu_ouvert = False
        self.tour_joueur = True
        self.fini = False

    def draw_ui(self, x, y, data, is_player=False):
        # UI Joueur au-dessus du sprite, UI Ennemi normale
        base_y = y + 160 if is_player else y
        
        # 1. Logo du Type
        try:
            t_name = data['types'][0].capitalize()
            if t_name == "Electrik": t_name = "Électrik"
            icon_path = os.path.join(TYPE_ICON_PATH, f"{t_name}.png")
            if os.path.exists(icon_path):
                icon = arcade.load_texture(icon_path)
                arcade.draw_texture_rectangle(x - 10, base_y + 30, 32, 14, icon)
        except: pass

        # 2. Nom et Niveau
        arcade.draw_text(f"{data['nom'].upper()}  Nv.{data['niveau']}", x + 20, base_y + 24, arcade.color.BLACK, 11, bold=True)
        
        # 3. Barre de PV
        arcade.draw_rect_filled(arcade.rect.XYWH(x + 100, base_y + 5, 200, 12), arcade.color.BLACK_OLIVE)
        ratio_pv = max(0, data['pv_actuels'] / data['max_hp'])
        col_pv = arcade.color.APPLE_GREEN if ratio_pv > 0.5 else (arcade.color.GOLD if ratio_pv > 0.2 else arcade.color.RED)
        if ratio_pv > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(x + (100 * ratio_pv), base_y + 5, 200 * ratio_pv, 8), col_pv)

        # 4. Barre d'EXP et PV texte (Joueur seulement)
        if is_player:
            arcade.draw_rect_filled(arcade.rect.XYWH(x + 100, base_y - 8, 200, 6), arcade.color.DARK_SLATE_GRAY)
            # Calcul ratio EXP
            exp_range = data['exp_max'] - data['exp_min']
            ratio_exp = min(1.0, (data['exp'] - data['exp_min']) / exp_range) if exp_range > 0 else 0
            
            arcade.draw_rect_filled(arcade.rect.XYWH(x + (100 * ratio_exp), base_y - 8, 200 * ratio_exp, 4), arcade.color.AZURE)
            arcade.draw_text(f"{int(data['pv_actuels'])}/{data['max_hp']} PV", x + 130, base_y - 25, arcade.color.BLACK, 9)

    def draw_attack_menu(self):
        for i, atk in enumerate(self.p1_data['capacites']):
            px, py = (140 + (i % 2) * 350), (100 - (i // 2) * 45)
            # Logo type attaque
            try:
                t_atk = atk.get('type', 'Normal').capitalize()
                if t_atk == "Electrik": t_atk = "Électrik"
                icon_path = os.path.join(TYPE_ICON_PATH, f"{t_atk}.png")
                if os.path.exists(icon_path):
                    tex = arcade.load_texture(icon_path)
                    arcade.draw_texture_rectangle(px - 45, py + 8, 32, 14, tex)
            except: pass
            arcade.draw_text(atk['nom_attaque'].upper(), px, py, arcade.color.BLACK, 13, bold=True)

    def on_draw(self):
        self.clear()
        self.player_sprite_list.draw()
        self.enemy_sprite_list.draw()

        self.draw_ui(480, 500, self.p2_data, is_player=False)
        self.draw_ui(120, 200, self.p1_data, is_player=True)

        # Boite de dialogue
        arcade.draw_rect_filled(arcade.rect.XYWH(400, 80, 750, 130), arcade.color.WHITE_SMOKE)
        arcade.draw_rect_outline(arcade.rect.XYWH(400, 80, 750, 130), arcade.color.BLACK, 3)
        
        if self.fini:
            arcade.draw_text(self.logs[-1], 400, 90, arcade.color.DARK_RED, 16, anchor_x="center", bold=True)
            arcade.draw_text("Cliquez pour recommencer", 400, 50, arcade.color.GRAY, 10, anchor_x="center")
        elif self.menu_ouvert:
            self.draw_attack_menu()
        else:
            for i, msg in enumerate(self.logs[-2:]):
                color = arcade.color.BLACK
                if "super efficace" in msg.lower(): color = arcade.color.RED_ORANGE
                elif "critique" in msg.lower(): color = arcade.color.CRIMSON
                elif "échoué" in msg.lower() or "n'affecte pas" in msg.lower(): color = arcade.color.SLATE_GRAY
                arcade.draw_text(msg, 70, 115 - i * 55, color, 15, bold=(i==1))

    def on_mouse_press(self, x, y, button, modifiers):
        if self.fini:
            self.setup_combat()
            return
        if self.tour_joueur:
            if not self.menu_ouvert:
                self.menu_ouvert = True
            else:
                idx = 0 if x < 400 and y > 80 else 1 if x >= 400 and y > 80 else 2 if x < 400 else 3
                if idx < len(self.p1_data['capacites']):
                    self.attaquer(idx)

    def attaquer(self, idx):
        atk = self.p1_data['capacites'][idx]
        dmg, mult, crit, miss = self.combat_logic.calculer_degats(self.p1_data, self.p2_data, atk)
        
        self.logs = [f"{self.p1_data['nom']} utilise {atk['nom_attaque']} !"]
        
        if miss:
            self.logs.append("L'attaque a échoué !")
        else:
            self.p2_data['pv_actuels'] = max(0, self.p2_data['pv_actuels'] - dmg)
            if crit: self.logs.append("COUP CRITIQUE !")
            eff_msg = TypeChart.get_effectiveness_message(mult)
            if eff_msg: self.logs.append(eff_msg)

        self.menu_ouvert = False
        self.tour_joueur = False
        if self.p2_data['pv_actuels'] <= 0:
            arcade.schedule(self.clore_combat, 1.0)
        else:
            arcade.schedule(self.ia_tour, 1.2)

    def ia_tour(self, dt):
        arcade.unschedule(self.ia_tour)
        if self.fini: return
        atk = random.choice(self.p2_data['capacites'])
        dmg, mult, crit, miss = self.combat_logic.calculer_degats(self.p2_data, self.p1_data, atk)
        self.p1_data['pv_actuels'] = max(0, self.p1_data['pv_actuels'] - dmg)
        self.logs = [f"{self.p2_data['nom']} sauvage utilise {atk['nom_attaque']} !"]
        if miss: self.logs.append("Mais elle échoue !")
        elif crit: self.logs.append("Coup critique !")
        eff_msg = TypeChart.get_effectiveness_message(mult)
        if eff_msg: self.logs.append(eff_msg)
        self.tour_joueur = True

    def clore_combat(self, dt):
        arcade.unschedule(self.clore_combat)
        gain, monte = LevelEngine.appliquer_gain_et_check(self.p1_data, self.p2_data)
        self.logs.append(f"Gagné ! +{gain} EXP.")
        if monte:
            self.logs.append(f"LEVEL UP ! {self.p1_data['nom']} passe Niv.{self.p1_data['niveau']} !")
        self.fini = True

if __name__ == "__main__":
    game = PokeFantasyGame()
    arcade.run()