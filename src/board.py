# src/board.py

import random
from src.config import TAM, N_POZOS

class Board:
    def __init__(self):
        self.grid = [['' for _ in range(TAM)] for _ in range(TAM)]
        self.wumpus_alive = True   # Si el Wumpus está vivo
        self.place_elements()

    def place_elements(self):
        # Coloca la entrada siempre en (0, 0)
        self.grid[0][0] = 'E'
        posiciones_libres = [(i, j) for i in range(TAM) for j in range(TAM) if self.grid[i][j] == '']

        # Coloca Wumpus
        x, y = random.choice(posiciones_libres)
        self.grid[x][y] = 'W'
        posiciones_libres.remove((x, y))

        # Coloca tesoro
        x, y = random.choice(posiciones_libres)
        self.grid[x][y] = 'T'
        posiciones_libres.remove((x, y))

        # Coloca pozos
        for _ in range(N_POZOS):
            x, y = random.choice(posiciones_libres)
            self.grid[x][y] = 'P'
            posiciones_libres.remove((x, y))

    def print_board(self):  # Solo para depuración
        for fila in self.grid:
            print(fila)

    def perceive(self, x, y, heard_scream=False):
        percepciones = []
        # Viento y hedor (casillas adyacentes)
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < TAM and 0 <= ny < TAM:
                if self.grid[nx][ny] == 'P':
                    percepciones.append('Viento')
                if self.grid[nx][ny] == 'W':
                    percepciones.append('Hedor')
        if self.grid[x][y] == 'T':
            percepciones.append('Tesoro')
        if self.grid[x][y] == 'P':
            percepciones.append('Pozo')
        if self.grid[x][y] == 'W' and self.wumpus_alive:
            percepciones.append('Wumpus')
        if heard_scream:
            percepciones.append('Grito')
        return percepciones

    def shoot_arrow(self, x, y, direction):
        dx, dy = 0, 0
        if direction == 'UP':
            dx = -1
        elif direction == 'DOWN':
            dx = 1
        elif direction == 'LEFT':
            dy = -1
        elif direction == 'RIGHT':
            dy = 1
        else:
            return False  # Dirección inválida

        nx, ny = x + dx, y + dy
        # Dispara en línea recta mientras esté dentro del tablero
        while 0 <= nx < TAM and 0 <= ny < TAM:
            if self.grid[nx][ny] == 'W' and self.wumpus_alive:
                self.wumpus_alive = False
                return True  # ¡Wumpus muerto!
            nx += dx
            ny += dy
        return False  # No le dio al Wumpus

# Test rápido (puedes borrar esto después)
if __name__ == '__main__':
    tablero = Board()
    tablero.print_board()
