from src.simulation.model import BatterySwapModel
from src.agents.rider import Rider
from src.agents.locker import Locker
import pandas as pd
import matplotlib.pyplot as plt
from src.visualization.live_grid import animate_simulation

model = BatterySwapModel(n_riders = 5, n_lockers = 3)

anim = animate_simulation(model, steps=100, interval=300)

