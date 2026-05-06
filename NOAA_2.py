import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from scipy.signal import savgol_filter
from statsmodels.tsa.seasonal import seasonal_decompose

BG = "#f4f6f8"
SURFACE = "#ffffff"
BORDER = "#d0d7de"
ACCENT = "#0969da"
ACCENT2 = "#0550ae"
TEXT = "#1f2328"
SUBTEXT = "#656d76"
SUCCESS = "#1a7f37"
ERROR = "#cf222e"

# Matplotlib styling
MPL_STYLE = {
    "figure.facecolor":  SURFACE,
    "axes.facecolor":    "#f4f6f8",
    "axes.edgecolor":    BORDER,
    "axes.labelcolor":   SUBTEXT,
    "axes.titlecolor":   TEXT,
    "axes.titlesize":    11,
    "axes.titlepad":     10,
    "xtick.color":       SUBTEXT,
    "ytick.color":       SUBTEXT,
    "xtick.labelsize":   7,
    "ytick.labelsize":   8,
    "grid.color":        BORDER,
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "legend.facecolor":  SURFACE,
    "legend.edgecolor":  BORDER,
    "legend.labelcolor": TEXT,
    "legend.fontsize":   8,
    "text.color":        TEXT,
}

plt.rcParams.update(MPL_STYLE)


class DataApp:

    def __init__(self, root):
        self.root = root
        self.root.title("NOAA Coastal Data Visualizer")
        self.root.geometry("1200x720")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.df          = pd.DataFrame()
        self.filtered_df = pd.DataFrame()

        self.products = {
            "Water Temperature (°C)":           "water_temperature",
            "Water Level (Meters)":             "water_level",
            "Tide Height Predictions (Meters)": "predictions",
        }

        self.stations = {
            "Alameda":      9414750,
            "Monterey":     9413450,
            "Port Chicago": 9415144,
            "Point Reyes":  9415020,
        }

        self.data_folder = "noaa_data_csv_files"

        self.apply_theme()
        self.build_ui()

        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)


    def apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".",
            background=BG, foreground=TEXT,
            fieldbackground=SURFACE, bordercolor=BORDER,
            darkcolor=BORDER, lightcolor=BORDER,
            troughcolor=SURFACE, selectbackground=ACCENT,
            selectforeground="white", font=("Helvetica", 10))
        style.configure("TCombobox",
            fieldbackground=SURFACE, background=SURFACE,
            foreground=TEXT, arrowcolor=ACCENT, bordercolor=BORDER, relief="flat")
        style.map("TCombobox",
            fieldbackground=[("readonly", SURFACE)],
            foreground=[("readonly", TEXT)])
        style.configure("TEntry",
            fieldbackground=SURFACE, foreground=TEXT,
            insertcolor=TEXT, bordercolor=BORDER, relief="flat")


    def build_ui(self):
        header = tk.Frame(self.root, bg=SURFACE, pady=12)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="NOAA Coastal Data Visualizer",
                 font=("Georgia", 18, "bold"), bg=SURFACE, fg=TEXT).pack(side=tk.LEFT, padx=18)
        tk.Label(header, text="Bay Area Tidal & Oceanographic Stations · GMT",
                 font=("Helvetica", 9), bg=SURFACE, fg=SUBTEXT).pack(side=tk.LEFT, padx=4)
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(body, bg=SURFACE, width=260)
        sidebar.pack(fill=tk.Y, side=tk.LEFT)
        sidebar.pack_propagate(False)

        tk.Frame(body, bg=BORDER, width=1).pack(fill=tk.Y, side=tk.LEFT)

        main = tk.Frame(body, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.build_sidebar(sidebar)
        self.build_main(main)

        # Status bar at the bottom
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)
        status_bar = tk.Frame(self.root, bg=SURFACE, pady=5)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(status_bar, text="●  Ready",
            font=("Helvetica", 9), bg=SURFACE, fg=SUCCESS, anchor="w")
        self.status_label.pack(padx=14, anchor="w")


    def build_sidebar(self, parent):
        tk.Label(parent, text="PARAMETERS", font=("Helvetica", 8),
                 bg=SURFACE, fg=SUBTEXT).pack(anchor="w", padx=14, pady=(10, 2))

        tk.Label(parent, text="Data Type", font=("Helvetica", 8),
                 bg=SURFACE, fg=SUBTEXT).pack(anchor="w", padx=14, pady=(4, 2))
        self.product_var = tk.StringVar(value="Water Temperature (°C)")
        ttk.Combobox(parent, textvariable=self.product_var,
                     values=list(self.products.keys()),
                     state="readonly", width=27).pack(padx=14, pady=(0, 8), fill=tk.X)

        tk.Label(parent, text="Days Back (1–31)", font=("Helvetica", 8),
                 bg=SURFACE, fg=SUBTEXT).pack(anchor="w", padx=14, pady=(4, 2))
        self.time_range_var = tk.StringVar(value="7")
        ttk.Entry(parent, textvariable=self.time_range_var,
                  width=10).pack(padx=14, pady=(0, 10), anchor="w")

        btn_row = tk.Frame(parent, bg=SURFACE)
        btn_row.pack(fill=tk.X, padx=14, pady=(0, 12))
        self.make_button(btn_row, "Get Data",
                         self.get_data, ACCENT).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.make_button(btn_row, "Visualizations",
                         self.open_visualization_window, BG).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, pady=4)

        tk.Label(parent, text="STATIONS", font=("Helvetica", 8),
                 bg=SURFACE, fg=SUBTEXT).pack(anchor="w", padx=14, pady=(10, 2))

        self.station_var   = tk.StringVar(value="Alameda")
        self.station_cards = {}

        for name in self.stations:
            card = tk.Frame(parent, bg=BG, pady=7, padx=10,
                            highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill=tk.X, padx=14, pady=3)

            tk.Label(card, text=name, font=("Helvetica", 11, "bold"),
                     bg=BG, fg=TEXT, anchor="w").pack(fill=tk.X)
            tk.Label(card, text="Station ID: " + str(self.stations[name]),
                     font=("Helvetica", 8), bg=BG, fg=SUBTEXT, anchor="w").pack(fill=tk.X)

            self.station_cards[name] = card

            for widget in [card] + card.winfo_children():
                widget.bind("<Button-1>", lambda e, n=name: self.select_station(n))
                widget.configure(cursor="hand2")

        self.select_station("Alameda", silent=True)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, pady=4)

        tk.Label(parent, text="SUMMARY", font=("Helvetica", 8),
                 bg=SURFACE, fg=SUBTEXT).pack(anchor="w", padx=14, pady=(10, 2))

        grid = tk.Frame(parent, bg=SURFACE)
        grid.pack(fill=tk.X, padx=14, pady=(0, 10))

        self.stat_labels = {}
        stat_info = [("avg", "Average"), ("max", "Maximum"),
                     ("min", "Minimum"), ("std", "Std Dev")]

        for i in range(len(stat_info)):
            key   = stat_info[i][0]
            label = stat_info[i][1]
            col   = i % 2
            row   = i // 2

            cell = tk.Frame(grid, bg=BG, padx=8, pady=6,
                            highlightthickness=1, highlightbackground=BORDER)
            cell.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            grid.columnconfigure(col, weight=1)

            tk.Label(cell, text=label.upper(), font=("Helvetica", 7),
                     bg=BG, fg=SUBTEXT).pack(anchor="w")
            val_label  = tk.Label(cell, text="—", font=("Georgia", 18, "italic"),
                                  bg=BG, fg=TEXT)
            val_label.pack(anchor="w")
            unit_label = tk.Label(cell, text="", font=("Helvetica", 8),
                                  bg=BG, fg=SUBTEXT)
            unit_label.pack(anchor="w")

            self.stat_labels[key] = (val_label, unit_label)


    def build_main(self, parent):
        chart_header = tk.Frame(parent, bg=BG, pady=8, padx=16)
        chart_header.pack(fill=tk.X)
        self.chart_title_label = tk.Label(chart_header,
            text="Select parameters and click Get Data",
            font=("Helvetica", 10), bg=BG, fg=SUBTEXT)
        self.chart_title_label.pack(side=tk.LEFT)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X)

        chart_frame = tk.Frame(parent, bg=BG)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self.figure, self.ax = plt.subplots(figsize=(9, 4))
        self.figure.tight_layout(pad=2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def make_button(self, parent, text, command, color):
        if color == ACCENT:
            fg = "white"
        else:
            fg = TEXT
        return tk.Button(parent, text=text, command=command,
                         bg=color, fg=fg, activebackground=color,
                         activeforeground=fg, relief="flat",
                         font=("Helvetica", 9, "bold"),
                         padx=10, pady=6, cursor="hand2", borderwidth=0)


    def select_station(self, name, silent=False):
        self.station_var.set(name)
        for n, card in self.station_cards.items():
            if n == name:
                card.configure(bg="#dbeafe", highlightbackground=ACCENT)
                for child in card.winfo_children():
                    child.configure(bg="#dbeafe")
            else:
                card.configure(bg=BG, highlightbackground=BORDER)
                for child in card.winfo_children():
                    child.configure(bg=BG)
        if not silent:
            self.set_status("Station: " + name + "  [" + str(self.stations[name]) + "]", SUCCESS)


    def get_data(self):
        try:
            days_back = int(self.time_range_var.get())
            if days_back < 1 or days_back > 31:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Days must be a number between 1 and 31.")
            return

        product      = self.products[self.product_var.get()]
        station_name = self.station_var.get().replace(" ", "_").lower()

        start_date = pd.to_datetime("today") - pd.Timedelta(days=days_back)
        begin_date = start_date.strftime("%Y%m%d")
        end_date   = pd.to_datetime("today").strftime("%Y%m%d")

        filename   = station_name + "_" + product + "_" + begin_date + "_" + end_date + ".csv"
        local_path = os.path.join(self.data_folder, filename)

        if os.path.exists(local_path):
            self.df = pd.read_csv(local_path)
            self.df["time"] = pd.to_datetime(self.df["time"])
            self.filtered_df = self.df
            self.update_plot()
            self.update_summary()
            self.set_status("Loaded from cache: " + filename, SUCCESS)
            return

        # Fetch from NOAA API
        url    = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        station = str(self.stations[self.station_var.get()])

        params = {
            "product": product,
            "application": "noaa_visualizer",
            "begin_date": begin_date,
            "end_date": end_date,
            "station": station,
            "time_zone": "gmt",
            "units": "metric",
            "format": "json",
        }

        if product == "water_level":
            params["datum"] = "MLLW"
        if product == "predictions":
            params["datum"]    = "MLLW"
            params["interval"] = "h"

        try:
            response = requests.get(url, params=params, timeout=15)
            data     = response.json()
        except Exception as e:
            self.handle_error("Network error: " + str(e))
            return

        if "error" in data:
            self.handle_error(data["error"]["message"])
            return
        if "data" in data:
            df = pd.DataFrame(data["data"])
        elif "predictions" in data:
            df = pd.DataFrame(data["predictions"])
        else:
            self.set_status("No data returned.", ERROR)
            return

        if "t" not in df.columns:
            self.set_status("Unexpected data format.", ERROR)
            return

        if "v" in df.columns:
            value_col = "v"
        else:
            value_col = None
            for col in df.columns:
                if col != "t":
                    value_col = col
                    break

        if value_col is None:
            self.set_status("No value column found.", ERROR)
            return

        df = df.rename(columns={"t": "time", value_col: "value"})
        df["time"]  = pd.to_datetime(df["time"],  errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna()

        self.df          = df
        self.filtered_df = df
        self.update_plot()
        self.update_summary()

        # Save to CSV
        try:
            self.df.to_csv(local_path, index=False)
            self.set_status("Saved: " + filename, SUCCESS)
        except Exception as e:
            self.set_status("Save failed: " + str(e), ERROR)

    def update_plot(self):
        self.ax.clear()

        if self.filtered_df.empty:
            self.ax.set_title("No data available", color=SUBTEXT)
            self.canvas.draw()
            return

        x        = self.filtered_df["time"]
        y        = self.filtered_df["value"]
        category = self.product_var.get()

        self.ax.plot(x, y, color=ACCENT, linewidth=1.2, label="Data", alpha=0.9)
        self.ax.fill_between(x, y, alpha=0.08, color=ACCENT)
        self.ax.set_title(category, fontsize=11, pad=10)
        self.ax.set_xlabel("Time", labelpad=6)
        self.ax.set_ylabel("Value", labelpad=6)
        self.ax.grid(True, alpha=0.3)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=7))
        self.ax.tick_params(axis="x", rotation=25)

        if "Temperature" in category:
            z = np.polyfit(mdates.date2num(x), y, 1)
            #self.ax.plot(x, np.poly1d(z)(mdates.date2num(x)),
             #            color=ACCENT2, linestyle="--", linewidth=1.5,
              #           label="Trend", alpha=0.7)
            self.ax.plot(x, np.poly1d(z)(mdates.date2num(x)),
                         color='red', linestyle="--", linewidth=1.5,
                         label="Trend", alpha=0.7)
        elif "Water Level" in category:
            trend = y.rolling(window=240, center=True, min_periods=1).mean()
            self.ax.plot(x, trend, color='red', linewidth=1.8,
                         linestyle="--", label="24 h Mean", alpha=0.7)

        self.ax.legend()
        self.figure.tight_layout(pad=2)
        self.canvas.draw()
        self.chart_title_label.config(
            text=category + "  ·  " + self.station_var.get(), fg=TEXT)

    def update_summary(self):
        if self.filtered_df.empty:
            for key in self.stat_labels:
                self.stat_labels[key][0].config(text="—")
                self.stat_labels[key][1].config(text="")
            return

        v = self.filtered_df["value"]

        if "Temperature" in self.product_var.get():
            unit = "°C"
        else:
            unit = "m"

        values = {
            "avg": v.mean(),
            "max": v.max(),
            "min": v.min(),
            "std": v.std()
        }

        for key in self.stat_labels:
            val_label  = self.stat_labels[key][0]
            unit_label = self.stat_labels[key][1]
            val_label.config(text=str(round(values[key], 2)))
            unit_label.config(text=unit)

    def open_visualization_window(self):
        if self.filtered_df.empty:
            messagebox.showwarning("No Data", "Please load data before opening visualizations.")
            return

        win = tk.Toplevel(self.root)
        win.title("Advanced Visualizations")
        win.geometry("1200x900")
        win.configure(bg=BG)

        y = self.filtered_df["value"].reset_index(drop=True)
        x = self.filtered_df["time"].reset_index(drop=True)

        fig, axes = plt.subplots(2, 2, figsize=(14, 9))
        fig.patch.set_facecolor(SURFACE)
        fig.subplots_adjust(hspace=0.6, wspace=0.32,
                            top=0.93, bottom=0.16, left=0.07, right=0.97)

        ax1 = axes[0, 0]
        ax2 = axes[0, 1]
        ax3 = axes[1, 0]
        ax4 = axes[1, 1]

        def format_xaxis(ax):
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            ax.tick_params(axis="x", rotation=30, labelsize=8)

        #Smoothed signal
        ax1.plot(x, y, color=ACCENT, alpha=0.4, linewidth=0.7, label="Raw")
        if len(y) >= 13:
            win_len = len(y) if len(y) % 2 == 1 else len(y) - 1
            win_len = min(51, win_len)
            smoothed = savgol_filter(y, window_length=win_len, polyorder=3)
            ax1.plot(x, smoothed, color=ACCENT, linewidth=2, label="Smoothed")
        ax1.set_title("Smoothed Signal")
        format_xaxis(ax1)
        ax1.legend()

        #Value distribution
        ax2.hist(y, bins=30, color=ACCENT, edgecolor=BG, alpha=0.85)
        ax2.axvline(y.mean(), color='red', linestyle="--", linewidth=1.5,
                    label="Mean: " + str(round(y.mean(), 2)))
        ax2.set_title("Value Distribution")
        ax2.tick_params(axis="x", labelsize=8)
        ax2.legend()

        #Seasonal decomposition
        try:
            if len(y) >= 48:
                result = seasonal_decompose(y, model="additive",
                                            period=24, extrapolate_trend="freq")
                ax3.plot(x, result.trend, color='red', linewidth=1.5, label="Trend")
                ax3.fill_between(x, result.trend, alpha=0.08, color=ACCENT2)
                ax3.legend()
            else:
                ax3.text(0.5, 0.5, "Need at least 48 data points",
                         ha="center", va="center", transform=ax3.transAxes,
                         color=SUBTEXT, fontsize=10)
        except Exception as e:
            ax3.text(0.5, 0.5, str(e), ha="center", va="center",
                     transform=ax3.transAxes, fontsize=8, color=ERROR)
        ax3.set_title("Seasonal Trend")
        format_xaxis(ax3)

        #Mean +/- std dev
        mean_val = y.mean()
        std_val  = y.std()
        ax4.plot(x, y, color='orange', alpha=0.4, linewidth=0.7, label="Data")
        ax4.axhline(mean_val, color=ACCENT, linewidth=1.5,
                    label="Mean: " + str(round(mean_val, 2)))
        ax4.axhline(mean_val + std_val, color='red', linewidth=1.1,
                    linestyle="--", label="+/-1 SD: " + str(round(std_val, 2)))
        ax4.axhline(mean_val - std_val, color='red', linewidth=1.1, linestyle="--")
        ax4.fill_between(x, mean_val - std_val, mean_val + std_val,
                         color=ACCENT, alpha=0.08)
        ax4.set_title("Mean +/- Std Dev")
        format_xaxis(ax4)
        ax4.legend()

        for ax in axes.flat:
            ax.grid(True, alpha=0.25)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.make_button(win, "Close", win.destroy, BORDER).pack(pady=8)

    def set_status(self, message, color=None):
        if color is None:
            color = TEXT
        if color == SUCCESS:
            indicator = "●  "
        elif color == ERROR:
            indicator = "⚠  "
        else:
            indicator = "○  "
        self.status_label.config(text=indicator + message, fg=color)

    def handle_error(self, message):
        self.filtered_df = pd.DataFrame()
        self.update_plot()
        self.set_status(message, ERROR)
        messagebox.showerror("Error", message)


if __name__ == "__main__":
    root = tk.Tk()
    app  = DataApp(root)
    root.mainloop()