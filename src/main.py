from src.simulation.model import BatterySwapModel
from src.agents.rider import Rider
from src.agents.locker import Locker
import pandas as pd
import matplotlib.pyplot as plt

model = BatterySwapModel(n_riders = 5, n_lockers = 3)

for step in range(50):
    model.step()

# basic viz
df = pd.DataFrame(model.history)

locker_columns = [
    col for col in df.columns
    if col.startswith("locker_") and col.endswith("_charged")
]

# locker battery depletion over time
for col in locker_columns:
    plt.plot(df["step"], df[col], label = col)

plt.xlabel("Simulation step")
plt.ylabel("Charged batteries")
plt.title("Locker level battery depletion over time")
plt.legend()
plt.show()

# batteries over time plot
""" plt.plot(df["step"], df["total_charged_batteries"])
plt.xlabel("simulation_step")
plt.ylabel("total_batteries_charged")
plt.title("Charged Batteries Over Time")
plt.show() """

# spatial plot
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
plt.show()