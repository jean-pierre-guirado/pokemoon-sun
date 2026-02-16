import arcade
import os
import json
import random
import unicodedata

# --- CONFIGURATION DES CHEMINS ---
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_PATH, "data")
SPRITE_PATH = os.path.join(BASE_PATH, "asset", "sprite")
DRESSEUR_JSON = os.path.join(DATA_PATH, "dresseur_config.json")
CAPA_JSON = os.path.join(DATA_PATH, "capacite_list.json")

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Poke Fantasy - Pure White Edition"

def normaliser(txt):
    return "".join([c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn']).lower().strip()

# --- CLASSES ISSUES DU MODELE PYGAME ---

class Pokemon:
    def __init__(self, data, db_capas):
        self.nom = data.get("nom", "Inconnu")
        self.niveau = data.get("niveau", 5)
        self.hp_base = data.get("hp_base", 100 + (self.niveau * 5))
        self.hp = data.get("hp_actuel", self.hp_base)
        self.xp = data.get("xp", 0)
        self.xp_max = self.niveau * 100
        self.stats = data.get("stats", {"attaque": 50 + self.niveau, "defense": 50 + self.niveau})
        self.capacites_noms = data.get("capacites", [])
        self.moves_obj = []
        
        for c in self.capacites_noms:
            m = next((m for m in db_capas if normaliser(m["nom_attaque"]) == normaliser(c)), None)
            self.moves_obj.append(m if m else {"nom_attaque": c, "puissance": 40})

    def gain_xp(self, montant):
        self.xp += montant
        leveled_up = False
        while self.xp >= self.xp_max:
            self.xp -= self.xp_max
            self.niveau += 1
            self.xp_max = self.niveau * 100
            self.hp_base += 10
            self.hp = self.hp_base
            leveled_up = True
        return leveled_up

    def to_dict(self):
        return {
            "nom": self.nom, "niveau": self.niveau, "hp_base": self.hp_base,
            "hp_actuel": self.hp, "xp": self.xp, "stats": self.stats,
            "capacites": self.capacites_noms
        }

class ExperienceEngine:
    @staticmethod
    def calculer_xp_gagne(ennemi):
        return ennemi.niveau * random.randint(15, 25)

class CombatEngine:
    @staticmethod
    def calculer_degats(attaquant, defenseur, move_data):
        pui = move_data.get("puissance", 40) or 40
        atk = attaquant.stats.get("attaque", 50)
        dfs = defenseur.stats.get("defense", 50)
        dmg = int((attaquant.niveau * 0.4 + 2) * pui * (atk/dfs) / 50 + 2)
        return max(1, dmg)

class ItemEngine:
    @staticmethod
    def utiliser_objet(item_nom, pokemon):
        nom = item_nom.lower().strip()
        
        if "bonbon" in nom or "rare-candy" in nom:
            pokemon.gain_xp(pokemon.xp_max)
            return True, f"Niveau Super ! {pokemon.nom} est Niv. {pokemon.niveau} !"

        if "potion" in nom:
            if pokemon.hp <= 0: return False, f"{pokemon.nom} est KO !"
            if pokemon.hp >= pokemon.hp_base: return False, "Deja full PV !"
            soin = 200 if "hyper" in nom else 50 if "super" in nom else 20
            if "max" in nom: soin = pokemon.hp_base
            old = pokemon.hp
            pokemon.hp = min(pokemon.hp_base, pokemon.hp + soin)
            return True, f"{pokemon.nom} soigne de {int(pokemon.hp - old)} PV."
            
        elif "rappel" in nom or "revive" in nom:
            if pokemon.hp <= 0:
                pokemon.hp = pokemon.hp_base // 2
                if "max" in nom: pokemon.hp = pokemon.hp_base
                return True, f"{pokemon.nom} est reanime !"
            return False, f"{pokemon.nom} n'est pas KO !"
            
        elif "restore" in nom or "guerison" in nom:
            pokemon.hp = pokemon.hp_base
            return True, f"PV restaures pour {pokemon.nom}."
            
        return False, "Aucun effet."

    @staticmethod
    def tenter_capture(ball_nom, ennemi):
        nom = ball_nom.lower().strip()
        if "master" in nom: return True
        taux_pv = (ennemi.hp / ennemi.hp_base)
        chance = 0.3
        if "hyper" in nom or "ultra" in nom: chance = 0.6
        elif "super" in nom or "great" in nom: chance = 0.4
        chance += (1.0 - taux_pv) * 0.3
        return random.random() < chance

# --- ENGINE PRINCIPAL ARCADE ---

class PokeFantasyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        # BACKGROUND BLANC ET PURE
        arcade.set_background_color(arcade.color.WHITE)
        
        self.etat = "PRINCIPAL"
        self.index_sel = 0
        self.message = ""
        self.item_en_cours = None
        self.ui_text = arcade.Text("", 50, 100, arcade.color.BLACK, 20)
        
        self.charger_donnees()
        self.generer_ennemi_aleatoire()
        self.charger_sprites()

    def charger_donnees(self):
        with open(DRESSEUR_JSON, 'r', encoding='utf-8') as f:
            self.data_full = json.load(f)
        with open(CAPA_JSON, 'r', encoding='utf-8') as f:
            self.db_capas = json.load(f)
        
        self.equipe = [Pokemon(p, self.db_capas) for p in self.data_full.get("equipe", [])]
        self.active_p = self.equipe[0]
        
        self.inventaire = []
        inv = self.data_full.get("inventaire", {})
        for cat in inv:
            for n, q in inv[cat].items():
                if q > 0: self.inventaire.append({"nom": n, "qty": q, "cat": cat})

    def sauvegarder_donnees(self):
        self.data_full["equipe"] = [p.to_dict() for p in self.equipe]
        new_inv = {"potions": {}, "balls": {}}
        for it in self.inventaire:
            cat = it["cat"]
            if cat not in new_inv: new_inv[cat] = {}
            new_inv[cat][it["nom"]] = it["qty"]
        self.data_full["inventaire"] = new_inv
        with open(DRESSEUR_JSON, 'w', encoding='utf-8') as f:
            json.dump(self.data_full, f, indent=4, ensure_ascii=False)

    def charger_sprites(self):
        self.tex_joueur = self._get_tex(self.active_p.nom, "dos")
        self.tex_ennemi = self._get_tex(self.ennemi.nom, "face")

    def _get_tex(self, nom, mode):
        target = normaliser(nom)
        for root, _, files in os.walk(SPRITE_PATH):
            for f in files:
                if target in normaliser(f) and mode in normaliser(f):
                    return arcade.load_texture(os.path.join(root, f))
        return arcade.make_soft_square_texture(200, arcade.color.GRAY)

    def generer_ennemi_aleatoire(self):
        possibles = []
        for root, _, files in os.walk(SPRITE_PATH):
            for f in files:
                if "_face" in f.lower(): 
                    nom_net = f.split("_face")[0].replace("_", " ")
                    if nom_net not in possibles: possibles.append(nom_net)
        nom = random.choice(possibles) if possibles else "Pikachu"
        lvl = max(1, self.active_p.niveau + random.randint(-1, 2))
        moves_pool = random.sample(self.db_capas, min(4, len(self.db_capas)))
        data_ennemi = {
            "nom": nom.capitalize(), "niveau": lvl,
            "hp_base": 80+(lvl*3), "hp_actuel": 80+(lvl*3),
            "stats": {"attaque": 40+lvl, "defense": 40+lvl},
            "capacites": [m["nom_attaque"] for m in moves_pool]
        }
        self.ennemi = Pokemon(data_ennemi, self.db_capas)

    def on_draw(self):
        self.clear()
        if self.etat == "GAME_OVER":
            arcade.draw_text("GAME OVER", SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arcade.color.RED, 40, anchor_x="center")
            return

        if self.active_p.hp > 0:
            arcade.draw_texture_rect(self.tex_joueur, arcade.LBWH(100, 200, 250, 250))
        arcade.draw_texture_rect(self.tex_ennemi, arcade.LBWH(450, 320, 250, 250))

        # Zone Message
        arcade.draw_lbwh_rectangle_filled(0, 0, 800, 200, arcade.color.WHITE)
        arcade.draw_lbwh_rectangle_outline(0, 0, 800, 200, arcade.color.BLACK, 5)

        self.draw_status_bar(50, 500, self.active_p, show_xp=True)
        self.draw_status_bar(450, 500, self.ennemi, show_xp=False)
        self.render_menu()

    def draw_status_bar(self, x, y, p, show_xp=False):
        arcade.draw_text(f"{p.nom} Lv.{p.niveau}", x, y+25, arcade.color.BLACK, 14, bold=True)
        arcade.draw_lbwh_rectangle_outline(x, y+5, 200, 12, arcade.color.BLACK, 1) # Outline pour fond blanc
        arcade.draw_lbwh_rectangle_filled(x, y+5, 200, 12, arcade.color.GRAY)
        hp_ratio = max(0, p.hp / p.hp_base)
        hp_clr = arcade.color.GREEN if hp_ratio > 0.5 else arcade.color.RED
        arcade.draw_lbwh_rectangle_filled(x, y+5, 200 * hp_ratio, 12, hp_clr)
        
        if show_xp:
            arcade.draw_lbwh_rectangle_outline(x, y-5, 200, 6, arcade.color.BLACK, 1)
            arcade.draw_lbwh_rectangle_filled(x, y-5, 200, 6, arcade.color.DARK_GRAY)
            xp_ratio = max(0, p.xp / p.xp_max)
            arcade.draw_lbwh_rectangle_filled(x, y-5, 200 * xp_ratio, 6, arcade.color.SKY_BLUE)

    def draw_selector(self, x, y, width=180, height=40):
        arcade.draw_lbwh_rectangle_outline(x - 10, y - 5, width, height, arcade.color.RED, 3)

    def render_menu(self):
        if self.etat == "PRINCIPAL":
            opts = ["ATTAQUE", "SAC", "POKEMON", "FUITE"]
            for i, o in enumerate(opts):
                tx, ty = 150+(i%2)*400, 140-(i//2)*70
                if i == self.index_sel: self.draw_selector(tx, ty, 200, 45)
                arcade.draw_text(o, tx, ty, arcade.color.BLACK, 22, bold=True)
        elif self.etat == "ATTAQUE":
            for i, m in enumerate(self.active_p.moves_obj):
                tx, ty = 100+(i%2)*400, 140-(i//2)*70
                if i == self.index_sel: self.draw_selector(tx, ty, 300, 40)
                arcade.draw_text(m["nom_attaque"].upper(), tx, ty, arcade.color.BLACK, 18)
        elif self.etat in ["EQUIPE", "CHOIX_SOIN"]:
            for i, p in enumerate(self.equipe):
                tx, ty = 80+(i%2)*400, 140-(i//2)*60
                if i == self.index_sel: self.draw_selector(tx, ty, 350, 35)
                ko_txt = " [KO]" if p.hp <= 0 else ""
                txt_clr = arcade.color.RED if p.hp <= 0 else arcade.color.BLACK
                arcade.draw_text(f"{p.nom} {int(p.hp)}/{p.hp_base} {ko_txt}", tx, ty, txt_clr, 14)
        elif self.etat == "SAC":
            visible = self.inventaire[self.index_sel//4*4 : self.index_sel//4*4+4]
            for i, it in enumerate(visible):
                tx, ty = 100+(i%2)*400, 140-(i//2)*60
                if i == self.index_sel % 4: self.draw_selector(tx, ty, 300, 35)
                arcade.draw_text(f"{it['nom']} x{it['qty']}", tx, ty, arcade.color.BLACK, 16)
        elif self.etat.startswith("MESSAGE"):
            self.ui_text.text = self.message
            self.ui_text.draw()

    def on_key_press(self, key, modifiers):
        if self.etat == "GAME_OVER": return
        if key == arcade.key.X:
            if self.etat == "CHOIX_SOIN": self.etat = "SAC"; return
            if not (self.etat == "EQUIPE" and self.active_p.hp <= 0):
                self.etat = "PRINCIPAL"; self.index_sel = 0; return

        nb_max = 4
        if self.etat == "SAC": nb_max = len(self.inventaire)
        elif self.etat in ["EQUIPE", "CHOIX_SOIN"]: nb_max = len(self.equipe)

        if nb_max > 0:
            if key == arcade.key.RIGHT: self.index_sel = (self.index_sel + 1) % nb_max
            elif key == arcade.key.LEFT: self.index_sel = (self.index_sel - 1) % nb_max
            elif key == arcade.key.UP: self.index_sel = (self.index_sel - 2) % nb_max
            elif key == arcade.key.DOWN: self.index_sel = (self.index_sel + 2) % nb_max

        if key in [arcade.key.ENTER, arcade.key.SPACE]:
            self.valider_selection()

    def valider_selection(self):
        if self.etat == "PRINCIPAL":
            if self.index_sel == 0: self.etat = "ATTAQUE"
            elif self.index_sel == 1: self.etat = "SAC"
            elif self.index_sel == 2: self.etat = "EQUIPE"
            elif self.index_sel == 3: self.message = "Fuite reussie !"; self.etat = "MESSAGE_V"
            self.index_sel = 0
        
        elif self.etat == "ATTAQUE":
            if self.index_sel < len(self.active_p.moves_obj):
                m = self.active_p.moves_obj[self.index_sel]
                dmg = CombatEngine.calculer_degats(self.active_p, self.ennemi, m)
                self.ennemi.hp = max(0, self.ennemi.hp - dmg)
                self.message = f"{self.active_p.nom} lance {m['nom_attaque']} !"; self.etat = "MESSAGE_J"
        
        elif self.etat == "SAC":
            if self.index_sel < len(self.inventaire):
                self.item_en_cours = self.inventaire[self.index_sel]
                if "ball" in self.item_en_cours["nom"].lower():
                    self.item_en_cours["qty"] -= 1
                    if ItemEngine.tenter_capture(self.item_en_cours["nom"], self.ennemi):
                        self.equipe.append(self.ennemi)
                        self.sauvegarder_donnees()
                        self.message = f"{self.ennemi.nom} capture ! XP gagne !"; self.attribuer_xp()
                    else: 
                        self.message = f"La {self.item_en_cours['nom']} a echoue !"; self.etat = "MESSAGE_J"
                else: 
                    self.etat = "CHOIX_SOIN"
                    self.index_sel = 0
        
        elif self.etat == "CHOIX_SOIN":
            cible = self.equipe[self.index_sel]
            ok, msg = ItemEngine.utiliser_objet(self.item_en_cours["nom"], cible)
            if ok:
                self.item_en_cours["qty"] -= 1
                if self.item_en_cours["qty"] <= 0:
                    self.inventaire.remove(self.item_en_cours)
                self.sauvegarder_donnees()
                self.message = msg
                self.etat = "MESSAGE_V"
            else:
                self.message = msg
                self.etat = "MESSAGE_J"
        
        elif self.etat == "EQUIPE":
            s = self.equipe[self.index_sel]
            if s.hp > 0:
                self.active_p = s; self.charger_sprites()
                self.message = f"Go {s.nom} !"; self.etat = "MESSAGE_J"
        
        elif self.etat == "MESSAGE_J":
            if self.ennemi.hp <= 0: 
                self.message = f"{self.ennemi.nom} est KO !"; self.attribuer_xp()
            else:
                m = random.choice(self.ennemi.moves_obj)
                dmg = CombatEngine.calculer_degats(self.ennemi, self.active_p, m)
                self.active_p.hp = max(0, self.active_p.hp - dmg)
                self.sauvegarder_donnees()
                self.message = f"{self.ennemi.nom} attaque !"; self.etat = "MESSAGE_E"
        
        elif self.etat == "MESSAGE_E":
            if self.active_p.hp <= 0:
                if all(p.hp <= 0 for p in self.equipe): self.etat = "GAME_OVER"
                else: self.message = "Pokemon KO ! Changez !"; self.etat = "EQUIPE"
            else: self.etat = "PRINCIPAL"
        
        elif self.etat == "MESSAGE_V":
            if self.ennemi.hp <= 0:
                self.generer_ennemi_aleatoire()
                self.charger_sprites()
            self.etat = "PRINCIPAL"
            self.index_sel = 0

    def attribuer_xp(self):
        xp_gain = ExperienceEngine.calculer_xp_gagne(self.ennemi)
        lvl_up = self.active_p.gain_xp(xp_gain)
        self.sauvegarder_donnees()
        if lvl_up:
            self.message += f" +{xp_gain} XP. LEVEL UP ! (Niv.{self.active_p.niveau})"
        else:
            self.message += f" +{xp_gain} XP."
        self.etat = "MESSAGE_V"

if __name__ == "__main__":
    game = PokeFantasyGame()
    arcade.run()