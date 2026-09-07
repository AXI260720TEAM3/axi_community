import turtle as t
import random as r

t.setup(500, 500)
t.shape('turtle')
t.bgcolor('black')
t.speed(0)
t.pensize(2)

colors = ['yellow', 'green', 'blue', 'red']
for x in range(300):
    c = r.choice(colors) #랜덤 컬러 
    t.color(c)
    a = r.randint(1, 360) #랜덤 각도
    t.setheading(a)
    d = r.randint(3, 30) #랜덤 거리
    t.forward(d)

t.mainloop()