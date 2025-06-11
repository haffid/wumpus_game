# src/agent.py

class Agent:
    def __init__(self):
        # Posición inicial
        self.x, self.y = 0, 0
        # Estado del agente
        self.lives = 2
        self.has_arrow = True
        self.has_treasure = False
        # Memoria del agente
        self.visited = set()        # Casillas visitadas
        self.safe_cells = set()     # Casillas seguras conocidas
        self.unsafe_cells = set()   # Casillas deducidas como peligrosas
        self.frontier_cells = set() # Casillas frontera para explorar
        self.danger_cells = set()   # Casillas conocidas como peligrosas (Pozo, Wumpus)
        self.wumpus_target = None   # Posición del Wumpus conocida (para intentar matarlo)

        # Inicialmente en la casilla de entrada (0,0)
        self.visited.add((0, 0))
        self.safe_cells.add((0, 0))

    def get_position(self):
        return self.x, self.y

    def move(self, direction):
        # Mover al agente según la dirección indicada
        if direction == 'UP' and self.x > 0:
            self.x -= 1
        elif direction == 'DOWN' and self.x < 4:
            self.x += 1
        elif direction == 'LEFT' and self.y > 0:
            self.y -= 1
        elif direction == 'RIGHT' and self.y < 4:
            self.y += 1

    def auto_move(self, board, heard_scream):
        """
        Algoritmo básico para que el agente se mueva solo.

        - Marca casillas seguras si no percibe viento ni hedor.
        - Construye la frontera de exploración.
        - Elige la siguiente casilla segura a visitar (básico BFS-like).
        - Devuelve la dirección en la que debe moverse.
        """
        from random import choice

        current_pos = self.get_position()

        # PRIORIDAD: regresar si ya tiene el tesoro
        if self.has_treasure:
            if current_pos == (0, 0):
                return None  # Ya llegó

            # Posibles movimientos: UP, DOWN, LEFT, RIGHT
            moves = []
            if self.x > 0:
                moves.append(('UP', (self.x - 1, self.y)))
            if self.x < 4:
                moves.append(('DOWN', (self.x + 1, self.y)))
            if self.y > 0:
                moves.append(('LEFT', (self.x, self.y - 1)))
            if self.y < 4:
                moves.append(('RIGHT', (self.x, self.y + 1)))

            # Filtrar solo movimientos a celdas seguras
            # safe_moves = [(dir, pos) for dir, pos in moves if pos in self.safe_cells or pos in self.visited]
            safe_moves = [(dir, pos) for dir, pos in moves if pos in self.safe_cells and pos not in self.danger_cells]


            # Si hay movimientos seguros, elegir el que acerque más a (0,0)
            if safe_moves:
                # Ordenar por distancia Manhattan a (0,0)
                safe_moves.sort(key=lambda m: abs(m[1][0] - 0) + abs(m[1][1] - 0))
                # Devolver la dirección que más acerque a (0,0)
                return safe_moves[0][0]
            else:
                # No hay camino seguro conocido → quedarse quieto (puedes mejorarlo con A* si querés)
                return None

        perceptions = board.perceive(current_pos[0], current_pos[1], heard_scream)

        # Si piso un Pozo o Wumpus, marco la celda como peligrosa
        if 'Pozo' in perceptions or 'Wumpus' in perceptions:
            self.danger_cells.add(current_pos)

        # --- Actualizar conocimiento ---
        # Si no percibe Viento, Hedor, Pozo o Wumpus → marca adyacentes como seguras
        if not any(p in perceptions for p in ['Viento', 'Hedor', 'Pozo', 'Wumpus']):
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = current_pos[0] + dx, current_pos[1] + dy
                if 0 <= nx < 5 and 0 <= ny < 5:
                    if (nx, ny) not in self.visited and (nx, ny) not in self.safe_cells:
                        self.safe_cells.add((nx, ny))
        else:
            # Si percibe Viento o Hedor → no marca adyacentes como seguras
            # (opcional: podrías marcar como posibles peligrosas)
            pass
        
        # Cazando al wumpus
        if self.wumpus_target and self.has_arrow:
            target_x, target_y = self.wumpus_target
            current_x, current_y = self.get_position()

            #Me alineo una casilla antes del wumpus para no morir y poder disparar la flecha
            # Si estoy alineado en fila
            if current_x == target_x:
                distance = abs(current_y - target_y)
                if distance == 1:
                    # Disparar en la dirección correcta SIN moverse
                    board.shoot_arrow(current_x, current_y, 'RIGHT' if target_y > current_y else 'LEFT')
                    self.has_arrow = False
                    self.wumpus_target = None
                    return None
                else:
                    # Moverse acercándose SOLO por safe_cells
                    if current_y < target_y:
                        next_pos = (current_x, current_y + 1)
                        if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                            return 'RIGHT'
                    elif current_y > target_y:
                        next_pos = (current_x, current_y - 1)
                        if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                            return 'LEFT'

            # Si estoy en la misma columna (Y == Y)
            elif current_y == target_y:
                distance = abs(current_x - target_x)
                if distance == 1:
                    # Disparar en la dirección correcta SIN moverse
                    board.shoot_arrow(current_x, current_y, 'DOWN' if target_x > current_x else 'UP')
                    self.has_arrow = False
                    self.wumpus_target = None
                    return None
                else:
                    # Moverse acercándose SOLO por safe_cells
                    if current_x < target_x:
                        next_pos = (current_x + 1, current_y)
                        if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                            return 'DOWN'
                    elif current_x > target_x:
                        next_pos = (current_x - 1, current_y)
                        if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                            return 'UP'

            # Si no estoy alineado → moverme hacia el Wumpus (solo por safe_cells)
            if current_x < target_x:
                next_pos = (current_x + 1, current_y)
                if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                    return 'DOWN'
            elif current_x > target_x:
                next_pos = (current_x - 1, current_y)
                if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                    return 'UP'
            elif current_y < target_y:
                next_pos = (current_x, current_y + 1)
                if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                    return 'RIGHT'
            elif current_y > target_y:
                next_pos = (current_x, current_y - 1)
                if next_pos in self.safe_cells and next_pos not in self.danger_cells:
                    return 'LEFT'

        # --- Construir frontera ---
        self.frontier_cells = set()
        for cell in self.safe_cells:
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = cell[0] + dx, cell[1] + dy
                if 0 <= nx < 5 and 0 <= ny < 5:
                    if (nx, ny) not in self.visited and (nx, ny) not in self.unsafe_cells:
                        self.frontier_cells.add((nx, ny))

        # --- Elegir próximo movimiento ---
        if self.frontier_cells:
            target_cell = choice(list(self.frontier_cells))
            tx, ty = target_cell

            # Decidir hacia qué dirección moverse
            if tx < self.x:
                return 'UP'
            elif tx > self.x:
                return 'DOWN'
            elif ty < self.y:
                return 'LEFT'
            elif ty > self.y:
                return 'RIGHT'

        # Si no hay frontera → quedarse quieto (None)
        return None
