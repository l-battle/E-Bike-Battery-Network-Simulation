import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from src.agents.rider import Rider 
from src.agents.locker import Locker

def animate_simulation(model, steps=100, interval=300):
    fig, ax = plt.subplots(figsize=(8, 8))

    def update(frame):
        model.step()
        ax.clear()

        for agent in model.agents:
            if isinstance(agent, Rider):
                marker = 'x' if agent.status == "seeking_locker" else 'o'

                ax.scatter(agent.x, agent.y, marker=marker)
                ax.text(
                    agent.x,
                    agent.y,
                    f"R{agent.rider_id}\n{agent.battery_level:.0f}%",
                    fontsize=8
                )

                if agent.target_locker is not None:
                    ax.plot(
                        [agent.x, agent.target_locker.x],
                        [agent.y, agent.target_locker.y],
                        linestyle='--',
                        linewidth=1,
                    )
            
            elif isinstance(agent, Locker):
                ax.scatter(agent.x, agent.y, marker='s', s=220)
                ax.text(
                    agent.x,
                    agent.y,
                    f"L{agent.locker_id}\nC:{agent.charged_batteries}\nD:{agent.depleted_batteries}",
                    fontsize=9
                )

        ax.set_xlim(0, model.width)
        ax.set_ylim(0, model.height)
        ax.set_xlabel("x pos")
        ax.set_ylabel("y pos")
        ax.set_title(
            f"step {model.current_step} | "
            f"swaps: {model.swap_count} | "
            f"Failed: {model.failed_swaps}"
        )
        ax.grid(True)

    anim = FuncAnimation(
        fig,
        update, 
        frames=steps,
        interval=interval,
        repeat=False
    )

    plt.show()

    return anim