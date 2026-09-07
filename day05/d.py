import turtle as t

t.bgcolor('black')
t.setup(500, 500)
t.speed(0)
t.color('yellow')

for x in range(300): #0, .. , 299
    t.forward(x)
    t.left(89)

t.mainloop()