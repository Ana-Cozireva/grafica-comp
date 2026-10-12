"""Контрольная работа: 2D-векторная графика и составная анимация. Вариант 4 — Вертолёт.
Запуск:  pip install pygame  ->  python helicopter.py
Управление: A/D или стрелки влево/вправо — полёт и разворот,
            W/S или стрелки вверх/вниз — высота, ПРОБЕЛ — сброс груза.
"""
import math
import pygame

W, H = 900, 500
GROUND = H - 30

# ---------- Относительные смещения дочерних примитивов (от центра корпуса) ----------
PARTS = {
    "body":       {"rx": 50, "ry": 30},                           # корпус (эллипс)
    "cockpit":    {"dx": 22, "dy": -6, "rx": 20, "ry": 14},       # кабина
    "boom":       {"dx": -120, "dy": -8, "w": 100, "h": 10},      # хвостовая балка (прямоугольник)
    "fin":        [(-120, -8), (-134, -34), (-124, -34), (-108, -8)],  # киль (полигон)
    "mast":       {"dx": 0, "dy": -30, "h": 12},                  # мачта (линия)
    "main_rotor": {"dx": 0, "dy": -42, "len": 110, "thick": 4},   # несущий винт
    "tail_rotor": {"dx": -128, "dy": -22, "len": 24, "thick": 3}, # хвостовой винт
    "skid":       {"dx": -34, "dy": 44, "w": 80},                 # полоз
    "struts_x":   [-22, 22],                                      # стойки шасси
    "hook":       {"dx": 0, "dy": 34},                            # точка сброса груза
}

# цвета
SKY_TOP, SKY_BOTTOM = (109, 179, 232), (207, 233, 247)
GRASS = (78, 143, 74)
RED, DARK_RED, BLUE_GRAY = (214, 69, 65), (192, 57, 43), (74, 106, 138)
GLASS, BLACK = (159, 216, 245), (43, 47, 54)


def ellipse_points(cx, cy, rx, ry, n=36):
    """Эллипс как полигон (чтобы его можно было поворачивать и отражать)."""
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


class Helicopter:
    MAX_V = 320.0   # максимальная скорость, px/s
    ACC = 520.0     # ускорение
    FRIC = 380.0    # торможение (инерция)
    HALF_W = 135    # габарит для границ экрана

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.facing = 1          # 1 — вправо, -1 — влево (зеркало по горизонтали)
        self.phase = 0.0         # фаза вращения винтов

    # --- преобразование локальных (относительных) координат в мировые ---
    def tf(self, p):
        x, y = p[0] * self.facing, p[1]              # зеркальное отражение
        a = self.facing * (self.vx / self.MAX_V) * 0.15  # наклон при разгоне
        c, s = math.cos(a), math.sin(a)
        return (self.x + x * c - y * s, self.y + x * s + y * c)

    def hook_world(self):
        return self.tf((PARTS["hook"]["dx"], PARTS["hook"]["dy"]))

    @staticmethod
    def _approach_zero(v, step):
        return v - math.copysign(min(abs(v), step), v) if v else 0.0

    def update(self, dt, keys):
        dir_x = (keys["right"] - keys["left"])
        dir_y = (keys["down"] - keys["up"])
        if dir_x:
            self.facing = dir_x
            self.vx += dir_x * self.ACC * dt
        else:
            self.vx = self._approach_zero(self.vx, self.FRIC * dt)
        if dir_y:
            self.vy += dir_y * self.ACC * dt
        else:
            self.vy = self._approach_zero(self.vy, self.FRIC * dt)
        self.vx = max(-self.MAX_V, min(self.MAX_V, self.vx))
        self.vy = max(-self.MAX_V, min(self.MAX_V, self.vy))
        self.x += self.vx * dt
        self.y += self.vy * dt

        # границы экрана
        if self.x < self.HALF_W:
            self.x, self.vx = self.HALF_W, 0.0
        if self.x > W - self.HALF_W:
            self.x, self.vx = W - self.HALF_W, 0.0
        if self.y < 70:
            self.y, self.vy = 70, 0.0
        if self.y > GROUND - 50:
            self.y, self.vy = GROUND - 50, 0.0

        # анимация винтов: скорость ∝ скорости корпуса, в покое — исходное положение
        speed = math.hypot(self.vx, self.vy)
        if speed < 2:
            self.phase = 0.0
        else:
            self.phase += (speed / self.MAX_V) * 40 * dt

    def draw(self, surf):
        P, tf = PARTS, self.tf

        # хвостовая балка (прямоугольник -> полигон)
        b = P["boom"]
        rect = [(b["dx"], b["dy"]), (b["dx"] + b["w"], b["dy"]),
                (b["dx"] + b["w"], b["dy"] + b["h"]), (b["dx"], b["dy"] + b["h"])]
        pygame.draw.polygon(surf, BLUE_GRAY, [tf(p) for p in rect])
        # киль
        pygame.draw.polygon(surf, DARK_RED, [tf(p) for p in P["fin"]])
        # корпус
        bd = P["body"]
        pygame.draw.polygon(surf, RED, [tf(p) for p in ellipse_points(0, 0, bd["rx"], bd["ry"])])
        # кабина
        c = P["cockpit"]
        pygame.draw.polygon(surf, GLASS, [tf(p) for p in ellipse_points(c["dx"], c["dy"], c["rx"], c["ry"])])
        # шасси
        sk = P["skid"]
        for sx in P["struts_x"]:
            pygame.draw.line(surf, BLACK, tf((sx, 24)), tf((sx, sk["dy"])), 3)
        pygame.draw.line(surf, BLACK, tf((sk["dx"], sk["dy"])), tf((sk["dx"] + sk["w"], sk["dy"])), 3)
        # мачта
        m = P["mast"]
        pygame.draw.line(surf, BLACK, tf((m["dx"], m["dy"])), tf((m["dx"], m["dy"] - m["h"])), 3)

        # несущий винт: длина линии меняется как |cos(phase)| (имитация вращения)
        mr = P["main_rotor"]
        ml = mr["len"] * math.cos(self.phase)
        pygame.draw.line(surf, BLACK, tf((mr["dx"] - ml, mr["dy"])), tf((mr["dx"] + ml, mr["dy"])), mr["thick"])

        # хвостовой винт: линия вращается вокруг ступицы
        tr = P["tail_rotor"]
        a = math.pi / 2 + self.phase * 1.5
        ox, oy = math.cos(a) * tr["len"], math.sin(a) * tr["len"]
        pygame.draw.line(surf, BLACK, tf((tr["dx"] - ox, tr["dy"] - oy)),
                         tf((tr["dx"] + ox, tr["dy"] + oy)), tr["thick"])

        # ступицы винтов
        for hub in ((mr["dx"], mr["dy"]), (tr["dx"], tr["dy"])):
            pygame.draw.circle(surf, BLACK, tf(hub), 4)


class Cargo:
    G = 900.0

    def __init__(self, x, y, vx):
        self.x, self.y, self.vx, self.vy = x, y, vx, 0.0
        self.w, self.h = 22, 18
        self.landed = 0.0

    def update(self, dt):
        if self.y + self.h < GROUND:
            self.vy += self.G * dt           # гравитация
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.y + self.h >= GROUND:
                self.y, self.vx, self.vy = GROUND - self.h, 0.0, 0.0
        else:
            self.landed += dt

    def draw(self, surf):
        r = pygame.Rect(int(self.x - self.w / 2), int(self.y), self.w, self.h)
        pygame.draw.rect(surf, (183, 121, 31), r)
        pygame.draw.rect(surf, (123, 74, 15), r, 2)
        pygame.draw.line(surf, (123, 74, 15), r.midleft, r.midright, 2)


def draw_background(surf):
    for y in range(H):  # вертикальный градиент неба
        t = y / H
        col = tuple(int(SKY_TOP[i] + (SKY_BOTTOM[i] - SKY_TOP[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (W, y))
    pygame.draw.rect(surf, GRASS, (0, GROUND, W, H - GROUND))


def draw_hud(surf, font, heli, dropped):
    panel = pygame.Surface((230, 58), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 140))
    surf.blit(panel, (10, 10))
    speed = math.hypot(heli.vx, heli.vy)
    surf.blit(font.render(f"Скорость: {speed:.0f} px/s", True, (255, 255, 255)), (20, 16))
    surf.blit(font.render(f"Грузов сброшено: {dropped}", True, (255, 255, 255)), (20, 38))


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Вертолёт — 2D-примитивы")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 18)

    heli = Helicopter(W / 2, 200)
    cargos, dropped, cooldown = [], 0, 0.0

    running = True
    while running:
        dt = min(0.05, clock.tick(60) / 1000)
        cooldown -= dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and cooldown <= 0:
                hx, hy = heli.hook_world()
                cargos.append(Cargo(hx, hy + 6, heli.vx))
                dropped += 1
                cooldown = 0.35

        pressed = pygame.key.get_pressed()
        keys = {
            "left":  pressed[pygame.K_a] or pressed[pygame.K_LEFT],
            "right": pressed[pygame.K_d] or pressed[pygame.K_RIGHT],
            "up":    pressed[pygame.K_w] or pressed[pygame.K_UP],
            "down":  pressed[pygame.K_s] or pressed[pygame.K_DOWN],
        }
        keys = {k: int(bool(v)) for k, v in keys.items()}

        heli.update(dt, keys)
        for c in cargos:
            c.update(dt)
        cargos = [c for c in cargos if c.landed < 4.0]

        draw_background(screen)
        for c in cargos:
            c.draw(screen)
        heli.draw(screen)
        draw_hud(screen, font, heli, dropped)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
