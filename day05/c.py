import turtle as t

t.bgcolor('black')
t.setup(500, 500)
t.speed(0)

def m(n, radius, col):
    for x in range(n):
        t.color(col)
        t.circle(radius)
        t.left(360/n)

m(70, 90, 'yellow')
m(50, 60, 'red')
m(30, 30, 'green')

t.mainloop()