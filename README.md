# cs122_Project
## Title: NOAA Coastal Data Visualizer 
## Author: Dan Nguyen, Joyce Liu

## Description:
A Python-based interface that retrieves real-time ocean data from NOAA, stores it, analyzes it, and visualizes it for users. The goal is to allow users to explore ocean conditions such as water temperature and sea level through an interactive GUI. Users can select a station, data type, and data range. The data retrieved and stored based on the user input will be analyzed and visualized by the application. It is easy to fetch, filter, and understand ocean data without needing to manually process raw datasets. 

## Outline/Plan:
- Retrieve live ocean data from NOAA API
- Interactive GUI built using Tkinter
- Select station and data type
- Filter Data using data range
- Calculate average, maximum, and minimum values based on data
- Visualize data using time series plots
## Interface Plan
- Build a graphic user interface (GUI) with Python's Tkinter library
- Home screen:
	- Drop-down window to select an ocean condition 
	- Drop-down window to select a station
	- Input boxes to enter data range
	- Enter button
- Pop-up window
	- Show data analysis
	- Show data visualization 
## Data Collection:
- The data for this is collected from the NOAA Tides and Currents API, which provides publicly available oceanographic data such as water temperature and water level measurements.
- The program sends HTTP requests to the NOAA API using the requests library.
- The API returns the data in JSON format, which is then parsed and converted into a structured format
## Data Processing:
- The retrieved JSON data is converted into a Pandas DataFrame for easier manipulation and analysis. 
- Steps:
	- Converting string values to numeric types
	- Handling missing or invalid data
	- Formatting timestamps if needed
## Data Storage:
- The processed data is stored locally as a CSV file to allow reuse without repeatedly calling the API. This improves efficiency and reduces dependency on network requests. 
- Dataset is saved with descriptive filename: Station ID, Data type, Data range
eg. monterey_water_temp_20260301_20260302.csv
## Data Updating:
- When the user requests new data or changes parameters, the program fetches updated data from the API and overwrites or creates a new CSV file.
- This will ensure the application always works with the most recent and relevant data while maintaining a consistent data structure for analysis and visualization.	
## Data Analysis:
- The application will calculate the average, maximum, minimum values, and trends in the data requested by the user. 
- This will allow users to identify environmental extremes and better understand the conditions at a particular station over a range of time.
## Visualization:
- The application will visualize the data with time series plot(s).
- This will allow users to see changes in ocean conditions, like water temperature and sea level, over time. 
