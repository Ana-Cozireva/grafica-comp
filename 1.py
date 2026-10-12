import turtle

t = turtle.Turtle()
t.shape('turtle')

screen = turtle.Screen()
t.speed(50)


def up():
    t.setheading(90)
    t.forward(5)


def down():
    t.setheading(270)
    t.forward(5)


def left():
    t.setheading(180)
    t.forward(5)


def right():
    t.setheading(0)
    t.forward(5)


def toggle_pen():
    if t.isdown():
        t.penup()
    else:
        t.pendown()


screen.listen()
screen.onkey(up, "Up")
screen.onkey(down, "Down")
screen.onkey(left, "Left")
screen.onkey(right, "Right")
screen.onkey(toggle_pen, "space")

screen.mainloop()
