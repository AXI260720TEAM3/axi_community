import turtle as t
import random as r


te = t.Turtle()
te.shape("turtle")
te.color("red")
te.speed(0)
te.up()
te.goto(0, 200)

tf = t.Turtle()
tf.shape("circle")
tf.color("green")
tf.up()
tf.goto(0, -200)

playing = False
score = 0

def turnR():
	t.setheading(0)
def turnU():
	t.setheading(90)
def turnL():
	t.setheading(180)
def turnD():
	t.setheading(270)
def play():
	global playing
	global score
	t.forward(10)
	
	if r.randint(1, 5) == 3:
		ang = te.towards(t.pos())
		te.setheading(ang)
	
	speedD = score + 5
	if speedD > 15:
		speedD = 15
	te.forward(speedD)

	if t.distance(tf)<12:
		score += 1 
		t.write(score)
		foodX = r.randint(-230, 230)
		foodY = r.randint(-230, 230)
		tf.goto(foodX, foodY)
	if t.distance(te)<12:
		scoreTxt = "Score : " + str(score)
		showmsg("Game Over", scoreTxt)
		playing = False
		score = 0
	if playing:
		t.ontimer(play, 100)

def showmsg(msg1, msg2):
	t.clear()
	t.goto(0, 100)
	t.write(msg1, False, "center", ("", 20))
	t.goto(0, -100)
	t.write(msg2, False, "center", ("", 15))
	t.home()

def start():
	global playing
	if playing == False:
		playing = True
		t.clear()
		play()

t.setup(500, 500)
t.bgcolor("orange")
t.shape("turtle");
t.speed(0)
t.up()
t.color("white")
t.onkeypress(turnR, "Right")
t.onkeypress(turnU, "Up")
t.onkeypress(turnL, "Left")
t.onkeypress(turnD, "Down")
t.onkeypress(start, "space")
t.listen()
showmsg("거북이를 잡아라", "[ Space for Start ]")
#play()

t.done()