"""Лабораторная работа 4: «Основы работы с 3D-графикой в OpenGL».
Сцена: домик (стены-куб + крыша-пирамида + дверь + труба) на лужайке.

Установка:  pip install pygame PyOpenGL PyOpenGL_accelerate
Запуск:     python lab4_opengl.py

Управление:
  ← → ↑ ↓      вращение сцены по осям Y и X
  Q / E        вращение по оси Z
  W / S, + / - приближение / отдаление камеры (также колесо мыши)
  Мышь (ЛКМ)   вращение сцены зажатой кнопкой
  ПРОБЕЛ       вкл/выкл автоматическое вращение
  L            вкл/выкл освещение
  T            вкл/выкл текстуру
  F            каркас / сплошные грани
  O            вкл/выкл облёт источника света вокруг сцены (индивидуальное задание)
  ESC          выход
"""
import math
import os
import sys

import pygame
from pygame.locals import (DOUBLEBUF, OPENGL, QUIT, KEYDOWN, MOUSEMOTION, MOUSEWHEEL,
                           K_ESCAPE, K_SPACE, K_l, K_t, K_f, K_o, K_LEFT, K_RIGHT,
                           K_UP, K_DOWN, K_q, K_e, K_w, K_s, K_PLUS, K_EQUALS, K_MINUS,
                           K_KP_PLUS, K_KP_MINUS)
from OpenGL.GL import *
from OpenGL.GLU import *

WIDTH, HEIGHT = 1000, 700
HERE = os.path.dirname(os.path.abspath(__file__))
TEXTURE_FILE = os.path.join(HERE, "brick.png")


# ======================= Текстура =======================
def make_texture_file(path):
    """Если файла текстуры нет — создаём кирпичную текстуру .png (светлую, чтобы цвет граней был виден)."""
    if os.path.exists(path):
        return
    size, brick_h, brick_w = 128, 16, 32
    surf = pygame.Surface((size, size))
    surf.fill((250, 250, 250))                      # раствор
    for row in range(size // brick_h):
        offset = (brick_w // 2) if row % 2 else 0
        for col in range(-1, size // brick_w + 1):
            x = col * brick_w + offset
            shade = 215 + ((row * 7 + col * 13) % 3) * 12
            pygame.draw.rect(surf, (shade, shade - 25, shade - 50),
                             (x + 2, row * brick_h + 2, brick_w - 3, brick_h - 3))
    pygame.image.save(surf, path)


def load_texture(path):
    surf = pygame.image.load(path)
    w, h = surf.get_size()
    to_bytes = getattr(pygame.image, "tobytes", None) or pygame.image.tostring
    data = to_bytes(surf, "RGBA", True)
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    return tex_id


# ======================= Геометрия =======================
def face_normal(a, b, c):
    """Нормаль грани по трём вершинам (векторное произведение, нормализованное)."""
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    length = math.sqrt(sum(x * x for x in n)) or 1.0
    return [x / length for x in n]


PASTEL = [(1.0, 0.55, 0.55), (0.55, 1.0, 0.55), (0.6, 0.6, 1.0),
          (1.0, 1.0, 0.5), (1.0, 0.6, 1.0), (0.5, 1.0, 1.0)]
TEX_UV = [(0, 0), (1, 0), (1, 1), (0, 1)]


def draw_box(hx, hy, hz, colors, textured=False, uv_scale=1.0):
    """Параллелепипед с центром в (0,0,0). У каждой грани свой цвет, нормаль и текстурные координаты."""
    faces = [
        [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)],        # перед  +Z
        [(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)],    # зад    -Z
        [(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)],        # право  +X
        [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)],    # лево   -X
        [(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)],        # верх   +Y
        [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)],    # низ    -Y
    ]
    glBegin(GL_QUADS)
    for i, quad in enumerate(faces):
        glColor3f(*colors[i % len(colors)])
        glNormal3f(*face_normal(quad[0], quad[1], quad[2]))
        for j, v in enumerate(quad):
            if textured:
                glTexCoord2f(TEX_UV[j][0] * uv_scale, TEX_UV[j][1] * uv_scale)
            glVertex3f(*v)
    glEnd()


def draw_pyramid(half_base, height, colors):
    """Четырёхгранная пирамида: основание в плоскости y=0, вершина (0, height, 0)."""
    b = half_base
    A, B, C, D = (-b, 0, b), (b, 0, b), (b, 0, -b), (-b, 0, -b)
    apex = (0, height, 0)
    glBegin(GL_TRIANGLES)
    for i, (p, q) in enumerate([(A, B), (B, C), (C, D), (D, A)]):
        glColor3f(*colors[i % len(colors)])
        glNormal3f(*face_normal(p, q, apex))
        glVertex3f(*p); glVertex3f(*q); glVertex3f(*apex)
    glEnd()
    glBegin(GL_QUADS)                       # основание (смотрит вниз)
    glColor3f(*colors[-1])
    glNormal3f(0, -1, 0)
    for v in (D, C, B, A):
        glVertex3f(*v)
    glEnd()


def draw_ground(size):
    glBegin(GL_QUADS)
    glColor3f(0.30, 0.62, 0.30)
    glNormal3f(0, 1, 0)
    for x, z in ((-size, size), (size, size), (size, -size), (-size, -size)):
        glVertex3f(x, 0, z)
    glEnd()


def draw_scene(textured, tex_id):
    """Составная фигура: домик. Все детали позиционируются смещениями относительно основания."""
    draw_ground(4)

    # стены (куб с текстурой и разноцветными гранями)
    glPushMatrix()
    glTranslatef(0, 0.8, 0)
    if textured:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
    draw_box(1.0, 0.8, 1.0, PASTEL, textured, uv_scale=2.0)
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

    # крыша (пирамида)
    glPushMatrix()
    glTranslatef(0, 1.6, 0)
    draw_pyramid(1.45, 1.0, [(0.75, 0.2, 0.15), (0.65, 0.15, 0.12),
                             (0.75, 0.2, 0.15), (0.65, 0.15, 0.12), (0.4, 0.1, 0.1)])
    glPopMatrix()

    # дверь
    glPushMatrix()
    glTranslatef(0, 0.45, 1.03)
    draw_box(0.25, 0.45, 0.04, [(0.4, 0.25, 0.1)])
    glPopMatrix()

    # окно
    glPushMatrix()
    glTranslatef(0.62, 0.95, 1.03)
    draw_box(0.2, 0.2, 0.03, [(0.6, 0.85, 1.0)])
    glPopMatrix()

    # труба (текстурированная)
    glPushMatrix()
    glTranslatef(0.65, 2.05, -0.45)
    if textured:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
    draw_box(0.18, 0.4, 0.18, [(1.0, 0.8, 0.7)], textured)
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()


# ======================= Свет и настройки =======================
def setup_gl():
    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 100.0)       # перспективная проекция
    glMatrixMode(GL_MODELVIEW)

    glClearColor(0.53, 0.75, 0.93, 1.0)
    glEnable(GL_DEPTH_TEST)                              # буфер глубины
    glDepthFunc(GL_LESS)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)

    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.7, 0.7, 0.7, 1.0))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 40.0)

    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.25, 0.25, 0.25, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 0.95, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_FALSE)


def draw_light_marker(pos):
    """Маленькая жёлтая сфера в позиции источника света (без освещения)."""
    glDisable(GL_LIGHTING)
    glDisable(GL_CULL_FACE)
    glPushMatrix()
    glTranslatef(*pos)
    glColor3f(1.0, 0.95, 0.2)
    q = gluNewQuadric()
    gluSphere(q, 0.12, 16, 16)
    gluDeleteQuadric(q)
    glPopMatrix()
    glEnable(GL_CULL_FACE)


# ======================= Главный цикл =======================
def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Лабораторная 4 — OpenGL")
    clock = pygame.time.Clock()

    setup_gl()
    make_texture_file(TEXTURE_FILE)
    tex_id = load_texture(TEXTURE_FILE)

    rot_x, rot_y, rot_z = 20.0, -30.0, 0.0
    dist = 9.0
    auto_rotate = lighting = textured = True
    wireframe = False
    light_orbit = True
    light_angle = 45.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for e in pygame.event.get():
            if e.type == QUIT:
                running = False
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False
                elif e.key == K_SPACE:
                    auto_rotate = not auto_rotate
                elif e.key == K_l:
                    lighting = not lighting
                elif e.key == K_t:
                    textured = not textured
                elif e.key == K_f:
                    wireframe = not wireframe
                elif e.key == K_o:
                    light_orbit = not light_orbit
            elif e.type == MOUSEMOTION and e.buttons[0]:     # вращение мышью
                rot_y += e.rel[0] * 0.4
                rot_x += e.rel[1] * 0.4
            elif e.type == MOUSEWHEEL:
                dist = max(3.0, min(25.0, dist - e.y * 0.6))

        keys = pygame.key.get_pressed()
        speed = 90 * dt
        if keys[K_LEFT]:  rot_y -= speed
        if keys[K_RIGHT]: rot_y += speed
        if keys[K_UP]:    rot_x -= speed
        if keys[K_DOWN]:  rot_x += speed
        if keys[K_q]:     rot_z -= speed
        if keys[K_e]:     rot_z += speed
        if keys[K_w] or keys[K_PLUS] or keys[K_EQUALS] or keys[K_KP_PLUS]:
            dist = max(3.0, dist - 6 * dt)
        if keys[K_s] or keys[K_MINUS] or keys[K_KP_MINUS]:
            dist = min(25.0, dist + 6 * dt)

        if auto_rotate:
            rot_y += 25 * dt                                  # автоматическое вращение
        if light_orbit:
            light_angle += 50 * dt
        la = math.radians(light_angle)
        light_pos = (4.0 * math.cos(la), 3.5, 4.0 * math.sin(la))

        # ---------- отрисовка ----------
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, -1.3, -dist)                          # камера

        if lighting:
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glLightfv(GL_LIGHT0, GL_POSITION, (*light_pos, 1.0))   # точечный источник
        else:
            glDisable(GL_LIGHTING)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)

        glPushMatrix()
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)
        glRotatef(rot_z, 0, 0, 1)
        draw_scene(textured and not wireframe, tex_id)
        glPopMatrix()

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        if lighting:
            draw_light_marker(light_pos)

        pygame.display.set_caption(
            f"Лаб. 4 — OpenGL | FPS {clock.get_fps():.0f} | свет:{'вкл' if lighting else 'выкл'} "
            f"текстура:{'вкл' if textured else 'выкл'} каркас:{'вкл' if wireframe else 'выкл'}")
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
