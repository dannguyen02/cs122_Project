import tkinter as tk
from tkinter import ttk
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class DataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NOAA Coastal Data Visualizer")
        self.station_id = "9414290"
        self.today = date.today()
        print(self.today)

        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()

        self.products = {
            "Water Temperature": "water_temperature",
            "Water Level": "water_level",
            "Tide Predictions": "predictions",
        }

        self.stations = {
            "San Francisco": 9414290,
            "Bay Bridge": 9414304,
            "Redwood City": 9414523,
            "Alameda": 9414750,
            "Oakland Middle Harbor": 9414769,
            "Monterey": 9413450,
            "Port Chicago": 9415144,
            "Point Reyes": 9415020,
            "Washington Lake": 9416131
        }

        tk.Label(root, text="Ocean Data Dashboard",
                 font=("Arial", 30)).pack(pady=10)
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="Data type").grid(row=0, column=0, padx=5)

        self.product_var = tk.StringVar(value="Water Temperature")
        self.product_menu = ttk.Combobox(
            control_frame,
            textvariable=self.product_var,
            values=list(self.products.keys()),
            state="readonly",
            width=18
        )
        self.product_menu.grid(row=1, column=0, padx=8)

        tk.Label(control_frame, text="Time range (hours)").grid(row=0, column=1, padx=5)

        self.time_range_var = tk.StringVar(value="24")
        self.time_range_input = tk.Entry(
            control_frame,
            textvariable=self.time_range_var,
            width=10
        )
        self.time_range_input.grid(row=1, column=1, padx=8)

        tk.Label(control_frame, text="Station").grid(row=0, column=2, padx=5)

        self.station_var = tk.StringVar(value="San Francisco")
        self.station_menu = ttk.Combobox(
            control_frame,
            textvariable=self.station_var,
            values=list(self.stations.keys()),
            state="readonly",
            width=18
        )
        self.station_menu.grid(row=1, column=2, padx=8)

        self.get_button = tk.Button(control_frame, text="Get Data", command=self.get_data)
        self.get_button.grid(row=1, column=3, padx=8)

        self.visualization_button = tk.Button(
            control_frame,
            text="Open Visualizations",
            command=self.open_visualization_window
        )
        self.visualization_button.grid(row=1, column=4, padx=8)

        self.figure, self.ax = plt.subplots(figsize=(7, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(pady=10)

        self.summary_label = tk.Label(root, text="No data")
        self.summary_label.pack(pady=10)

        self.status_label = tk.Label(root, text="Ready")
        self.status_label.pack(pady=5)

    def get_data(self):
        product = self.products[self.product_var.get()]
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        station = str(self.stations[self.station_var.get()])

        params = {
            "product": product,
            "application": "test",
            "begin_date": "20260301",
            "end_date": "20260302",
            "station": station,
            "time_zone": "gmt",
            "units": "metric",
            "format": "json"
        }

        if product == "water_level":
            params["datum"] = "MLLW"

        if product == "predictions":
            params["datum"] = "MLLW"
            params["interval"] = "h"

        try:
            response = requests.get(url, params=params)
            data = response.json()
        except:
            self.status_label["text"] = "Error getting data"
            return

        if "data" in data:
            df = pd.DataFrame(data["data"])
        elif "predictions" in data:
            df = pd.DataFrame(data["predictions"])
        else:
            self.status_label["text"] = "No data"
            return

        if "t" not in df.columns:
            self.status_label["text"] = "No data"
            return

        if "v" in df.columns:
            value_col = "v"
        else:
            other_cols = [col for col in df.columns if col != "t"]
            if len(other_cols) == 0:
                self.status_label["text"] = "No data"
                return
            value_col = other_cols[0]

        df = df.rename(columns={"t": "time", value_col: "value"})
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna()

        self.df = df
        self.filtered_df = df

        self.update_plot()
        self.update_summary()
        self.status_label["text"] = "Ready"

    def update_plot(self):
        self.ax.clear()

        if self.filtered_df.empty:
            self.ax.set_title("No data")
        else:
            self.ax.plot(self.filtered_df["time"], self.filtered_df["value"])
            self.ax.set_title(self.product_var.get())
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Value")
            self.ax.tick_params(axis="x", rotation=25)

        self.figure.tight_layout()
        self.canvas.draw()

    def update_summary(self):
        if self.filtered_df.empty:
            self.summary_label.config(text="No data")
            return

        values = self.filtered_df["value"]
        avg_value = np.mean(values)
        max_value = np.max(values)
        min_value = np.min(values)

        summary_text = f"Average: {avg_value:.2f}   Max: {max_value:.2f}   Min: {min_value:.2f}"
        self.summary_label.config(text=summary_text)

    def open_visualization_window(self):
        print("Visualization window clicked")


if __name__ == "__main__":
    root = tk.Tk()  # Change from Tk() to tk.Tk()
    app = DataApp(root)
    root.mainloop()
