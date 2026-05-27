from src.visualization.live_grid import animate_simulation
from src.simulation.model import BatterySwapModel

model = BatterySwapModel(n_riders = 5, n_lockers = 3)

anim = animate_simulation(model, steps=100, interval=300)