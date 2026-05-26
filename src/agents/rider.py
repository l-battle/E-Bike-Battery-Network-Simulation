from mesa import Agent
from src.agents.locker import Locker
import random, math

class Rider(Agent):
    """A rider """

    def __init__(self, model, rider_id, x, y, battery_level=100, battery_threshold=20, speed=5, consumption_rate=1):
        super().__init__(model)
        self.rider_id = rider_id
        self.x = x
        self.y = y
        self.battery_threshold = battery_threshold
        self.speed = speed
        self.consumption_rate = consumption_rate
        self.battery_level = battery_level
        self.target_locker = None
        self.status = "riding"

    def step(self):
        # If battery is low, enter seeking mode
        if self.battery_level <= self.battery_threshold and self.status != "seeking_locker":
            self.status = "seeking_locker"
            self.target_locker = self.find_nearest_available_locker()

        # Seeking locker behavior
        if self.status == "seeking_locker":

            # No available locker exists
            if self.target_locker is None:
                print(f"Rider {self.rider_id} could not find an available locker")
                self.model.failed_swaps += 1
                return

            # Target locker became empty before rider arrived
            if self.target_locker.charged_batteries <= 0:
                self.target_locker = self.find_nearest_available_locker()

                if self.target_locker is None:
                    print(f"Rider {self.rider_id} could not find another available locker")
                    self.model.failed_swaps += 1
                    return

            self.move_towards(self.target_locker.x, self.target_locker.y)

            if self.distance_to(self.target_locker) <= self.speed:
                self.try_swap(self.target_locker)

        # Normal riding behavior
        else:
            self.random_move()

    def random_move(self):
        dx = random.uniform(-1, 1) * self.speed
        dy = random.uniform(-1, 1) * self.speed
    
        self.x = max(0, min(self.model.width, self.x + dx))
        self.y = max(0, min(self.model.height, self.y + dy))
    
        distance = math.sqrt(dx**2 + dy**2)
        self.battery_level -= distance * self.consumption_rate

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
             return
        
        move_distance = min(self.speed, distance)
        self.x += (dx / distance) * move_distance
        self.y += (dy / distance) * move_distance

        self.battery_level -= move_distance * self.consumption_rate

    def find_nearest_available_locker(self):
        lockers = [
            agent for agent in self.model.agents
            if isinstance(agent, Locker) and agent.charged_batteries > 0    
        ]

        if not lockers:
             return None
        
        return min(lockers, key=lambda locker: self.distance_to(locker))
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def try_swap(self, locker):
        if locker.charged_batteries > 0:
            locker.charged_batteries -= 1
            self.battery_level = 100
            self.status = "riding"
            self.target_locker = None
            self.model.swap_count += 1
            print(f"Rider {self.rider_id} swapped at Locker {locker.locker_id}")
        else:
            self.model.failed_swaps += 1
            self.target_locker = None
            print(f"Rider {self.rider_id} failed to swap at Locker {locker.locker_id}")