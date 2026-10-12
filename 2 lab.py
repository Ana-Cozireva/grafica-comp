"""Лабораторная работа 2: «Геометрические фракталы».
Кривая Чезаро (Ana) — модификация кривой Коха: на средней трети каждого отрезка строится
не правильный треугольник (угол при вершине 60°), а более острый зубец (угол < 60°).

Запуск:  python ana_fractal.py        (нужен только стандартный tkinter, установка не требуется)
         python ana_fractal.py 4      (необязательно: задать N в командной строке)

Управление:
  + / = / ↑   увеличить глубину N          - / ↓   уменьшить глубину N
  ] / [       увеличить / уменьшить угол зубца (индивидуальное задание)
  I           сменить инициатор: треугольник → квадрат → отрезок
  Слайдеры в нижней панели делают то же самое.
"""
import math
import sys
import tkinter as tk
from tkinter import simpledialog

MAX_N = 7                  # защита от зависания: при N=7 у треугольника 3·4^7 = 49152 отрезка
DEFAULT_N = 3              # глубина по умолчанию (оценка 6: N = 3..4 задано переменной)
DEFAULT_ANGLE = 40         # угол при вершине зубца, градусы (< 60°)
MIN_ANGLE, MAX_ANGLE = 40, 59   # при меньших углах кривая начинает самопересекаться
MARGIN = 40

# Цвет зависит от уровня рекурсии, на котором появился элемент (0 — исходная фигура)
LEVEL_COLORS = ["#ffffff", "#ff5252", "#ffb74d", "#ffee58", "#66bb6a",
                "#29b6f6", "#7e57c2", "#ec407a"]


# ===================== ИНИЦИАТОРЫ (начальные фигуры) =====================
def initiator(kind):
    """Возвращает вершины замкнутой ломаной (или отрезка) в порядке обхода ПРОТИВ часовой стрелки
    (в математической системе координат, ось Y вверх) — тогда зубцы строятся наружу."""
    if kind == "triangle":
        return [(0, 0), (1, 0), (0.5, math.sqrt(3) / 2)], True
    if kind == "square":
        return [(0, 0), (1, 0), (1, 1), (0, 1)], True
    return [(1, 0), (0, 0)], False                      # одиночный отрезок


NAMES = {"triangle": "треугольник", "square": "квадрат", "segment": "отрезок"}
ORDER = ["triangle", "square", "segment"]


# ===================== РЕКУРСИВНОЕ ПОСТРОЕНИЕ =====================
def cesaro(a, b, level, n, color, alpha, out):
    """Строит кривую Чезаро для отрезка a→b.

    level — текущий уровень рекурсии, n — требуемая глубина,
    color — индекс цвета отрезка, out — список результата [(a, b, color), ...].
    """
    # ---- УСЛОВИЕ ВЫХОДА ИЗ РЕКУРСИИ: достигнута нужная глубина (при n = 0 рисуется только инициатор)
    if level == n:
        out.append((a, b, color))
        return

    # ---- БАЗОВЫЙ ШАГ АЛГОРИТМА: делим отрезок на три части и строим зубец на средней
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    p = (a[0] + dx / 3, a[1] + dy / 3)                  # начало зубца
    q = (a[0] + 2 * dx / 3, a[1] + 2 * dy / 3)          # конец зубца
    # высота равнобедренного треугольника с основанием |pq| = L/3 и углом при вершине alpha
    h = (length / 6) / math.tan(alpha / 2)
    nx, ny = dy / length, -dx / length                  # единичная нормаль (наружу)
    t = ((a[0] + b[0]) / 2 + nx * h, (a[1] + b[1]) / 2 + ny * h)   # вершина зубца

    # ---- РЕКУРСИВНЫЙ ВЫЗОВ для каждого из 4 новых отрезков
    new_color = min(level + 1, len(LEVEL_COLORS) - 1)   # стороны зубца — цвет нового уровня
    cesaro(a, p, level + 1, n, color, alpha, out)       # левая часть — наследует цвет
    cesaro(p, t, level + 1, n, new_color, alpha, out)   # левая сторона зубца
    cesaro(t, q, level + 1, n, new_color, alpha, out)   # правая сторона зубца
    cesaro(q, b, level + 1, n, color, alpha, out)       # правая часть — наследует цвет


def build(kind, n, alpha_deg):
    """Строит все отрезки фигуры для заданных инициатора, глубины и угла."""
    verts, closed = initiator(kind)
    edges = len(verts) if closed else len(verts) - 1
    out = []
    for i in range(edges):
        cesaro(verts[i], verts[(i + 1) % len(verts)], 0, n, 0, math.radians(alpha_deg), out)
    return out


# ===================== ПРИЛОЖЕНИЕ =====================
class App:
    def __init__(self, root, n0):
        self.root = root
        self.kind = "triangle"
        self.n = n0
        self.angle = DEFAULT_ANGLE
        self._job = None
        root.title("Кривая Чезаро (Ana)")

        self.canvas = tk.Canvas(root, bg="#101820", highlightthickness=0, width=900, height=640)
        self.canvas.pack(fill="both", expand=True)

        panel = tk.Frame(root)
        panel.pack(fill="x")
        self.info = tk.Label(panel, font=("Arial", 12, "bold"), anchor="w")
        self.info.pack(fill="x", padx=8, pady=(4, 0))
        self.n_scale = tk.Scale(panel, from_=0, to=MAX_N, orient="horizontal", label="Глубина N",
                                command=self.on_n)
        self.n_scale.set(n0)
        self.n_scale.pack(side="left", fill="x", expand=True, padx=8)
        self.a_scale = tk.Scale(panel, from_=MIN_ANGLE, to=MAX_ANGLE, orient="horizontal",
                                label="Угол зубца, °", command=self.on_angle)
        self.a_scale.set(DEFAULT_ANGLE)
        self.a_scale.pack(side="left", fill="x", expand=True, padx=8)

        root.bind("<plus>", lambda e: self.change_n(+1))
        root.bind("<equal>", lambda e: self.change_n(+1))
        root.bind("<KP_Add>", lambda e: self.change_n(+1))
        root.bind("<Up>", lambda e: self.change_n(+1))
        root.bind("<minus>", lambda e: self.change_n(-1))
        root.bind("<KP_Subtract>", lambda e: self.change_n(-1))
        root.bind("<Down>", lambda e: self.change_n(-1))
        root.bind("<bracketright>", lambda e: self.a_scale.set(min(MAX_ANGLE, self.angle + 1)))
        root.bind("<bracketleft>", lambda e: self.a_scale.set(max(MIN_ANGLE, self.angle - 1)))
        root.bind("<i>", lambda e: self.next_initiator())
        root.bind("<I>", lambda e: self.next_initiator())
        self.canvas.bind("<Configure>", lambda e: self.schedule())
        self.redraw()

    # --- обработчики ввода ---
    def change_n(self, d):
        self.n_scale.set(max(0, min(MAX_N, self.n + d)))     # ограничение глубины

    def on_n(self, value):
        self.n = int(float(value)); self.schedule()

    def on_angle(self, value):
        self.angle = int(float(value)); self.schedule()

    def next_initiator(self):
        self.kind = ORDER[(ORDER.index(self.kind) + 1) % len(ORDER)]
        self.schedule()

    def schedule(self):
        """Откладываем перерисовку, чтобы не строить фигуру много раз подряд."""
        if self._job:
            self.root.after_cancel(self._job)
        self._job = self.root.after(30, self.redraw)

    # --- отрисовка ---
    def redraw(self):
        self._job = None
        segs = build(self.kind, self.n, self.angle)
        xs = [p[0] for s in segs for p in s[:2]]
        ys = [p[1] for s in segs for p in s[:2]]
        w, h = max(self.canvas.winfo_width(), 100), max(self.canvas.winfo_height(), 100)
        bw, bh = max(max(xs) - min(xs), 1e-9), max(max(ys) - min(ys), 1e-9)
        # фигура полностью помещается в окно: масштаб по ограничивающему прямоугольнику
        k = min((w - 2 * MARGIN) / bw, (h - 2 * MARGIN) / bh)
        ox = (w - bw * k) / 2 - min(xs) * k
        oy = (h + bh * k) / 2 + min(ys) * k                  # ось Y экрана направлена вниз

        def to_screen(p):
            return ox + p[0] * k, oy - p[1] * k

        c = self.canvas
        c.delete("all")
        width = 2 if len(segs) < 3000 else 1
        for a, b, col in segs:
            x1, y1 = to_screen(a); x2, y2 = to_screen(b)
            c.create_line(x1, y1, x2, y2, fill=LEVEL_COLORS[col], width=width)

        # легенда уровней
        for i in range(min(self.n, len(LEVEL_COLORS) - 1) + 1):
            c.create_rectangle(10, 10 + i * 18, 24, 22 + i * 18, fill=LEVEL_COLORS[i], outline="")
            c.create_text(30, 16 + i * 18, anchor="w", fill="#cfd8dc", font=("Arial", 10),
                          text="инициатор" if i == 0 else f"уровень {i}")

        self.info.config(text=f"N = {self.n}   |   элементов (отрезков): {len(segs)}   |   "
                              f"инициатор: {NAMES[self.kind]}   |   угол зубца: {self.angle}°")


def ask_depth():
    """Ввод глубины N пользователем перед запуском построения (окно ввода)."""
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return max(0, min(MAX_N, int(sys.argv[1])))
    tmp = tk.Tk(); tmp.withdraw()
    n = simpledialog.askinteger("Глубина рекурсии", f"Введите N (0…{MAX_N}):",
                                initialvalue=DEFAULT_N, minvalue=0, maxvalue=MAX_N, parent=tmp)
    tmp.destroy()
    return DEFAULT_N if n is None else n


def main():
    n0 = ask_depth()
    root = tk.Tk()
    App(root, n0)
    root.mainloop()


if __name__ == "__main__":
    main()
