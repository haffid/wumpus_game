import pygame
import os
import sys
from src.board import Board
from src.agent import Agent

# --- NUEVA FUNCIÓN: Para rutas de recursos (imágenes, sonidos, etc.) ---
def resource_path(relative_path):
    # Compatible con PyInstaller y ejecución normal
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- CONFIGURACIÓN ---
CELL_SIZE = 100         # Puedes ajustarlo a 80 o 70 si quieres más pequeño
GRID_SIZE = 5           # 5x5 como pide el proyecto
STATUS_HEIGHT = max(100, int(CELL_SIZE * 1.2))  # Altura proporcional al tamaño de celda
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
font = pygame.font.SysFont(None, int(CELL_SIZE * 0.2))      # Fuente normal
font_big = pygame.font.SysFont(None, int(CELL_SIZE * 0.3))  # Fuente grande

# --- MODIFICA LA FUNCIÓN PARA CARGAR SPRITES ---
def load_sprite(filename, scale):
    path = resource_path(os.path.join('assets', filename))
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (scale, scale))

# --- Carga de imágenes (USA resource_path) ---
adventurer_img = load_sprite('adventurer.png', CELL_SIZE - 10)
wumpus_img     = load_sprite('wumpus.png',     CELL_SIZE - 10)
hole_img       = load_sprite('pit.png',        CELL_SIZE - 10)
treasure_img   = load_sprite('treasure.png',   CELL_SIZE - 10)
entrance_img   = load_sprite('entrance.png',   CELL_SIZE - 10)

# --- Carga de sonidos (USA resource_path) ---
scream_sound = pygame.mixer.Sound(resource_path(os.path.join('assets', 'scream.wav')))
win_sound    = pygame.mixer.Sound(resource_path(os.path.join('assets', 'win.wav')))
lose_sound   = pygame.mixer.Sound(resource_path(os.path.join('assets', 'lose.wav')))


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
    menu_msg = font.render("Presiona A para Auto-Juego, R para reiniciar o Q para salir", True, BLACK)
    vidas_text = font.render(f'Vidas: {agent.lives}', True, BLACK)
    flecha_text = font.render(f'Flecha: {"Sí" if agent.has_arrow else "No"}', True, BLACK)
    tesoro_text = font.render(f'Tesoro: {"Sí" if agent.has_treasure else "No"}', True, BLACK)
    win.blit(menu_msg, (10, WINDOW_SIZE + 5))
    win.blit(vidas_text, (10, WINDOW_SIZE + 25))
    win.blit(flecha_text, (160, WINDOW_SIZE + 25))
    win.blit(tesoro_text, (320, WINDOW_SIZE + 25))
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
    if modo_auto_juego:
        auto_msg = font.render("Modo auto-juego: ACTIVADO", True, RED)
        win.blit(auto_msg, (10, WINDOW_SIZE + STATUS_HEIGHT - 60))


#controla el modo si avanza o modo disparo
modo_disparo = False
# Controla si el agente juega solo
modo_auto_juego = False
# Temporizador para auto_move
ultimo_auto_move = 0
intervalo_auto_move = 1000  # milisegundos = 1 segundos

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
                sys.exit()

            # Permite movimiento siempre que el mensaje NO sea de muerte, fin o victoria
            elif event.type == pygame.KEYDOWN and not (
                "pierdes" in message.lower()
                or "fin" in message.lower()
                or "victoria" in message.lower()
            ):
                x, y = agent.get_position()
                moved = False

                # Tecla A → activar/desactivar modo auto-juego
                if event.key == pygame.K_a:
                    modo_auto_juego = not modo_auto_juego
                    message = "Modo auto-juego ACTIVADO" if modo_auto_juego else "Modo auto-juego DESACTIVADO"

                if event.key == pygame.K_SPACE and agent.has_arrow and not modo_disparo:
                    modo_disparo = True
                    message = "Modo disparo activado. Usa flechas para apuntar."

                # --- Ejecutar disparo en la dirección presionada ---
                elif modo_disparo:
                    direction = None
                    if event.key == pygame.K_UP:
                        direction = 'UP'
                    elif event.key == pygame.K_DOWN:
                        direction = 'DOWN'
                    elif event.key == pygame.K_LEFT:
                        direction = 'LEFT'
                    elif event.key == pygame.K_RIGHT:
                        direction = 'RIGHT'

                    if direction:
                        if board.shoot_arrow(x, y, direction):
                            message = f"¡Has matado al Wumpus hacia {direction}! Se escucha un grito."
                            scream_sound.play()
                            heard_scream = True
                        else:
                            message = f"La flecha no dio en el blanco ({direction})."
                        agent.has_arrow = False
                        modo_disparo = False  # Salir del modo disparo

                # --- Movimiento normal si no está en modo disparo ---
                elif not modo_disparo:
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

        # --- AUTO JUEGO ---
        if modo_auto_juego and running:
            tiempo_actual = pygame.time.get_ticks()
            if tiempo_actual - ultimo_auto_move >= intervalo_auto_move:
                direction = agent.auto_move(board, heard_scream)
                if direction:
                    agent.move(direction)
                    moved = True
                    agent.visited.add(agent.get_position())
                    
                    pos = agent.get_position()
                    percepciones = board.perceive(pos[0], pos[1], heard_scream)
                    
                    # Si cae en un pozo
                    if 'Pozo' in percepciones:
                        agent.lives -= 1
                        peligros_revelados.add(pos)
                        agent.danger_cells.add(pos)
                        if agent.lives == 0:
                            message = "¡Has perdido todas tus vidas! Fin del juego."
                            lose_sound.play()
                            show_menu = True
                            running = False
                        else:
                            message = "¡Te caíste en un pozo! Pierdes una vida."
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
                        agent.danger_cells.add(pos)
                        
                        # si tengo flecha, guardo la posicion del wumpus para ir a cazarlo
                        if agent.has_arrow:
                            agent.wumpus_target = pos

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
                        agent.safe_cells.add(pos)
                        agent.visited.add(pos)
                        win_sound.play()
                    
                    # Si sale con el tesoro por la entrada
                    elif agent.has_treasure and pos == (0, 0):
                        message = "¡FELICIDADES! Has salido con el tesoro. ¡Victoria!"
                        win_sound.play()
                        show_menu = True
                        running = False
                    
                    # Mensajes de percepción normal (opcional)
                    else:
                        msg = []
                        if 'Viento' in percepciones:
                            msg.append("Percibes viento")
                        if 'Hedor' in percepciones:
                            msg.append("Percibes hedor")
                        if 'Grito' in percepciones:
                            agent.wumpus_target = None
                            msg.append("¡Grito! El agente disparó la flecha automáticamente.")
                        message = ", ".join(msg) if msg else ""
                ultimo_auto_move = tiempo_actual
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
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reiniciar juego completo
                    board, agent, heard_scream, message, running, peligros_revelados, show_menu = reset_vars()
                    break
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
        if running:
            break
