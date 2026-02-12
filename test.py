import arcade
from personnage import Player
from map import MapLoader

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Pokemon Arcade 3.0")
        self.player = None
        self.map_manager = None
        self.camera = None

    def setup(self):
        self.camera = arcade.camera.Camera2D()
        self.camera.zoom = 3.0
        
        self.map_manager = MapLoader("hub.tmx")
        self.player = Player()
        
        self.player.center_x = 400
        self.player.center_y = 300
        
        self.map_manager.scene.add_sprite("Player", self.player)
        self.map_manager.setup_physics(self.player)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.map_manager.scene.draw(pixelated=True)

    def on_update(self, delta_time):
        self.map_manager.physics_engine.update()
        self.player.update_animation(delta_time)
        self.camera.position = (self.player.center_x, self.player.center_y)

    def on_key_press(self, key, modifiers):
        s = 3
        if key == arcade.key.UP: self.player.change_y = s
        elif key == arcade.key.DOWN: self.player.change_y = -s
        elif key == arcade.key.LEFT: self.player.change_x = -s
        elif key == arcade.key.RIGHT: self.player.change_x = s

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.UP, arcade.key.DOWN): self.player.change_y = 0
        if key in (arcade.key.LEFT, arcade.key.RIGHT): self.player.change_x = 0

if __name__ == "__main__":
    game = MyGame()
    game.setup()
    arcade.run()