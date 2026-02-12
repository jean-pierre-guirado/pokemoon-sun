import arcade
import os

class MapLoader:
    def __init__(self, map_name):
        # On récupère le dossier où se trouve ce script (mappa)
        base_path = os.path.dirname(os.path.abspath(__file__))
        # On cherche le fichier directement dans ce dossier
        full_path = os.path.join(base_path, map_name)
        
        print(f"Chargement de la carte : {full_path}")
        
        self.tile_map = arcade.load_tilemap(full_path, scaling=1.0)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.physics_engine = None

    def setup_physics(self, player_sprite):
        if "Walls" in self.tile_map.sprite_lists:
            self.physics_engine = arcade.PhysicsEngineSimple(
                player_sprite,
                self.tile_map.sprite_lists["Walls"]
            )
        else:
            self.physics_engine = arcade.PhysicsEngineSimple(player_sprite, [])