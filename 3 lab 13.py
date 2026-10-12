#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лабораторная работа 3. «Алгебраические фракталы»
Рациональный фрактал «Симонброт» (Simonbrot)

Итерация:   z(0) = 0,   z(n+1) = z(n)^2 * |z(n)| + c
Точка c принадлежит множеству, если орбита не выходит за круг |z| <= 2
за MAX_ITER шагов. Выход: x^2 + y^2 > 4.

Нужно: Python 3 + numpy  (pip install numpy). tkinter входит в стандартную поставку.

Управление:
    ЛКМ            - увеличить масштаб в 2 раза вокруг курсора
    ПКМ / колесо   - уменьшить / увеличить масштаб
    + / -          - число итераций +50 / -50 (]/[ - ×2 / ÷2)
    стрелки        - сдвиг изображения
    R (или Home)   - сброс масштаба в исходное состояние
    B              - чёрно-белый режим / цветной режим
    P              - сменить палитру (индивидуальное задание)
    C / V          - сдвиг цветов по палитре (индивидуальное задание)
    S              - сохранить изображение в PNG (индивидуальное задание)
    H              - показать / скрыть панель параметров
"""

import sys
import time
import tkinter as tk
from tkinter import simpledialog

import numpy as np

# ------------------------------ Параметры --------------------------------
WIDTH = HEIGHT = 720          # размер окна фиксирован (квадрат => пропорции не искажаются)
DEFAULT_ITER = 100            # число итераций по умолчанию (если пользователь не ввёл своё)
MIN_ITER, MAX_ITER_LIMIT = 10, 20000
START_CENTER = (-0.35, 0.0)   # начальный центр области комплексной плоскости
START_SPAN = 3.4              # начальная ширина области (и высота - она такая же)
BAILOUT2 = 4.0                # условие выхода: x^2 + y^2 > 4

# Палитры: 3-4 опорных цвета, между ними - плавный градиент (последний = первому для цикличности)
PALETTES = {
    "Океан":  [(0, 7, 100), (32, 107, 203), (237, 255, 255), (255, 170, 0)],
    "Огонь":  [(20, 0, 0), (200, 40, 0), (255, 200, 40), (255, 255, 220)],
    "Лес":    [(0, 30, 10), (20, 140, 60), (200, 240, 120), (250, 250, 230)],
    "Неон":   [(20, 0, 60), (200, 0, 200), (0, 220, 255), (255, 255, 120)],
}
LUT_SIZE = 1024


def make_lut(colors):
    """Строит таблицу цветов LUT_SIZE x 3 с плавным циклическим градиентом."""
    pts = colors + [colors[0]]                     # замыкаем цикл
    seg = len(pts) - 1
    lut = np.zeros((LUT_SIZE, 3), dtype=np.float64)
    for i in range(LUT_SIZE):
        t = i / LUT_SIZE * seg
        k = int(t)
        f = t - k
        f = f * f * (3 - 2 * f)                    # сглаживание (smoothstep)
        a, b = np.array(pts[k]), np.array(pts[k + 1])
        lut[i] = a + (b - a) * f
    return lut.astype(np.uint8)


# ----------------------------- Вычисление --------------------------------
def compute(center, span, max_iter, w=WIDTH, h=HEIGHT):
    """
    Возвращает массив float размера (h, w): «непрерывный» номер итерации выхода
    или -1 для точек, оставшихся внутри множества.
    Пиксели квадратные: шаг по x и y одинаков, поэтому пропорции сохраняются.
    """
    step = span / w
    xs = center[0] + (np.arange(w) - w / 2 + 0.5) * step
    ys = center[1] - (np.arange(h) - h / 2 + 0.5) * step      # ось Y экрана направлена вниз
    c = (xs[None, :] + 1j * ys[:, None]).ravel()

    z = np.zeros_like(c)
    result = np.full(c.shape, -1.0)
    idx = np.arange(c.size)                                   # номера ещё «живых» точек
    cc = c.copy()

    for n in range(max_iter):
        # ----- сама формула Симонброта: z = z^2 * |z| + c -----
        z = z * z * np.abs(z) + cc
        # ----- условие выхода x^2 + y^2 > 4: запоминаем номер шага -----
        out = (z.real * z.real + z.imag * z.imag) > BAILOUT2
        if out.any():
            zo = z[out]
            # сглаживание: убирает «ступеньки» между соседними номерами итераций
            # (степень роста |z| за шаг равна 3, поэтому log base 3)
            nu = n + 1 - np.log(np.maximum(np.log(np.abs(zo)) / np.log(2.0), 1e-9)) / np.log(3.0)
            result[idx[out]] = np.maximum(nu, 0)
            keep = ~out                                       # вышедшие точки больше не считаем
            z, cc, idx = z[keep], cc[keep], idx[keep]
            if idx.size == 0:
                break
    return result.reshape(h, w)


def colorize(values, lut, bw, shift):
    """Превращает массив итераций в RGB-байты (PPM)."""
    inside = values < 0
    if bw:
        img = np.where(inside[..., None], 0, 255).astype(np.uint8)
        img = np.repeat(img, 3, axis=2) if img.shape[-1] == 1 else img
    else:
        idx = ((np.sqrt(np.maximum(values, 0)) * 90.0 + shift) % LUT_SIZE).astype(np.int64)   # 90 - «частота» циклов цвета
        img = lut[idx]
        img[inside] = (0, 0, 0)                                          # внутренность - чёрная
    return np.ascontiguousarray(img)


# ------------------------------ Приложение -------------------------------
class App:
    def __init__(self, root, max_iter):
        self.root = root
        root.title("Симонброт: z → z²·|z| + c")
        root.resizable(False, False)                           # фиксированный размер окна

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0, bg="black")
        self.canvas.pack()
        self.img_id = self.canvas.create_image(0, 0, anchor="nw")
        self.photo = None

        self.max_iter = max_iter
        self.center = list(START_CENTER)
        self.span = START_SPAN
        self.bw = False
        self.shift = 0
        self.show_hud = True
        self.pal_names = list(PALETTES)
        self.pal_i = 0
        self.luts = {k: make_lut(v) for k, v in PALETTES.items()}
        self.values = None
        self.mouse = (WIDTH // 2, HEIGHT // 2)
        self.last_time = 0.0

        c = self.canvas
        c.bind("<Button-1>", lambda e: self.zoom_at(e.x, e.y, 0.5))      # ЛКМ: приближение
        c.bind("<Button-3>", lambda e: self.zoom_at(e.x, e.y, 2.0))      # ПКМ: отдаление
        c.bind("<MouseWheel>", lambda e: self.zoom_at(e.x, e.y, 0.5 if e.delta > 0 else 2.0))
        c.bind("<Button-4>", lambda e: self.zoom_at(e.x, e.y, 0.5))      # колесо (Linux)
        c.bind("<Button-5>", lambda e: self.zoom_at(e.x, e.y, 2.0))
        c.bind("<Motion>", self.on_motion)

        for key in ("<plus>", "<KP_Add>", "<equal>"):
            root.bind(key, lambda e: self.change_iter(self.max_iter + 50))
        for key in ("<minus>", "<KP_Subtract>"):
            root.bind(key, lambda e: self.change_iter(self.max_iter - 50))
        root.bind("<bracketright>", lambda e: self.change_iter(self.max_iter * 2))
        root.bind("<bracketleft>", lambda e: self.change_iter(self.max_iter // 2))
        for key in ("r", "R", "<Home>", "<Cyrillic_ka>", "<Cyrillic_KA>"):
            root.bind(key, lambda e: self.reset())
        root.bind("<Left>", lambda e: self.pan(-0.2, 0))
        root.bind("<Right>", lambda e: self.pan(0.2, 0))
        root.bind("<Up>", lambda e: self.pan(0, 0.2))
        root.bind("<Down>", lambda e: self.pan(0, -0.2))
        for key in ("b", "B"):
            root.bind(key, lambda e: self.toggle_bw())
        for key in ("p", "P"):
            root.bind(key, lambda e: self.next_palette())
        for key in ("c", "C"):
            root.bind(key, lambda e: self.shift_colors(64))
        for key in ("v", "V"):
            root.bind(key, lambda e: self.shift_colors(-64))
        for key in ("s", "S"):
            root.bind(key, lambda e: self.save_png())
        for key in ("h", "H"):
            root.bind(key, lambda e: self.toggle_hud())

        self.render(recompute=True)

    # ---------- действия пользователя ----------
    def zoom_at(self, px, py, factor):
        """Центр области переносится в точку курсора, масштаб меняется в 1/factor раз."""
        step = self.span / WIDTH
        self.center[0] += (px - WIDTH / 2) * step
        self.center[1] -= (py - HEIGHT / 2) * step
        self.span = min(max(self.span * factor, 1e-13), 8.0)    # предел точности double
        self.render(True)

    def pan(self, dx, dy):
        self.center[0] += dx * self.span
        self.center[1] += dy * self.span
        self.render(True)

    def change_iter(self, n):
        n = max(MIN_ITER, min(MAX_ITER_LIMIT, n))
        if n != self.max_iter:
            self.max_iter = n
            self.render(True)

    def reset(self):
        """Быстрый сброс масштаба и положения в исходное состояние."""
        self.center = list(START_CENTER)
        self.span = START_SPAN
        self.render(True)

    def toggle_bw(self):
        self.bw = not self.bw
        self.render(False)

    def next_palette(self):
        self.pal_i = (self.pal_i + 1) % len(self.pal_names)
        self.bw = False
        self.render(False)

    def shift_colors(self, d):
        self.shift = (self.shift + d) % LUT_SIZE
        self.render(False)

    def toggle_hud(self):
        self.show_hud = not self.show_hud
        self.draw_hud()

    def save_png(self):
        name = time.strftime("simonbrot_%Y%m%d_%H%M%S.png")
        try:
            self.photo.write(name, format="png")
            self.last_msg = f"Сохранено: {name}"
        except tk.TclError:
            self.last_msg = "Сохранение PNG не поддерживается этой версией Tk"
        self.draw_hud()

    def on_motion(self, e):
        self.mouse = (e.x, e.y)
        self.draw_hud()

    # ---------- отрисовка ----------
    def render(self, recompute):
        if recompute or self.values is None:
            self.canvas.config(cursor="watch")
            self.root.update_idletasks()
            t0 = time.time()
            self.values = compute(self.center, self.span, self.max_iter)
            self.last_time = time.time() - t0
            self.canvas.config(cursor="")
        lut = self.luts[self.pal_names[self.pal_i]]
        rgb = colorize(self.values, lut, self.bw, self.shift)
        ppm = b"P6 %d %d 255\n" % (WIDTH, HEIGHT) + rgb.tobytes()
        self.photo = tk.PhotoImage(data=ppm, format="PPM")
        self.canvas.itemconfig(self.img_id, image=self.photo)
        self.last_msg = ""
        self.draw_hud()

    def draw_hud(self):
        """Панель параметров: масштаб, координаты центра, число итераций."""
        c = self.canvas
        c.delete("hud")
        if not self.show_hud:
            return
        step = self.span / WIDTH
        mx = self.center[0] + (self.mouse[0] - WIDTH / 2) * step
        my = self.center[1] - (self.mouse[1] - HEIGHT / 2) * step
        zoom = START_SPAN / self.span
        lines = [
            f"Масштаб: x{zoom:,.4g}",
            f"Центр: {self.center[0]:.10g} {self.center[1]:+.10g}i",
            f"Итераций: {self.max_iter}",
            f"Курсор: {mx:.8g} {my:+.8g}i",
            f"Расчёт: {self.last_time:.2f} с   Палитра: {'ч/б' if self.bw else self.pal_names[self.pal_i]}",
        ]
        if getattr(self, "last_msg", ""):
            lines.append(self.last_msg)
        c.create_rectangle(6, 6, 372, 12 + 18 * len(lines), fill="black", stipple="gray50",
                           outline="", tags="hud")
        for i, t in enumerate(lines):
            c.create_text(12, 10 + 18 * i, anchor="nw", text=t, fill="white",
                          font=("Consolas", 10), tags="hud")


def ask_iterations():
    """Окно ввода максимального числа итераций перед запуском (или аргумент командной строки)."""
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return int(sys.argv[1])
    tmp = tk.Tk()
    tmp.withdraw()
    n = simpledialog.askinteger("Симонброт", f"Максимальное число итераций ({MIN_ITER}..{MAX_ITER_LIMIT}):",
                                initialvalue=DEFAULT_ITER, minvalue=MIN_ITER,
                                maxvalue=MAX_ITER_LIMIT, parent=tmp)
    tmp.destroy()
    return n or DEFAULT_ITER


if __name__ == "__main__":
    iters = ask_iterations()
    root = tk.Tk()
    App(root, iters)
    root.mainloop()
