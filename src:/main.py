from simulation.model import BatterySwapModel

model = BatterySwapModel(n_riders = 5, n_lockers = 3)

for step in range(20):
    print(f"\n--- Step {step} ---")
    model.step()