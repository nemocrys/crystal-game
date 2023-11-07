from tkinter import *
import time
import numpy as np
from postprocess import calculate_score

'''

CHANGES:

18.07.2022
- Tested and improved serial interaface delays
- Merged changes from dev branch

20.07.2022
- Canvas is resized with main window

24.01.2022
- Added option for water with 100 C initial T


TODO

Start can pressed multiple times on gamepad!!
Show target diameter 
Score board?


Outlook:
Show current T in picture
Direct power control instead of PID? I reduzieren? PID optimieren?
Beim Experiment Kamerbild zeigen
Bessere analytische Naeherung fuer D(L)
Numerische Berechnung des Temperaturfeldes im Kristall
Auswahl Kristallmaterial (phys. Eigenschaften)


'''

# root window
root = Tk()
root.title("Hello Mr. Cz")
root.option_add( "*font", "lucida 16 bold" )

# ---------- Global variables

USE_REALITY = FALSE
USE_GAMEPAD = True
USE_WATER = False

global vp, tm, tt, zs, stop, seeding, cr, dt, tts, canvasw, canvash

vp = 0.0 # pull rate [mm/min]
tm = 240 # melt temperature [C]
tt = 0.0 # time [min]
zs = 200 # seed bottom coord [mm]
cr = []  # crystal shape
re = []  # recipe
dt = 0.1 # time increment [min] for 100 ms; see USE_REALITY below!!  
weight = 0
canvasw = 400
canvash = 600
stop = True
seeding = False
tts = int(time.time())
crystal_is_connected=False

# --- Labels
lbl_time_display = ['Zeit [Minuten] = 0', 'Time [minutes] = ']
lbl_start_button = ["Start", "Start"]
lbl_stop_button = ["Stop", "Stop"]
lbl_pullRate_display = ['Ziehrate V [mm/min] = ', 'Pull rate V [mm/min] = ']
lbl_pullRate_button = ['Ziehrate', 'Pull rate']
lbl_temperature_display = ['Temperatur T [°C] = ', 'Temperature T [°C] = ']
lbl_temperature_button = ['Temperatur', 'Temperature']
lbl_zCoordinate_display = ['Höhe=','Height=']
lbl_diameter_display = ['D=','D=']
lbl_weight_display = ['Gewicht=','Weight=']

language = 1 #0: deutsch; 1: english

# ---------- Initialize

if USE_REALITY:
    import ai_interface as ai
    ai.setport(timeout=0.05) # use small value
    dt = 1/60

if USE_GAMEPAD:
    import gamepad as gp
    gp.setdevice()

if USE_WATER:
    tm = 100

# ---------- Screen coordinates 50x300 mm -> 400x600 px

def sx(x) :
    global canvasw
    return x*canvasw/50.0 # 50 mm = 'canvasw' px

def sy(y) :
    global canvash
    return canvash-y*canvash/300.0 # 300 mm = 'canvash' px

def polyxy(xy) :
    poly = []
    for p in xy:
        xx = sx(25+0.5*p[1])
        yy = sy(zs-p[0])
        poly.append(xx)
        poly.append(yy)
    for p in reversed(xy):
        xx = sx(25-0.5*p[1])
        yy = sy(zs-p[0])
        poly.append(xx)
        poly.append(yy)
    return poly

def calc_weight(cr):
    if len(cr)==0:
        volume=0
    else:
        cr = np.array(sum(cr,[])).reshape((-1,2))
        volume = np.pi*cr[0,1]**2*cr[0,0]/4 # starting volume = pi*D_min^2/4*L1
        for i in range(1,len(cr)):
            # volume of current conus in mm^3: V_conus = 1/3*pi*(L_current-L_old)*(D_current^2+D_old*D_old+D_old)/4
            volume += 1/3*np.pi*(cr[i,0]-cr[i-1,0]) * (cr[i,1]**2+cr[i,1]*cr[i-1,1]+cr[i-1,1]**2)/4

    weight_g = volume*1e-6*7179 

    return weight_g

# ---------- Canvas

def temptocol(T):
    r = int(100+(200-100)/(250-232)*(T-232)) # 232->100, 250->200
    if USE_WATER:
        r = int(100+(200-100)/(100.0-0.0)*(T-0.0)) # 232->100, 250->200
    g = 70
    b = 255
    return "#%02x%02x%02x" % (r,g,b)   

canvas1 = Canvas(root, width=canvasw, height=canvash)
root.rowconfigure(tuple(range(7)),weight=1)
root.columnconfigure(0,weight=1)
canvas1.grid(column=0, row=0, rowspan=7, padx=5, sticky='nsew')
#tkinter.update()

# (x0, y0) - top left, (x1, y1)- bottom right
rect1 = canvas1.create_rectangle(0, sy(300), sx(50), sy(0), width=0, fill="white")           # back
rect2 = canvas1.create_rectangle(sx(24), sy(zs+20), sx(26), sy(zs), width=0, fill="grey")    # 2x20 mm seed
rect3 = canvas1.create_rectangle(sx(0), sy(10), sx(50), sy(0), width=0, fill=temptocol(tm))  # 10 mm melt layer
rect4 = canvas1.create_rectangle(sx(24.75), sy(300), sx(25.25), sy(zs+20), width=0, fill="red") # 0.5 mm wire

txt1 = canvas1.create_text(sx(27), sy(zs), text=lbl_zCoordinate_display[language]+str(round(zs))+' mm', anchor='sw', fill="black", font="lucida 12")
txt2 = canvas1.create_text(sx(0), sy(10), text='', anchor='se', fill="black", font="lucida 12")
txt3 = canvas1.create_text(sx(0), sy(10), text='', anchor='se', fill="black", font="lucida 12")

canvas1.addtag_all("all")

# Called also on startup
def canvas_resize(event):
    global canvasw, canvash, stop
    #print(str(event.width)+' '+str(event.height))
    if stop == True:
        wscale = float(event.width-2)/canvasw
        hscale = float(event.height-2)/canvash
        canvasw = event.width - 2
        canvash = event.height - 2
        canvas1.scale("all",0,0,wscale,hscale)

canvas1.bind('<Configure>', canvas_resize)

# ---------- Main calculation and drawing loop, loopback with 100 ms delay!!!

def calculate():
    global tt, zs, stop, seeding, cr, tts, crystal_is_connected, weight

    if stop==False:
        tt = tt + dt #
        lbl1.config(text=lbl_time_display[language]+str(round(tt,1)))
        dz = dt*vp # dz in dt
        if zs+dz<290 :
            if zs+dz>0 :
                zs = zs + dz
                # x0, y0, x1, y1 = canvas1.coords(rect2)
                canvas1.coords(rect2, sx(24), sy(zs+20), sx(26), sy(zs))
                canvas1.coords(rect4, sx(24.75), sy(300), sx(25.25), sy(zs+20))
                canvas1.coords(txt1, sx(27), sy(zs)) 
                canvas1.itemconfig(txt1, text=lbl_zCoordinate_display[language]+str(round(zs))+' mm')
            if zs<10 :
                seeding = True
                crystal_is_connected = True
                weight=0

            if seeding == True and zs>10 :
                L = zs-10 # seed-melt distance
                canvas1.itemconfig(txt2, text='')
                if vp>0:
                    if crystal_is_connected:
                        D = 1000*4*(L/1000.0)*10*(tm-20-500*(L/1000.0)) / ( (vp/60000.0)*7179*6e4 + 62*(tm-232)/0.01 )
                        if len(cr)==0 or L-cr[-1][0]>1: # reduce shape step to 1mm
                            if len(cr)==0: #set starting diameter to 2 mm (=seeding diameter)
                                D = 2
                            if D<0.15: # crystal rips from melt
                                crystal_is_connected=False
                            cr.append([L, D]) 
                            canvas1.delete("cr") # delete the old polygon
                            if len(cr)>1: canvas1.create_polygon(polyxy(cr), fill="grey", outline="black", tag="cr")
                        canvas1.coords(txt2, sx(23-0.5*D), sy(10)) 
                        canvas1.itemconfig(txt2, text=lbl_diameter_display[language]+str(round(D,1))+' mm')
                        # print('Growing: L='+str(L)+' D='+str(D))
                    else: # draw ripped crystal
                        canvas1.delete("cr") # delete the old polygon
                        if len(cr)>1: canvas1.create_polygon(polyxy(cr), fill="grey", outline="black", tag="cr")       
                        weight=0      
                if vp<0:
                    for i in reversed(range(len(cr))):
                        if cr[i][0]>L: cr.pop(i)
                    canvas1.delete("cr") # delete the old polygon
                    if len(cr)>1: canvas1.create_polygon(polyxy(cr), fill="grey", outline="black", tag="cr")
                    # print('Melting: L='+str(L))

                weight_g=calc_weight(cr)                                       
                canvas1.coords(txt3, sx(23), sy(zs)) 
                canvas1.itemconfig(txt3, text=lbl_weight_display[language]+str(round(weight_g,3))+' g')
            
            #ttn = int(time.time())
            #if ttn - tts > 2 :
            #    tts = ttn
            #    print( 't='+str(ttn)+' T='+str(ai.get_cructemp()) )
            
        root.after(100, calculate) # delay in ms!!!

# ---------- Buttons and labels

lbl1 = Label(root, text=lbl_time_display[language]+str(tt))
lbl1.grid(column=1, row=0, columnspan=2, padx=10)


def btn1_run():
    # canvas1.itemconfig(rect1, fill='red')
    global stop
    stop = False
    btn1["state"] = "disabled"
    root.resizable(width=False, height=False)
    calculate()

btn1 = Button(root, text=lbl_start_button[language], width=20, command=btn1_run)
btn1.grid(column=1, row=1, columnspan=2, padx=10)


def btn2_run():
    # canvas1.itemconfig(rect1, fill='green')
    global stop
    stop = True
    btn1["state"] = "normal"
    root.resizable(width=True, height=True)
    with open('crystal.txt', "w") as file1:
        for p in cr: file1.write(str(p[0])+' '+str(p[1])+'\n')
    with open('recipe.txt', "w") as file2:
        for p in re: file2.write(str(p[0])+' '+str(p[1])+' '+str(p[2])+'\n')

    recipe = np.genfromtxt("recipe.txt")
    crystal = np.genfromtxt("crystal.txt")
    score = calculate_score(crystal, recipe, 8)
    print(score)


btn2 = Button(root, text=lbl_stop_button[language], width=20, command=btn2_run)
btn2.grid(column=1, row=2, columnspan=2, padx=10)


lbl2 = Label(root, text=lbl_pullRate_display[language]+str(vp))
lbl2.grid(column=1, row=3, columnspan=2, padx=10)


def btn3_run():
    global vp
    if vp>-100: vp = vp - 1
    lbl2.config(text=lbl_pullRate_display[language]+str(round(vp,2)))
    if USE_REALITY: ai.set_pullrate(vp/60000.0)
    re.append([tt,vp,tm])

btn3 = Button(root, text=lbl_pullRate_button[language]+"-", width=10, command=btn3_run)
btn3.grid(column=1, row=4, padx=10)


def btn4_run():
    global vp
    if vp<100: vp = vp + 1
    lbl2.config(text=lbl_pullRate_display[language]+str(round(vp,2)))
    if USE_REALITY: ai.set_pullrate(vp/60000.0)
    re.append([tt,vp,tm])

btn4 = Button(root, text=lbl_pullRate_button[language]+"+", width=10, command=btn4_run)
btn4.grid(column=2, row=4, padx=10)


lbl3 = Label(root, text=lbl_temperature_display[language]+str(tm))
lbl3.grid(column=1, row=5, columnspan=2, padx=10)


def btn5_run():
    global tm
    if USE_WATER:
        tm = tm - 1
    else:
        if tm>232: tm = tm - 1
    lbl3.config(text=lbl_temperature_display[language]+str(round(tm,1)))
    canvas1.itemconfig(rect3, fill=temptocol(tm))
    if USE_REALITY: ai.set_cructemp(tm)
    re.append([tt,vp,tm])

btn5 = Button(root, text=lbl_temperature_button[language]+"-", width=10, command=btn5_run)
btn5.grid(column=1, row=6, padx=10)


def btn6_run():
    global tm
    if USE_WATER:
        tm = tm + 1
    else:
        if tm<250: tm = tm + 1
    lbl3.config(text=lbl_temperature_display[language]+str(round(tm,1)))
    canvas1.itemconfig(rect3, fill=temptocol(tm))
    if USE_REALITY: ai.set_cructemp(tm)
    #time.sleep(2)
    re.append([tt,vp,tm])

btn6 = Button(root, text=lbl_temperature_button[language]+"+", width=10, command=btn6_run)
btn6.grid(column=2, row=6, padx=10)

# ---------- Loop for gamepad input

def getcontrols():
    res = gp.getevent()
    if res == 'right1':
        btn6.config(relief=SUNKEN) 
        btn6_run()
    if res == 'right0':
        btn6.config(relief=RAISED) 
    if res == 'left1': 
        btn5.config(relief=SUNKEN) 
        btn5_run()
    if res == 'left0': 
        btn5.config(relief=RAISED) 
    if res == 'up1': 
        btn4.config(relief=SUNKEN) 
        btn4_run()
    if res == 'up0':
        btn4.config(relief=RAISED) 
    if res == 'down1': 
        btn3.config(relief=SUNKEN) 
        btn3_run()
    if res == 'down0':
        btn3.config(relief=RAISED) 
    if res == 'start1': 
        btn1.config(relief=SUNKEN) 
        btn1_run()
    if res == 'start0':
        btn1.config(relief=RAISED) 
    if res == 'back1': 
        btn2.config(relief=SUNKEN) 
        btn2_run()
    if res == 'back0': 
        btn2.config(relief=RAISED) 
        
    root.after(50, getcontrols)

# ----------

if USE_GAMEPAD:
    root.after(50, getcontrols)

root.mainloop()
