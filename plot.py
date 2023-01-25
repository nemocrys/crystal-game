import matplotlib.pyplot as plt
import pandas as pd

variables = ["time", 
            "pullRate", 
            "temperature"]
            
##################

df = pd.read_csv("recipe.txt",
                index_col = False,
                header = None,
                sep=" ", 
                names = variables)

dfC = pd.read_csv("crystal.txt",
                index_col = False,
                header = None,
                sep=" ", 
                names = ["length","diameter"])                

plt.subplots(figsize=(6,6))
ax1 = plt.subplot2grid((4, 4), (0, 0), colspan=2, rowspan=2)
ax2 = plt.subplot2grid((4, 4), (2, 0), colspan=2, rowspan=2)
ax3 = plt.subplot2grid((4, 4), (0, 2), rowspan=4, colspan=2)
ax1.plot(df["time"],df["pullRate"])
ax1.set_ylabel("pull rate [mm/min]")
ax1.set_xlabel("time [s]")
ax1.grid()

ax2.plot(df["time"],df["temperature"])
ax2.set_ylabel("temperature [$^\circ$C]")
ax2.set_xlabel("time [s]")
ax2.grid()

ax3.plot(dfC["diameter"],dfC["length"])
ax3.set_ylabel("length [mm]")
ax3.set_xlabel("diameter [mm]")
ax3.invert_yaxis()
ax3.grid()

ax1.set_title("recipe",fontsize=14, y=1.0, pad=-14)
ax3.set_title('crystal',fontsize=14, y=1.0, pad=-14)

f = plt.gcf()

plt.tight_layout()
f.savefig("democz-results.pdf",dpi=300)
