import turtle as t

def r():
    t.setheading(0)
    t.forward(10)
def u():
    t.setheading(90)
    t.forward(10)
def l():
    t.setheading(180)
    t.forward(10)
def d():
    t.setheading(270)
    t.forward(10)

def pUp(): t.penup()
def pDown(): t.pendown()

def black(): t.color('black')
def red(): t.color('red')
def green(): t.color('green')
def blue(): t.color('blue')
def yellow(): t.color('yellow')

colors = ['black', 'red', 'green', 'blue', 'yellow']
idx=0 #글로벌
def changeC(): 
    global idx
    idx+=1 #글로벌
    if idx>=len(colors): idx=0
    t.color(colors[idx])

def init():
    t.clear()
    t.penup()
    t.goto(0,0)
    t.pendown()
    #t.setheading(0)

t.setup(500, 500)
t.shape('turtle')

t.onkeypress(r, 'Right')
t.onkeypress(u, 'Up')
t.onkeypress(l, 'Left')
t.onkeypress(d, 'Down')

t.onkeypress(pUp, 'u')
t.onkeypress(pDown, 'd')

t.onkeypress(black, 'k')
t.onkeypress(red, 'r')
t.onkeypress(green, 'g')
t.onkeypress(blue, 'b')
t.onkeypress(yellow, 'y')

t.onkeypress(changeC, 'c')

t.onkeypress(init, 'Escape')

t.listen()
t.mainloop()