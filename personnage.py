import arcade
import os

class Player(arcade.Sprite):
    def __init__(self, anim_speed=0.15):
        # On utilise le dossier local (mappa)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        initial_texture_path = os.path.join(self.base_path, "down2.png")
        initial_texture = arcade.load_texture(initial_texture_path)
        super().__init__(initial_texture, scale=0.2)
        
        self.anim_speed = anim_speed
        self.current_frame = 0.0
        
        self.walk_down = self.load_animation_frames("down")
        self.walk_up = self.load_animation_frames("up")
        self.walk_left = self.load_animation_frames("left")
        self.walk_right = self.load_animation_frames("right")

    def load_animation_frames(self, direction):
        frames = []
        for i in range(1, 4):
            path = os.path.join(self.base_path, f"{direction}{i}.png")
            frames.append(arcade.load_texture(path))
        return frames

    def update_animation(self, delta_time: float = 1/60):
        if self.change_x == 0 and self.change_y == 0:
            self.current_frame = 1.0
        else:
            self.current_frame += self.anim_speed
            if self.current_frame >= 3:
                self.current_frame = 0.0

        idx = int(self.current_frame)
        if self.change_y > 0: self.texture = self.walk_up[idx]
        elif self.change_y < 0: self.texture = self.walk_down[idx]
        elif self.change_x < 0: self.texture = self.walk_left[idx]
        elif self.change_x > 0: self.texture = self.walk_right[idx]