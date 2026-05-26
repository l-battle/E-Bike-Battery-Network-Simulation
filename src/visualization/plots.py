from src.simulation.model import BatterySwapModel
from src.agents.rider import Rider
from src.agents.locker import Locker
import pandas as pd
import matplotlib.pyplot as plt
from src.visualization.live_grid import animate_simulation

model = BatterySwapModel(n_riders = 5, n_lockers = 3)

# basic viz
df = pd.DataFrame(model.history)

locker_columns = [
    col for col in df.columns
    if col.startswith("locker_") and col.endswith("_charged")
]

# locker battery depletion over time
plt.figure()
for col in locker_columns:
    plt.plot(df["step"], df[col], label = col)

plt.xlabel("Simulation step")
plt.ylabel("Charged batteries")
plt.title("Locker level battery depletion over time")
plt.legend()
plt.show(block=False)

# batteries over time plot
plt.figure()
plt.plot(df["step"], df["total_charged_batteries"])
plt.xlabel("simulation_step")
plt.ylabel("total_batteries_charged")
plt.title("Charged Batteries Over Time")
plt.show(block=False)

# spatial plot
plt.figure()
for agent in model.agents:
    if isinstance(agent, Rider):
        plt.scatter(agent.x, agent.y, marker='o', label='Rider')
    
    elif isinstance(agent, Locker):
        plt.scatter(agent.x, agent.y, marker='s', label=f'Locker {agent.locker_id}')

plt.xlim(0, model.width)
plt.ylim(0, model.height)
plt.xlabel("x pos")
plt.ylabel("y pos")
plt.title("Rider and Locker Positions")
plt.legend()
plt.show(block=False)

#charged+depleted battery plot
plt.figure()
plt.plot(df["step"], df["total_charged_batteries"], label="Charged batteries")
plt.plot(df["step"], df["total_depleted_batteries"], label="Depleted batteries")

plt.xlabel("Simulation step")
plt.ylabel("Battery count")
plt.title("Charged vs Depleted Batteries Over Time")
plt.legend()
plt.show(block=False)

# spatial trajectory plot
plt.figure()
for agent in model.agents:
    if isinstance(agent, Rider):
        x_coords = [pos[0] for pos in agent.path_history]
        y_coords = [pos[1] for pos in agent.path_history]

        plt.plot(x_coords, y_coords, alpha=0.5)
        plt.scatter(agent.x, agent.y, marker="o")
        plt.text(agent.x, agent.y, f"R{agent.rider_id}")

    elif isinstance(agent, Locker):
        plt.scatter(agent.x, agent.y, marker="s", s=200)
        plt.text(agent.x, agent.y, f"L{agent.locker_id}")

plt.xlim(0, model.width)
plt.ylim(0, model.height)
plt.xlabel("x pos")
plt.ylabel("y pos")
plt.title("Rider Trajectories and Locker Positions")
plt.show()