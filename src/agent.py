from src.config import TAM

class Agent:
    def __init__(self):
        self.x = 0  # Empieza en la entrada (0, 0)
        self.y = 0
        self.lives = 2
        self.has_arrow = True
        self.has_treasure = False
        self.visited = set([(0, 0)])  # Guarda las casillas visitadas

    def move(self, direction):
        if direction == 'UP' and self.x > 0:
            self.x -= 1
        elif direction == 'DOWN' and self.x < TAM - 1:
            self.x += 1
        elif direction == 'LEFT' and self.y > 0:
            self.y -= 1
        elif direction == 'RIGHT' and self.y < TAM - 1:
            self.y += 1
        self.visited.add((self.x, self.y))  # Marca la casilla como visitada

    def get_position(self):
        return (self.x, self.y)
