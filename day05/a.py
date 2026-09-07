import turtle as t

t.setup(500, 500)
#t.shape('square')
#t.shape('circle')
t.shape('turtle')
t.pensize(1) #5

def m(n, len, col): #다각형을 그리는 함수
    t.color(col)
    for x in range(n):
        t.forward(len)
        t.right(360/n)

t.begin_fill()
m(4, 80, 'red')
t.end_fill()

m(5, 100, 'green')
m(6, 120, 'blue')

t.color('yellow')
t.begin_fill()
t.circle(80) #반지름 radius:80
t.end_fill()

#t.exitonclick()
t.mainloop()