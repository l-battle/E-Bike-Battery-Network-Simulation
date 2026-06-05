import matplotlib.pyplot as plt
import pandas as pd

# Shared x-axis for all time series. Switch these two constants to change
# what every plot is drawn against, e.g.:
#   X_COLUMN, X_LABEL = "elapsed_minutes", "Elapsed time (minutes)"
X_COLUMN = "step"
X_LABEL = "Simulation step"


def history_to_dataframe(model):
    return pd.DataFrame(model.history)


def plot_system_outcomes(df):
    plt.figure()

    plt.plot(df[X_COLUMN], df["completed_trips"], label="Completed trips")
    plt.plot(df[X_COLUMN], df["stranded_count"], label="Stranded riders")
    plt.plot(df[X_COLUMN], df["swap_count"], label="Successful swaps")
    plt.plot(df[X_COLUMN], df["failed_swaps"], label="Failed swaps")

    plt.xlabel(X_LABEL)
    plt.ylabel("Count")
    plt.title("System Outcomes Over Time")
    plt.legend()


def plot_battery_states(df):
    plt.figure()

    plt.plot(df[X_COLUMN], df["total_charged_batteries"], label="Charged batteries")
    plt.plot(df[X_COLUMN], df["total_depleted_batteries"], label="Depleted batteries")

    plt.xlabel(X_LABEL)
    plt.ylabel("Battery count")
    plt.title("Battery State Over Time")
    plt.legend()


def plot_average_battery(df):
    plt.figure()

    plt.plot(df[X_COLUMN], df["avg_battery"])

    plt.xlabel(X_LABEL)
    plt.ylabel("Average battery level")
    plt.title("Average Rider Battery Over Time")


def plot_rider_status_counts(df):
    plt.figure()

    plt.plot(df[X_COLUMN], df["active_riders"], label="Delivering")
    plt.plot(df[X_COLUMN], df["seeking_riders"], label="Seeking locker")
    plt.plot(df[X_COLUMN], df["stranded_riders"], label="Stranded")

    plt.xlabel(X_LABEL)
    plt.ylabel("Number of riders")
    plt.title("Rider Status Counts Over Time")
    plt.legend()


def plot_locker_inventory(df):
    plt.figure()

    locker_columns = [
        col for col in df.columns
        if col.startswith("locker_") and col.endswith("_charged")
    ]

    for col in locker_columns:
        plt.plot(df[X_COLUMN], df[col], label=col)

    plt.xlabel(X_LABEL)
    plt.ylabel("Charged batteries")
    plt.title("Locker Inventory Over Time")
    plt.legend()


def show_all_graph_metrics(model):
    df = history_to_dataframe(model)

    plot_system_outcomes(df)
    plot_battery_states(df)
    plot_average_battery(df)
    plot_rider_status_counts(df)
    plot_locker_inventory(df)

    plt.show()
