import pygame
import os
from src.board import Board
from src.agent import Agent

# --- CONFIGURACIÓN ---
CELL_SIZE = 140        # Tamaño de cada celda en píxeles
GRID_SIZE = 5          # Tamaño del tablero (5x5)
STATUS_HEIGHT = 200    # Altura para mostrar mensajes e instrucciones
WINDOW_SIZE = CELL_SIZE * GRID_SIZE
FPS = 30               # Cuadros por segundo

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (211, 211, 211)
RED = (255, 0, 0)

pygame.init()
pygame.mixer.init()
window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + STATUS_HEIGHT))
pygame.display.set_caption('Mundo de Wumpus')
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)
font_big = pygame.font.SysFont(None, 40)

# --- Función para cargar y escalar sprites PNG ---
def load_sprite(filename, scale):
    path = os.path.join('assets', filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (scale, scale))

# --- Carga de imágenes ---
adventurer_img = load_sprite('adventurer.png', CELL_SIZE - 10)
wumpus_img     = load_sprite('wumpus.png',     CELL_SIZE - 10)
hole_img       = load_sprite('hole.png',       CELL_SIZE - 10)
treasure_img   = load_sprite('treasure.png',   CELL_SIZE - 10)
entrance_img   = load_sprite('entrance.png',   CELL_SIZE - 10)

# --- Carga de sonidos ---
scream_sound = pygame.mixer.Sound(os.path.join('assets', 'scream.wav'))
win_sound    = pygame.mixer.Sound(os.path.join('assets', 'win.wav'))
lose_sound   = pygame.mixer.Sound(os.path.join('assets', 'lose.wav'))

# --- Función para reiniciar todos los valores del juego ---
def reset_vars():
    return Board(), Agent(), False, "", True, set(), False

board, agent, heard_scream, message, running, peligros_revelados, show_menu = reset_vars()

# --- Dibuja el tablero mostrando solo celdas visitadas, reveladas, o del agente ---
def draw_grid(win, board, agent, peligros_revelados):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x, y = j * CELL_SIZE, i * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(win, WHITE, rect)
            pygame.draw.rect(win, BLACK, rect, 2)
            # Solo dibuja sprites en casillas visitadas, reveladas, o donde está el agente
            if (i, j) in agent.visited or (i, j) == agent.get_position() or (i, j) in peligros_revelados:
                if board.grid[i][j] == 'E':
                    win.blit(entrance_img, rect.move(5, 5))
                if board.grid[i][j] == 'P':
                    win.blit(hole_img, rect.move(5, 5))
                if board.grid[i][j] == 'W' and board.wumpus_alive:
                    win.blit(wumpus_img, rect.move(5, 5))
                # Muestra el tesoro si está ahí o el agente lo acaba de tomar
                if (board.grid[i][j] == 'T') or ((i, j) == agent.get_position() and agent.has_treasure):
                    win.blit(treasure_img, rect.move(5, 5))
            else:
                pygame.draw.rect(win, GRAY, rect)
                pygame.draw.rect(win, BLACK, rect, 2)
            # Siempre dibuja el aventurero sobre todo lo demás
            if (i, j) == agent.get_position():
                win.blit(adventurer_img, rect.move(5, 5))

# --- Dibuja panel de estado, mensajes e instrucciones ---
def draw_status(win, agent, message, show_menu):
    pygame.draw.rect(win, GRAY, (0, WINDOW_SIZE, WINDOW_SIZE, STATUS_HEIGHT))
    vidas_text = font.render(f'Vidas: {agent.lives}', True, BLACK)
    flecha_text = font.render(f'Flecha: {"Sí" if agent.has_arrow else "No"}', True, BLACK)
    tesoro_text = font.render(f'Tesoro: {"Sí" if agent.has_treasure else "No"}', True, BLACK)
    win.blit(vidas_text, (10, WINDOW_SIZE + 10))
    win.blit(flecha_text, (160, WINDOW_SIZE + 10))
    win.blit(tesoro_text, (320, WINDOW_SIZE + 10))
    # Mensaje principal (multi-línea si es largo)
    lines = []
    if message:
        while len(message) > 45:
            idx = message[:45].rfind(" ")
            lines.append(message[:idx])
            message = message[idx+1:]
        lines.append(message)
    for i, line in enumerate(lines):
        msg = font.render(
            line,
            True,
            RED if "pierdes" in line.lower() or "fin" in line.lower() or "victoria" in line.lower() else BLACK
        )
        win.blit(msg, (10, WINDOW_SIZE + 45 + 30 * i))   # Espacio mayor entre líneas
    instrucciones = font.render(
        "Flechas: Mover   |   Espacio: Disparar   |   Gana si sales con el tesoro",
        True,
        BLACK
    )
    win.blit(instrucciones, (10, WINDOW_SIZE + STATUS_HEIGHT - 35))
    # Menú de reinicio cuando termina el juego
    if show_menu:
        menu_msg = font_big.render("Presiona R para reiniciar o Q para salir", True, BLACK)
        win.blit(menu_msg, (WINDOW_SIZE // 16, WINDOW_SIZE + STATUS_HEIGHT - 75))

# --- Ciclo principal del juego ---
while True:
    while running:
        window.fill(GRAY)
        draw_grid(window, board, agent, peligros_revelados)
        draw_status(window, agent, message, False)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            # Permite movimiento siempre que el mensaje NO sea de muerte, fin o victoria
            elif event.type == pygame.KEYDOWN and not (
                "pierdes" in message.lower()
                or "fin" in message.lower()
                or "victoria" in message.lower()
            ):
                x, y = agent.get_position()
                moved = False
                # Movimiento con flechas
                if event.key == pygame.K_UP and x > 0:
                    agent.move('UP')
                    moved = True
                elif event.key == pygame.K_DOWN and x < GRID_SIZE - 1:
                    agent.move('DOWN')
                    moved = True
                elif event.key == pygame.K_LEFT and y > 0:
                    agent.move('LEFT')
                    moved = True
                elif event.key == pygame.K_RIGHT and y < GRID_SIZE - 1:
                    agent.move('RIGHT')
                    moved = True
                # Disparo con barra espaciadora
                elif event.key == pygame.K_SPACE and agent.has_arrow:
                    if board.shoot_arrow(x, y, 'UP'):
                        message = "¡Has matado al Wumpus! Se escucha un grito."
                        scream_sound.play()
                        heard_scream = True
                    else:
                        message = "La flecha no dio en el blanco."
                    agent.has_arrow = False

                if moved:
                    pos = agent.get_position()
                    agent.visited.add(pos)
                    percepciones = board.perceive(pos[0], pos[1], heard_scream)
                    # Si cae en un pozo
                    if 'Pozo' in percepciones:
                        agent.lives -= 1
                        peligros_revelados.add(pos)
                        if agent.lives == 0:
                            message = "¡Has perdido todas tus vidas! Fin del juego."
                            lose_sound.play()
                            show_menu = True
                            running = False
                        else:
                            message = "¡Te caíste en un pozo! Pierdes una vida."
                            # Muestra el tablero actualizado antes del delay
                            window.fill(GRAY)
                            draw_grid(window, board, agent, peligros_revelados)
                            draw_status(window, agent, message, False)
                            pygame.display.flip()
                            pygame.time.delay(1500)
                            agent.x, agent.y = 0, 0
                            agent.visited.add((0, 0))
                            message = ""
                    # Si lo devora el Wumpus
                    elif 'Wumpus' in percepciones:
                        agent.lives -= 1
                        peligros_revelados.add(pos)
                        if agent.lives == 0:
                            message = "¡Has perdido todas tus vidas! Fin del juego."
                            lose_sound.play()
                            show_menu = True
                            running = False
                        else:
                            message = "¡El Wumpus te devoró! Pierdes una vida."
                            window.fill(GRAY)
                            draw_grid(window, board, agent, peligros_revelados)
                            draw_status(window, agent, message, False)
                            pygame.display.flip()
                            pygame.time.delay(1500)
                            agent.x, agent.y = 0, 0
                            agent.visited.add((0, 0))
                            message = ""
                    # Si encuentra el tesoro
                    elif 'Tesoro' in percepciones and not agent.has_treasure:
                        message = "¡Encontraste el tesoro!"
                        agent.has_treasure = True
                        board.grid[pos[0]][pos[1]] = ''
                        win_sound.play()  # Sonido de victoria al recoger tesoro
                    # Si sale con el tesoro por la entrada
                    elif agent.has_treasure and pos == (0, 0):
                        message = "¡FELICIDADES! Has salido con el tesoro. ¡Victoria!"
                        win_sound.play()
                        show_menu = True
                        running = False
                    # Mensajes de percepción (puede seguir jugando)
                    else:
                        msg = []
                        if 'Viento' in percepciones:
                            msg.append("Percibes viento")
                        if 'Hedor' in percepciones:
                            msg.append("Percibes hedor")
                        if 'Grito' in percepciones:
                            msg.append("¡Grito!")
                        message = ", ".join(msg) if msg else ""
        clock.tick(FPS)

    # --- Menú de reinicio/salir cuando termina el juego ---
    while True:
        window.fill(GRAY)
        draw_grid(window, board, agent, peligros_revelados)
        draw_status(window, agent, message, True)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reiniciar juego completo
                    board, agent, heard_scream, message, running, peligros_revelados, show_menu = reset_vars()
                    break
                elif event.key == pygame.K_q:
                    pygame.quit()
                    exit()
        if running:
            break
