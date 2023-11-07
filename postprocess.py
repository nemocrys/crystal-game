import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def calculate_score(crystal, recipe, dset):
    shape = crystal

    # Calculate the average diameter
    lengths = np.diff(shape[:, 0])
    total_length = shape[-1, 0]
    mean_diameter = np.sum(shape[1:, 1] * lengths / total_length)
    d_target = dset # or mean_diameter

    # Create an ideal cylinder array
    ideal_cylinder = np.array([[entry[0], d_target] for entry in shape])

    # Calculate the Diameter Change Penalty
    diameter_change_penalty = np.sum(np.diff([entry[1] for entry in shape]) ** 2)

    # Calculate the MSE between the shape and ideal cylinder
    # mse = np.mean((np.array(shape)[:, 1] - ideal_cylinder[:, 1]) ** 2)
    mse = np.mean((np.array(shape)[:, 1] - ideal_cylinder[:, 1]) ** 2)

    # Weight for each metric
    weight_mse = 1
    weight_diameter_change_penalty = 1

    # Final score
    score = total_length*(weight_mse * mse + weight_diameter_change_penalty * diameter_change_penalty)
    print(f"Target diameter: {d_target}")
    print(f"AVG diameter: {mean_diameter}")
    print(f"Total length: {total_length}")
    print(f"Diameter change penalty: {diameter_change_penalty}")
    print(f"MSE penalty: {mse}")
    print(f"Total score: {score}")

    return score

def plot_recipe(dfC, df):
    plt.subplots(figsize=(6, 6))
    ax1 = plt.subplot2grid((4, 4), (0, 0), colspan=2, rowspan=2)
    ax2 = plt.subplot2grid((4, 4), (2, 0), colspan=2, rowspan=2)
    ax3 = plt.subplot2grid((4, 4), (0, 2), rowspan=4, colspan=2)

    ax1.plot(df["time"], df["pullRate"])
    ax1.set_ylabel("pull rate [mm/min]")
    ax1.set_xlabel("time [s]")
    ax1.grid()

    ax2.plot(df["time"], df["temperature"])
    ax2.set_ylabel("temperature [$^\circ$C]")
    ax2.set_xlabel("time [s]")
    ax2.grid()

    ax3.plot(dfC["diameter"], dfC["length"])
    ax3.set_ylabel("length [mm]")
    ax3.set_xlabel("diameter [mm]")
    ax3.invert_yaxis()
    ax3.grid()

    ax1.set_title("recipe", fontsize=14, y=1.0, pad=-14)
    ax3.set_title('crystal', fontsize=14, y=1.0, pad=-14)

def plot_crystal(dfC):
    max_diameter = dfC["diameter"].max()
    max_length = dfC["length"].max()

    f, ax = plt.subplots(figsize=(3, max_length / 10 * 0.3937))
    ax.plot(dfC["diameter"], dfC["length"], lw=2)
    ax.set_ylabel("length [mm]")
    ax.set_xlabel("diameter [mm]")
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_title("crystal", fontsize=14)
    
    xticks = ax.get_xticks()
    ax.set_xticks([0, max_diameter])
    ax.set_xticklabels([0, round(max_diameter, 1)], rotation=90)
    plt.tight_layout()

def main():
    variables = ["time", "pullRate", "temperature"]
    df = pd.read_csv("recipe.txt", index_col=False, header=None, sep=" ", names=variables)
    dfC = pd.read_csv("crystal.txt", index_col=False, header=None, sep=" ", names=["length", "diameter"])

    plot_recipe(dfC, df)
    score = calculate_score(dfC.to_numpy(), df.to_numpy(), 8)
    praise = ["Bummer, try again!", "Good job!", "Excellent!", "Perfect!"]
    plt.suptitle(f"{praise[0]} Your score is: {int(score)}")
    plt.tight_layout()

    f = plt.gcf()
    f.savefig("results/recipe.pdf", dpi=300)

    plot_crystal(dfC)
    f = plt.gcf()
    f.savefig("results/crystal.pdf", dpi=300)

if __name__ == "__main__":
    main()