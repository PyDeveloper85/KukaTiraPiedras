import asyncio
import os
import random
import sys
import pygame

async def main():
    pygame.init()
    pygame.mixer.init()

    # --- Música (segura para navegador) ---
    try:
        pygame.mixer.music.load(os.path.join("Assets", "audio", "sound1.ogg"))
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass

    # --- Configuración ---
    ANCHO = 380
    ALTO = 420
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Tira piedras 🦁")

    SABANA_FONDO = (128, 191, 255)
    SUELO_COLOR = (128, 128, 128)
    TEXTO_COLOR = (255, 255, 255)

    reloj = pygame.time.Clock()
    FPS = 50
    ALTURA_SUELO = 380

    # --- Carga de imágenes ---
    try:
        IMAGEN_LEON = pygame.image.load(os.path.join("Assets", "Leon", "Leon.png")).convert_alpha()
        IMAGEN_FONDO = pygame.image.load(os.path.join("Assets", "Fondo", "fondo.png")).convert_alpha()
        bird01 = pygame.image.load(os.path.join("Assets", "BIrds", "bird01.png")).convert_alpha()
        bird02 = pygame.image.load(os.path.join("Assets", "BIrds", "bird02.png")).convert_alpha()
        roca_img = pygame.image.load(os.path.join("Assets", "Obstaculos", "roca.png")).convert_alpha()
        arbusto_img = pygame.image.load(os.path.join("Assets", "Obstaculos", "arbusto.png")).convert_alpha()
    except pygame.error as e:
        print(f"Error al cargar imágenes: {e}")
        pygame.quit()
        sys.exit()

    # --- Sistema de récord ---
    ARCHIVO_RECORD = os.path.join("Assets", "HIghscores", "record.txt")

    def cargar_record():
        if not os.path.exists(ARCHIVO_RECORD):
            try:
                with open(ARCHIVO_RECORD, "w") as f:
                    f.write("0")
            except OSError:
                return 0
            return 0
        try:
            with open(ARCHIVO_RECORD, "r") as f:
                contenido = f.read().strip()
                return int(contenido) if contenido.isdigit() else 0
        except (OSError, ValueError):
            return 0

    def guardar_record(nuevo_record):
        try:
            with open(ARCHIVO_RECORD, "w") as f:
                f.write(str(nuevo_record))
        except OSError:
            print("No se pudo guardar el récord.")

    record_maximo = cargar_record()

    # ============================================
    # CLASES
    # ============================================

    class Leon:
        def __init__(self):
            self.ancho = 100
            self.alto = 100
            self.imagen = pygame.transform.scale(IMAGEN_LEON, (self.ancho, self.alto))
            self.x = 100
            self.y = ALTURA_SUELO - self.alto
            self.vel_y = 0
            self.gravedad = 0.9
            self.salto_fuerza = -21.5
            self.en_el_suelo = True

        def saltar(self):
            if self.en_el_suelo:
                self.vel_y = self.salto_fuerza
                self.en_el_suelo = False

        def actualizar(self):
            self.vel_y += self.gravedad
            self.y += self.vel_y
            if self.y >= ALTURA_SUELO - self.alto:
                self.y = ALTURA_SUELO - self.alto
                self.vel_y = 0
                self.en_el_suelo = True

        def dibujar(self, superficie):
            superficie.blit(self.imagen, (self.x, self.y))

        def obtener_rect(self):
            return pygame.Rect(self.x + 15, self.y + 15, self.ancho - 30, self.alto - 15)

    # ---------- Clase base de obstáculos ----------
    class Obstaculo:
        def __init__(self, velocidad, x_pos=ANCHO):
            self.ancho = 100
            self.alto = 100
            self.velocidad = velocidad
            self.x = x_pos
            self.y = ALTURA_SUELO - self.alto
            self.imagen = None  # se define en las subclases

        def actualizar(self):
            self.x -= self.velocidad

        def dibujar(self, superficie):
            superficie.blit(self.imagen, (self.x, self.y))

        def obtener_rect(self):
            # Hitbox genérica (las subclases pueden sobreescribir)
            return pygame.Rect(
                self.x + 15,
                self.y + 10,
                self.ancho - 30,
                self.alto - 20
            )

        def fuera_de_pantalla(self):
            return self.x + self.ancho < 0

    # ---------- Subclases ----------
    class Roca(Obstaculo):
        def __init__(self, velocidad, x_pos=ANCHO):
            super().__init__(velocidad, x_pos)
            self.imagen = pygame.transform.scale(roca_img, (self.ancho, self.alto))

        def obtener_rect(self):
            return pygame.Rect(self.x + 18, self.y + 15, self.ancho - 36, self.alto - 25)

    class Arbusto(Obstaculo):
        def __init__(self, velocidad, x_pos=ANCHO):
            super().__init__(velocidad, x_pos)
            self.imagen = pygame.transform.scale(arbusto_img, (self.ancho, self.alto))

        def obtener_rect(self):
            return pygame.Rect(self.x + 12, self.y + 20, self.ancho - 24, self.alto - 30)

    class Bird(Obstaculo):
        def __init__(self, velocidad, x_pos=ANCHO, variant=0):
            super().__init__(velocidad, x_pos)

            # Tamaño más pequeño
            self.ancho = 55
            self.alto = 45

            # Posicionada un poco por encima de las rocas y arbustos
            self.y = ALTURA_SUELO - self.alto - 55  # ← aquí controlas cuánto más arriba va

            img = bird01 if variant == 0 else bird02
            self.imagen = pygame.transform.scale(img, (self.ancho, self.alto))

        def obtener_rect(self):
            # Hitbox más ajustada al tamaño pequeño
            return pygame.Rect(
                self.x + 8,
                self.y + 8,
                self.ancho - 16,
                self.alto - 16
            )

    # ============================================
    # VARIABLES DEL JUEGO
    # ============================================
    leon = Leon()
    obstaculos = []
    puntuacion = 0
    velocidad_juego = 7.0
    frecuencia_obstaculo = 0

    fondo_x1 = 0
    fondo_x2 = ANCHO

    fuente = pygame.font.SysFont("Orbitron", 25)
    fuente_grande = pygame.font.SysFont("Orbitron", 20)
    fuente_titulo = pygame.font.SysFont("Orbitron", 50, bold=True)

    en_menu = True
    jugando = True
    game_over = False

    def reiniciar_partida():
        nonlocal leon, obstaculos, puntuacion, velocidad_juego
        nonlocal fondo_x1, fondo_x2, game_over, SABANA_FONDO, frecuencia_obstaculo
        leon = Leon()
        obstaculos = []
        puntuacion = 0
        velocidad_juego = 7.0
        frecuencia_obstaculo = 0
        fondo_x1 = 0
        fondo_x2 = ANCHO
        game_over = False
        SABANA_FONDO = (128, 191, 255)
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

    # ============================================
    # BUCLE PRINCIPAL
    # ============================================
    while jugando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jugando = False
                pygame.mixer.quit()
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                if en_menu:
                    if evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                        en_menu = False
                else:
                    if evento.key in (pygame.K_SPACE, pygame.K_UP):
                        if not game_over:
                            leon.saltar()
                        else:
                            reiniciar_partida()

        # ---------- MENÚ ----------
        if en_menu:
            pantalla.fill(SABANA_FONDO)
            pantalla.blit(IMAGEN_FONDO, (0, 0))

            texto_tit = fuente_titulo.render("Kuka Tira Piedras", True, (143, 0, 255))
            texto_instrucciones = fuente.render("ESPACIO o ENTER para empezar", True, TEXTO_COLOR)
            texto_record_menu = fuente.render(f"MAXIMA SUPERVIVENCIA: {record_maximo} DÍAS", True, (255, 255, 255))

            pantalla.blit(texto_tit, (ANCHO // 2 - texto_tit.get_width() // 2, ALTO // 4))
            pantalla.blit(texto_record_menu, (ANCHO // 2 - texto_record_menu.get_width() // 2, ALTO // 2 - 20))
            pantalla.blit(texto_instrucciones, (ANCHO // 2 - texto_instrucciones.get_width() // 2, ALTO // 2 + 40))

        # ---------- PARTIDA ----------
        else:
            if not game_over:
                # Cambio de color de cielo
                if puntuacion > 30:
                    SABANA_FONDO = (17, 17, 255)

                # Parallax del fondo
                velocidad_fondo = velocidad_juego * 0.5
                fondo_x1 -= velocidad_fondo
                fondo_x2 -= velocidad_fondo
                if fondo_x1 <= -ANCHO:
                    fondo_x1 = fondo_x2 + ANCHO
                if fondo_x2 <= -ANCHO:
                    fondo_x2 = fondo_x1 + ANCHO

                leon.actualizar()
                velocidad_juego += 0.002
                frecuencia_obstaculo -= 1

                # Generación de obstáculos
                if frecuencia_obstaculo <= 0 and random.random() < 0.04:
                    tipo = random.choices(
                        ["roca", "arbusto", "bird"],
                        weights=[40, 25, 25]
                    )[0]

                    if tipo in ("roca", "arbusto") and random.random() < 0.3:
                        # Grupo de 1 o 2 obstáculos terrestres
                        cantidad = random.choice([1, 2])
                        espacio = 30
                        for i in range(cantidad):
                            x_inicial = ANCHO + i * (80 + espacio)
                            if tipo == "roca":
                                obstaculos.append(Roca(velocidad_juego, x_inicial))
                            else:
                                obstaculos.append(Arbusto(velocidad_juego, x_inicial))
                        frecuencia_obstaculo = 80 + (cantidad * 30)
                    else:
                        if tipo == "roca":
                            obstaculos.append(Roca(velocidad_juego))
                        elif tipo == "arbusto":
                            obstaculos.append(Arbusto(velocidad_juego))
                        else:  # bird
                            variant = random.randint(0, 1)
                            obstaculos.append(Bird(velocidad_juego, variant=variant))
                        frecuencia_obstaculo = 85

            # Actualizar y comprobar colisiones
            for obstaculo in obstaculos[:]:
                obstaculo.actualizar()

                if leon.obtener_rect().colliderect(obstaculo.obtener_rect()):
                    game_over = True
                    if pygame.mixer.get_init():
                        pygame.mixer.music.stop()

                    puntos_finales = int(puntuacion)
                    if puntos_finales > record_maximo:
                        record_maximo = puntos_finales
                        guardar_record(record_maximo)

                if obstaculo.fuera_de_pantalla():
                    obstaculos.remove(obstaculo)
                    puntuacion += 0.5

            # --- DIBUJADO ---
            pantalla.fill(SABANA_FONDO)
            pantalla.blit(IMAGEN_FONDO, (fondo_x1, 200))
            pantalla.blit(IMAGEN_FONDO, (fondo_x2, 200))

            # Suelo
            pygame.draw.rect(pantalla, SUELO_COLOR, (0, ALTURA_SUELO, ANCHO, ALTO - ALTURA_SUELO))

            leon.dibujar(pantalla)
            for obstaculo in obstaculos:
                obstaculo.dibujar(pantalla)

            # HUD
            texto_puntos = fuente.render(f"DIAS DE GESTION: {int(puntuacion)}", True, TEXTO_COLOR)
            texto_record_vivo = fuente.render(f"RÉCORD: {record_maximo}", True, (50, 50, 50))
            pantalla.blit(texto_puntos, (10, 10))
            pantalla.blit(texto_record_vivo, (ANCHO - texto_record_vivo.get_width() - 10, 10))

            # Créditos (fuente más pequeña para que entre bien)
            fuente_creditos = pygame.font.SysFont("Orbitron", 16)
            texto_creditos = fuente_creditos.render("Hecho con amor junto con Grok", True,
                                                    (180, 180, 180))
            pantalla.blit(texto_creditos, (ANCHO // 2 - texto_creditos.get_width() // 2, ALTO - 28))


            if game_over:
                texto_fin = fuente_grande.render("¡VOLTEADO POR KUKAS!", True, (139, 0, 0))
                texto_reiniciar = fuente.render("Presiona ESPACIO para volver a rugir", True, TEXTO_COLOR)
                pantalla.blit(texto_fin, (ANCHO // 2 - texto_fin.get_width() // 2, ALTO // 2 - 50))
                pantalla.blit(texto_reiniciar, (ANCHO // 2 - texto_reiniciar.get_width() // 2, ALTO // 2 + 10))

        pygame.display.flip()
        reloj.tick(FPS)
        await asyncio.sleep(0)  # Obligatorio para pygbag

# Punto de entrada para pygbag
if __name__ == "__main__":
    asyncio.run(main())

