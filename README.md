# cs122_Project
Title: NOAA Coastal Data Visualizer 
Author: Dan Nguyen, Joyce Liu

## Description:
A Python based interface that retrieves real-time ocean data from NOAA, analyzes it, and visualizes it for users. The goal is to allow users to explore ocean conditions such as water temperature and sea level through an interactive GUI.
It is easy to fetch, filter, and understand ocean data without needing to manually process raw datasets.

## Outline/Plan:
- Retrive live ocean data from NOAA API
- Interactive GUI built using Tkinter
- Select station and data type
- Filter Data using data range
- Data analysis:
	- Average
	- Maximum
	- Minimum
-Visualization using line plots
## Data Collection:
- The data for this is collected from the NOAA Tides and Currents API, which provides publicly available oceanographic data such as water temperature and water level measurements.
- The programs sends HTTP requests to NOAA API using requests library.
- The API returns the data in JSON format, which is then parsed and converted into a structured format
## Data Processing:
- The retrieved JSON data is converted into a Pandas DataFrame for easier manipulation and analysis. 
- Steps:
	- Converting string values to numeric types
	- Handling missing or invalid data
	- Formatting timestamps if needed
## Data Storage:
- The processed data is stored locally as CVS file to allow reuse without repeatedly calling the API. This improves effieciency and reduces dependency on netwoek requests. 
- Dataset is saved with descriptive filename: Station ID, Data type, Data range
eg. monterey_water_temp_20260301_20260302.csv
## Data Updating:
- When the user requests new data or changes parameters, the program fetches updated data from the API and overwrites or creates a new CSV file.
- This will ensures the application always works with most recent and relevant data while maintaining a consistent data structure for analysis and visualization.	
