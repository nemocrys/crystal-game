
from evdev import InputDevice, categorize, ecodes, KeyEvent
from select import select

# ----------

global gamepad

# ----------

def setdevice():
    global gamepad
    gamepad = InputDevice('/dev/input/event3')
    print(gamepad.capabilities(verbose=True))

def getevent():
    global gamepad
    event = gamepad.read_one()
    #if event != None: 
    #    print('---')
    #    print('code='+str(event.code)+' value='+str(event.value)
    if event != None: 
        if event.code==289 and event.value==0: return 'right0'
        if event.code==291 and event.value==0: return 'left0'    
        if event.code==288 and event.value==0: return 'up0'
        if event.code==290 and event.value==0: return 'down0' 
        if event.code==297 and event.value==0: return 'start0' 
        if event.code==296 and event.value==0: return 'back0' 
        if event.code==289 and event.value==1: return 'right1'
        if event.code==291 and event.value==1: return 'left1'    
        if event.code==288 and event.value==1: return 'up1'
        if event.code==290 and event.value==1: return 'down1' 
        if event.code==297 and event.value==1: return 'start1' 
        if event.code==296 and event.value==1: return 'back1' 

# for event in gamepad.read_loop():
    # #if event.type == ecodes.EV_KEY:
    # print(categorize(event))
    # if event.type == ecodes.EV_ABS:
        # print(event.value)
    # # print(keyevent.state)
    # #if keyevent.keystate == KeyEvent.key_down:
    # #print(keyevent.scancode)
    # print('----------')