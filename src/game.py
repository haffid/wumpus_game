# src/game.py

from src.board import Board
from src.agent import Agent

class Game:
    def __init__(self):
        self.board = Board()
        self.agent = Agent()
        self.running = True
        self.heard_scream = False  # Si el agente escuchó el grito

    def print_state(self):
        for i in range(len(self.board.grid)):
            row = ''
            for j in range(len(self.board.grid[i])):
                if (i, j) == self.agent.get_position():
                    row += 'A '  # A de Agente
                elif self.board.grid[i][j] != '':
                    row += self.board.grid[i][j] + ' '
                else:
                    row += '. '
            print(row)
        print(f"Vidas: {self.agent.lives}, Flecha: {self.agent.has_arrow}, Tesoro: {self.agent.has_treasure}")

    def play(self):
        while self.running:
            self.print_state()
            pos = self.agent.get_position()

            # Condición de victoria
            if self.agent.has_treasure and pos == (0, 0):
                print("¡FELICIDADES! Has salido con el tesoro. ¡Victoria!")
                self.running = False
                continue

            percepciones = self.board.perceive(pos[0], pos[1], self.heard_scream)
            print(f"Percepciones: {', '.join(percepciones) if percepciones else 'Nada especial.'}")

            # Lógica de muerte (el Wumpus solo mata si está vivo)
            if 'Pozo' in percepciones:
                print("¡Te caíste en un pozo! Pierdes una vida.")
                self.agent.lives -= 1
                if self.agent.lives == 0:
                    print("¡Has perdido todas tus vidas! Fin del juego.")
                    self.running = False
                else:
                    self.agent.x, self.agent.y = 0, 0
                continue
            if 'Wumpus' in percepciones:
                print("¡El Wumpus te devoró! Pierdes una vida.")
                self.agent.lives -= 1
                if self.agent.lives == 0:
                    print("¡Has perdido todas tus vidas! Fin del juego.")
                    self.running = False
                else:
                    self.agent.x, self.agent.y = 0, 0
                continue
            if 'Tesoro' in percepciones and not self.agent.has_treasure:
                print("¡Encontraste el tesoro!")
                self.agent.has_treasure = True
                self.board.grid[pos[0]][pos[1]] = ''

            # Comando de usuario
            move = input("Acción (UP/DOWN/LEFT/RIGHT, SHOOT <DIRECCION>, Q para salir): ").upper().strip()
            if move in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                self.agent.move(move)
            elif move.startswith('SHOOT') and self.agent.has_arrow:
                try:
                    _, direction = move.split()
                    if direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                        if self.board.shoot_arrow(pos[0], pos[1], direction):
                            print("¡Has matado al Wumpus! Se escucha un grito en todo el tablero.")
                            self.heard_scream = True
                        else:
                            print("La flecha no dio en el blanco.")
                        self.agent.has_arrow = False
                    else:
                        print("Dirección inválida. Usa UP, DOWN, LEFT, RIGHT.")
                except ValueError:
                    print("Uso: SHOOT <DIRECCION>")
            elif move == 'Q':
                self.running = False
            else:
                print("Acción inválida.")

if __name__ == '__main__':
    juego = Game()
    juego.play()
