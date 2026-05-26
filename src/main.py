from src.simulation.model import BatterySwapModel
import pandas as pd
import matplotlib.pyplot as plt

model = BatterySwapModel(n_riders = 5, n_lockers = 3)

for step in range(20):
    model.step()
    print(f"\n--- Step {model.current_step} ---")
    print(f"Successful swaps: {model.successful_swaps}")
    print(f"Failed swaps: {model.failed_swaps}")

    for agent in model.agents:
        if agent.__class__.__name__ == "Rider":
            print(f"Rider {agent.rider_id}: battery={agent.battery_level}")
    
        elif agent.__class__.__name__ == "Locker":
            print(
                f"locker {agent.locker_id}: "
                f"charged batteries={agent.charged_batteries}"
            )

# basic viz
df = pd.DataFrame(model.history)

locker_columns = [
    col for col in df.columns
    if col.startswith("locker_") and col.endswith("_charged")
]

for col in locker_columns:
    plt.plot(df["step"], df[col], label = col)

plt.xlabel("Simulation step")
plt.ylabel("Charged batteries")
plt.title("Locker level battery depletion over time")
plt.legend()
plt.show()

""" plt.plot(df["step"], df["total_charged_batteries"])
plt.xlabel("simulation_step")
plt.ylabel("total_batteries_charged")
plt.title("Charged Batteries Over Time")
plt.show() """