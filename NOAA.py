import tkinter as tk
from tkinter import ttk
import requests
import panda as pd
import numpy as np
import matplotlib.pyplot as plt

class DataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NOAA Coastal Data Visualizer")
        self.station_id = "9414290"
        
        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()

        self.products ={
            "Water Temperature": "water_temperature"
            "Water Level": "water_level"
            "Tide Predictions": "predictions"
        }
        tk.Label(root, text="Ocean Data Dashboard", font=("Time New Roman", 16)).pack(pady=10)
        tk.Label(root, text="Station ID: 9414290").pack()
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="Data type").grid(row=0, column=0, padx=5)

        self.product_var = tk.StringVar(value="Water Temperature")
        self.product_menu = ttk.Combobox(
            control_frame,
            textvariable=self.product_var,
            values=list(self.products.keys()),
            state="readonly"
        )
        self.product_menu.grid(row=1, column=0, padx=5)
         self.get_button = tk.Button(control_frame, text="Get Data", command=self.get_data)
        self.get_button.grid(row=2, column=0, padx=5)

        self.filter_button = tk.Button(control_frame, text="Filter", command=self.open_filer_window)
        self.filter_button.grid(row=1, column=2, padx=5)

        self.figure, self.ax = plt.subplots(figsize=(6,3))
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(pady=10)

        self.summary_label = tk.Label(root, text="No data")
        self.summary_label.pack(pady=10)

        self.status_label = tk.Label(root, text="Ready")
        self.status_label.pack(pady=5)

    def get_data(self):
        product = self.products[self.product_var.get()]
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

        params = {
            "product": product,
            "application": "test",
            "begin_date": "20260301",
            "end_date": "20260302",
            "station": self.station_id,
            "time_zone": "gmt",
            "units": "metric",
            "format": "json"
        }

