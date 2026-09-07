import turtle as t

t.setup(500, 500)
t.shape('turtle')
t.bgcolor('black')
t.speed(0)
t.color('white')

for x in range(300):
    if x%3 == 0:
        t.color('red')
    if x%3 == 1:
        t.color('green')
    if x%3 == 2:
        t.color('yellow')

    t.forward(x)
    t.left(119)

t.mainloop()