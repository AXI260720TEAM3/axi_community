import turtle as t

t.setup(500, 500)
t.shape('turtle')

def init():
    t.clear()
    t.penup()
    t.goto(0,0)
    t.pendown()
    #t.setheading(0)
    
t.onkeypress(init, 'Escape')    
t.onscreenclick(t.goto)

t.listen()
t.mainloop()