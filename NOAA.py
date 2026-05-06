import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from scipy.signal import savgol_filter
from statsmodels.tsa.seasonal import seasonal_decompose

class DataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NOAA Coastal Data Visualizer")
        self.station_id = "9414523"

        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()

        self.products = {
            "Water Temperature (°C)": "water_temperature",
            "Water Level (Meters)": "water_level",
            "Tide Height Predictions (Meters)": "predictions",
        }

        self.stations = {
            "Alameda": 9414750,
            "Monterey": 9413450,
            "Port Chicago": 9415144,
            "Point Reyes": 9415020
        }

        DATA_FOLDER = "noaa_data_csv_files"

        tk.Label(root, text="Ocean Data Dashboard",
                 font=("Arial",24)).pack(pady=10)
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="Data type").grid(row=0, column=0, padx=5)

        self.product_var = tk.StringVar(value="Water Temperature (°C)")
        self.product_menu = ttk.Combobox(
            control_frame,
            textvariable=self.product_var,
            values=list(self.products.keys()),
            state="readonly",
            width=25
        )
        self.product_menu.grid(row=1, column=0, padx=8)

        tk.Label(control_frame, text="Past number of days (max 31)").grid(row=0, column=1, padx=5)

        self.time_range_var = tk.StringVar(value="7")
        self.time_range_input = tk.Entry(
            control_frame,
            textvariable=self.time_range_var,
            width=10
        )
        self.time_range_input.grid(row=1, column=1, padx=8)

        tk.Label(control_frame, text="Station").grid(row=0, column=2, padx=5)

        self.station_var = tk.StringVar(value="Alameda")
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

        # self.save_button = tk.Button(
        #     control_frame, 
        #     text="Save to CSV", 
        #     command=self.save_to_csv
        #     )
        # self.save_button.grid(row=1, column=5, padx=8)

        self.figure, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(pady=10)

        self.summary_label = tk.Label(root, text="No data")
        self.summary_label.pack(pady=10)

        self.status_label = tk.Label(root, text="Ready")
        self.status_label.pack(pady=5)

        self.data_folder = "noaa_data_csv_files"
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    def get_data(self):
        # print("clicked get data")
        product = self.products[self.product_var.get()]
        station_name = self.station_var.get().replace(" ", "_").lower()

        days_back = int(self.time_range_var.get())
        start_date = pd.to_datetime("today") - pd.Timedelta(days=days_back)
        begin_date = start_date.strftime("%Y%m%d")
        end_date = pd.to_datetime("today").strftime("%Y%m%d")

        local_filename = f"{station_name}_{product}_{begin_date}_{end_date}.csv"
        local_filepath = os.path.join(self.data_folder, local_filename)

        if os.path.exists(local_filepath):
            # print(f"Loading data from local file: {local_filepath}")
            self.df = pd.read_csv(local_filepath)

            self.df["time"] = pd.to_datetime(self.df["time"])
            self.filtered_df = self.df
            self.update_plot()
            self.update_summary()
            self.status_label["text"] = f"Found and loaded data from local file {local_filepath}"
            return
    
        # print("data not found locally, using api")
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        station = str(self.stations[self.station_var.get()])

        params = {
            "product": product,
            "application": "test",
            "begin_date": begin_date,
            "end_date": end_date,
            "station": station,
            "time_zone": "gmt",
            "units": "metric",
            "format": "json"
        }

        # if product in ["water_level", "predictions"]:
        #         params["datum"] = "MLLW"
        #         if product == "predictions":
        #             params["interval"] = "h"

        if product == "water_level":
            params["datum"] = "MLLW"

        if product == "predictions":
            params["datum"] = "MLLW"
            params["interval"] = "h"

        try:
            response = requests.get(url, params=params)
            data = response.json()

            # import json
            # print(json.dumps(data, indent=4))
            if "error" in data:
                self.filtered_df = pd.DataFrame()
                self.update_plot()
                self.status_label["text"] = data["error"]["message"]
                messagebox.showerror("Error", data["error"]["message"])
                return
        except:
            self.status_label["text"] = "Error getting data"
            self.filtered_df = pd.DataFrame()
            self.update_plot()
            messagebox.showerror("Error", data["error"]["message"])
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

        self.save_to_csv()

    def update_plot(self):
        self.ax.clear()

        if self.filtered_df.empty:
            self.ax.set_title("No data")
        else:
            # self.ax.plot(self.filtered_df["time"], self.filtered_df["value"], label='Data')
            self.ax.set_title(self.product_var.get())
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Value")
            self.ax.tick_params(axis="x", rotation=25, labelsize=8)

            category = self.product_var.get() 
            x = self.filtered_df['time']
            y = self.filtered_df['value']

            self.ax.plot(x, y, color="black", label="Data")

            if "Temperature" in category:
                # Straight line for Temp
                z = np.polyfit(pd.to_numeric(x), y, 1)
                p = np.poly1d(z)
                self.ax.plot(x, p(pd.to_numeric(x)), "r--", label="Temp Trend", alpha=0.4)

            elif "Water Level" in category:
                # window=240 for 6-minute data (24 hours)
                # min_periods=1 ensures it starts at the first data point
                trend = y.rolling(window=240, center=True, min_periods=1).mean()
                self.ax.plot(x, trend, color="red", linewidth=2, label="Daily Mean", alpha=0.4, linestyle='dashed')
            
        self.ax.legend()
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
        self.summary_label.config(text=summary_text, font=("Arial", 16))

    # def open_visualization_window(self):
    #     print("Visualization window clicked")
    def open_visualization_window(self):
        if self.filtered_df.empty:
            messagebox.showwarning("No Data", "Please load data before opening visualizations.")
            return

        win = tk.Toplevel(self.root)
        win.title("Visualizations")
        win.geometry("1000x700")

        y = self.filtered_df["value"].reset_index(drop=True)
        x = self.filtered_df["time"].reset_index(drop=True)

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        ax1 = axes[0, 0]
        ax2 = axes[0, 1]
        ax3 = axes[1, 0]
        ax4 = axes[1, 1]
        fig.subplots_adjust(hspace=0.4, wspace=0.3, top=0.95, bottom=0.1, left=0.08, right=0.97)

        ax1.plot(x, y, color="gray", alpha=0.5, linewidth=0.8, label="Raw data")
        if len(y) >= 13:
            window = min(51, len(y) if len(y) % 2 == 1 else len(y) - 1)
            smoothed = savgol_filter(y, window_length=window, polyorder=3)
            ax1.plot(x, smoothed, color="steelblue", linewidth=2, label="Smoothed")
        ax1.set_title("Smoothed Signal", fontsize=11, pad=8)
        #ax1.set_xlabel("Time")
        #ax1.set_ylabel("Value")
        ax1.tick_params(axis="x", rotation=20, labelsize=7)
        ax1.legend(fontsize=8)

        ax2.hist(y, bins=30, color="steelblue", edgecolor="white", alpha=0.85)
        ax2.axvline(np.mean(y), color="red", linestyle="--", linewidth=1.5, label=f"Mean: {np.mean(y):.2f}")
        ax2.set_title("Value Distribution", fontsize=11, pad=8)
        #ax2.set_xlabel("Value")
        #ax2.set_ylabel("Frequency")
        ax2.legend(fontsize=8)

        try:
            if len(y) >= 48:
                result = seasonal_decompose(y, model="additive", period=24, extrapolate_trend="freq")
                ax3.plot(x, result.trend, color="darkorange", linewidth=1.5, label="Trend")
            else:
                ax3.text(0.5, 0.5, "Not enough data", ha="center", va="center", transform=ax3.transAxes)
        except Exception as e:
            ax3.text(0.5, 0.5, str(e), ha="center", va="center", transform=ax3.transAxes, fontsize=8)
        ax3.set_title("Seasonal Decomposition", fontsize=11, pad=8)
        #ax3.set_xlabel("Time")
        #ax3.set_ylabel("Value")
        ax3.tick_params(axis="x", rotation=20, labelsize=7)
        ax3.legend(fontsize=8)

        mean_val = np.mean(y)
        std_val = np.std(y)
        ax4.plot(x, y, color="gray", alpha=0.5, linewidth=0.8, label="Data")
        ax4.axhline(mean_val, color="steelblue", linewidth=1.5, label=f"Mean: {mean_val:.2f}")
        ax4.axhline(mean_val + std_val, color="orange", linewidth=1.2, linestyle="--",
                    label=f"+1 std: {mean_val + std_val:.2f}")
        ax4.axhline(mean_val - std_val, color="orange", linewidth=1.2, linestyle="--",
                    label=f"-1 std: {mean_val - std_val:.2f}")
        ax4.fill_between(x, mean_val - std_val, mean_val + std_val, color="steelblue", alpha=0.1)
        ax4.set_title("Mean ± Std Dev", fontsize=11, pad=8)
        #ax4.set_xlabel("Time")
        #ax4.set_ylabel("Value")
        ax4.tick_params(axis="x", rotation=20, labelsize=7)
        ax4.legend(fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        tk.Button(win, text="Close", command=win.destroy).pack(pady=8)

    def save_to_csv(self):

        if self.df.empty:
            self.status_label["text"] = "No data to save"
            return None
    
        data_type = self.products[self.product_var.get()]
        station_name = self.station_var.get().replace(" ", "_").lower()


        days_back = int(self.time_range_var.get())
        start_date = pd.to_datetime("today") - pd.Timedelta(days=days_back)
        begin_date = start_date.strftime("%Y%m%d")
        end_date = pd.to_datetime("today").strftime("%Y%m%d")

        filename = f"{station_name}_{data_type}_{begin_date}_{end_date}.csv"
        filepath = os.path.join(self.data_folder, filename)

        try:
            self.df.to_csv(filepath,  index=False)
            # print(f"Successfully saved to {filename}")
            self.status_label["text"] = f"Saved: {filename}"
            return filename
        except Exception as e:
            # print(f"Save failed: {e}")
            self.filtered_df = pd.DataFrame()
            self.update_plot()
            self.status_label["text"] = "Save Error"
            messagebox.showerror("Error", "Save Error")
            return None
        


if __name__ == "__main__":
    root = tk.Tk()  # Change from Tk() to tk.Tk()
    app = DataApp(root)
    root.mainloop()
