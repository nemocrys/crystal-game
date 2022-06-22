from tkinter import *

'''

TODO

- Beim Experiment Kamerbild zeigen
- Bessere analytische Näherung für D(L)
- Numerische Berechnung des Temperaturfeldes im Kristall
- Auswahl Kristallmaterial (phys. Eigenschaften)


'''

# root window
root = Tk()
root.title("Hello Mr. Cz")
root.option_add( "*font", "lucida 16 bold" )

# --- Global variables

global vp, tm, tt, zs, stop, seeding, cr, dt

vp = 0.0 # pull rate [mm/min]
tm = 240 # melt temperature [C]
tt = 0.0 # time [min]
zs = 200.0 # seed bottom coord [mm]
cr = []  # crystal shape
re = []  # recipe
dt = 0.1 # time increment [min] for 100 ms; use 1/600 for real time
stop = False
seeding = False
crystal_is_connected=False
# ---------- Screen coordinates 50x300 mm -> 400x600 px

def sx(x) :
    return x*400/50.0 # 50 mm = 400 px

def sy(y) :
    return 600-y*600/300.0 # 300 mm = 600 px

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

# ---------- Canvas

def temptocol(T):
    r = int(100+(200-100)/(250-232)*(T-232)) # 232->100, 250->200
    g = 70
    b = 255
    return "#%02x%02x%02x" % (r,g,b)   

canvas1 = Canvas(root, width=400, height=600)
canvas1.grid(column=0, row=0, rowspan=7, padx=5)
#tkinter.update()

# (x0, y0) - top left, (x1, y1)- bottom right
rect1 = canvas1.create_rectangle(0, sy(300), sx(50), sy(0), width=0, fill="white")           # back
rect2 = canvas1.create_rectangle(sx(24), sy(zs+20), sx(26), sy(zs), width=0, fill="grey")    # 2x20 mm seed
rect3 = canvas1.create_rectangle(sx(0), sy(10), sx(50), sy(0), width=0, fill=temptocol(tm))  # 10 mm melt layer
rect4 = canvas1.create_rectangle(sx(24.75), sy(300), sx(25.25), sy(zs+20), width=0, fill="red") # 0.5 mm wire

txt1 = canvas1.create_text(sx(27), sy(zs), text='z='+str(round(zs))+' mm', anchor='sw', fill="black", font="lucida 12")
txt2 = canvas1.create_text(sx(0), sy(10), text='', anchor='se', fill="black", font="lucida 12")

# ---------- Main calculation and drawing loop, loopback with 100 ms delay!!!

def calculate():
    global tt, zs, stop, seeding, cr, crystal_is_connected

    if stop==False:
        tt = tt + dt #
        lbl1.config(text="Time [min] = "+str(round(tt,1)))
        dz = dt*vp # dz in dt
        if zs+dz<290 :
            if zs+dz>0 :
                zs = zs + dz
                # x0, y0, x1, y1 = canvas1.coords(rect2)
                canvas1.coords(rect2, sx(24), sy(zs+20), sx(26), sy(zs))
                canvas1.coords(rect4, sx(24.75), sy(300), sx(25.25), sy(zs+20))
                canvas1.coords(txt1, sx(27), sy(zs)) 
                canvas1.itemconfig(txt1, text='z='+str(round(zs))+' mm')
            if zs<10 :
                seeding = True
                crystal_is_connected = True

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
                        canvas1.itemconfig(txt2, text='D='+str(round(D,1))+' mm')
                        # print('Growing: L='+str(L)+' D='+str(D))
                    else: # draw ripped crystal
                        canvas1.delete("cr") # delete the old polygon
                        if len(cr)>1: canvas1.create_polygon(polyxy(cr), fill="grey", outline="black", tag="cr")                        
                if vp<0:
                    for i in reversed(range(len(cr))):
                        if cr[i][0]>L: cr.pop(i)
                    canvas1.delete("cr") # delete the old polygon
                    if len(cr)>1: canvas1.create_polygon(polyxy(cr), fill="grey", outline="black", tag="cr")
                    # print('Melting: L='+str(L))


        root.after(100, calculate) # delay in ms!!!

# ---------- Buttons and labels

lbl1 = Label(root, text="Time [min] = "+str(tt))
lbl1.grid(column=1, row=0, columnspan=2, padx=10)


def btn1_run():
    # canvas1.itemconfig(rect1, fill='red')
    global stop
    stop = False
    btn1["state"] = "disabled"
    calculate()

btn1 = Button(root, text="Start", width=20, command=btn1_run)
btn1.grid(column=1, row=1, columnspan=2, padx=10)


def btn2_run():
    # canvas1.itemconfig(rect1, fill='green')
    global stop
    stop = True
    btn1["state"] = "normal"
    with open('crystal.txt', "w") as file1:
        for p in cr: file1.write(str(p[0])+' '+str(p[1])+'\n')
    with open('recipe.txt', "w") as file2:
        for p in re: file2.write(str(p[0])+' '+str(p[1])+' '+str(p[2])+'\n')

btn2 = Button(root, text="Stop", width=20, command=btn2_run)
btn2.grid(column=1, row=2, columnspan=2, padx=10)


lbl2 = Label(root, text="V [mm/min] = "+str(vp))
lbl2.grid(column=1, row=3, columnspan=2, padx=10)


def btn3_run():
    global vp
    if vp<100: vp = vp + 1
    lbl2.config(text="V [mm/min] = "+str(round(vp,2)))
    re.append([tt,vp,tm])

btn3 = Button(root, text="V+", width=10, command=btn3_run)
btn3.grid(column=2, row=4, padx=10)


def btn4_run():
    global vp
    if vp>-100: vp = vp - 1
    lbl2.config(text="V [mm/min] = "+str(round(vp,2)))
    re.append([tt,vp,tm])

btn4 = Button(root, text="V-", width=10, command=btn4_run)
btn4.grid(column=1, row=4, padx=10)


lbl3 = Label(root, text="T [C] = "+str(tm))
lbl3.grid(column=1, row=5, columnspan=2, padx=10)


def btn5_run():
    global tm
    if tm<250: tm = tm + 1
    lbl3.config(text="T [C] = "+str(round(tm,1)))
    canvas1.itemconfig(rect3, fill=temptocol(tm))
    re.append([tt,vp,tm])

btn5 = Button(root, text="T+", width=10, command=btn5_run)
btn5.grid(column=2, row=6, padx=10)


def btn6_run():
    global tm
    if tm>232: tm = tm - 1
    lbl3.config(text="T [C] = "+str(round(tm,1)))
    canvas1.itemconfig(rect3, fill=temptocol(tm))
    re.append([tt,vp,tm])

btn6 = Button(root, text="T-", width=10, command=btn6_run)
btn6.grid(column=1, row=6, padx=10)

# ----------

root.mainloop()