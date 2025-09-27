import pygame
from game.io.assets import load_image

class Pieces:
    def __init__(self):
        self.images = {}
        
    def get(self, key, path):
        s = self.images.get(key)
        if s is None:
            s = load_image(path)
            self.images[key] = s
        return s