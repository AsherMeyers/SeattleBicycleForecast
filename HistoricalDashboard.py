from os.path import dirname, join
from datetime import datetime, date
import pandas as pd
from bokeh.layouts import row, widgetbox, layout
from bokeh.models import ColumnDataSource,CheckboxButtonGroup, CustomJS, DatetimeTickFormatter, FuncTickFormatter
from bokeh.models.widgets import Select, DateRangeSlider, RadioGroup, RangeSlider, Button, DataTable, TableColumn, DateFormatter
from bokeh.io import curdoc
from urllib.request import urlopen
from bokeh.plotting import figure
from bokeh.io import output_file, show
import numpy as np

#cd C:\Users\asher\Documents\GitHub\data602-finalproject 
#bokeh serve HistoricalDashboard.py --show


# Colors for plotting Counters
colors = ['red', 'green', 'blue', 'orange', 'black', 'grey', 'brown',
                   'cyan', 'yellow', 'purple']

# Weather Coding Dictionary
weatherDict = {0:"None", 
               1: "Fog", 
               2: "Rain", 
               3: "Snow",
               4:"Thunderstorm"}

# Get dataframe of historical observations, weather, and daylight hours
#histPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/histDF.csv"
#weatherPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/weatherDF.csv"
#daylightPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/daylightDF.csv"

# Local path for testing
histPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/histDF.csv"
weatherPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/weatherDF.csv"
daylightPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/daylightDF.csv"

#jsPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/download.js"

histDF = pd.read_csv(histPath, index_col = 0) # From Seattle Data Portal
weatherDF = pd.read_csv(weatherPath, index_col = 0) # From WeatherUnderground
daylightDF = pd.read_csv(daylightPath, index_col = 0) # From jakevdp formula

# Set indices of hist and weather as datetime & date objects, respectively
Indx = [] # Index to house dates
for i in range(len(histDF)): 
    Indx.append(datetime.strptime(histDF.index[i], '%m/%d/%Y %H:%M'))
histDF.index = Indx

Indx = [] # Index to house dates
for i in range(len(weatherDF)): 
    Indx.append(datetime.strptime(weatherDF.index[i], '%Y-%m-%d').date())
weatherDF.index = Indx

Indx = [] # Index to house dates
for i in range(len(daylightDF)): 
    Indx.append(datetime.strptime(daylightDF.index[i], '%Y-%m-%d').date())
daylightDF.index = Indx

MyTools = "pan,wheel_zoom,box_zoom,reset,undo,save"

def subsetMonth(monthList, df=histDF):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.month.isin(monthList)]

def subsetWeekday(daylist, df=histDF):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.weekday.isin(daylist)]

def subsetHours(start, end, df=histDF):
    # Return dataframe within the times specified, in 24 hour format
    # e.g. start = '12:00', end = '13:00'
    start = str(int(start)) + ":00"
    end = str(int(end)) + ":00"
    df = df.between_time(start, end)
    return df

def subsetRain(low = 0, high = 2.5, wdf = weatherDF, df = histDF):
    # Subset histDF by specified rain volume, inches per day
    
    dfDates = pd.Series(df.index.date) # All dates in dataset
    
    filterDates = [] # List to store dates meeting filters
    
    # Create list of lists of dates satisfying filters
    filterDates = wdf[(wdf.Precip >= low) & 
                      (wdf.Precip <= high)].index 
        
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))
    
    # Return dataframe containing only the dates that meet the filter criteria    
    return df[filterBools]

def subsetWeather(weatherList, wdf = weatherDF, df = histDF):
    # Return dataframe containing only dates where the specified weather events
    # occurred. Eg, subsetWeather(["Rain", "Snow"]) returns all counts from days
    # on which it rained or snowed. If no events, string should be "None"
    # 
    # Note, if there were also fog on a given day, 
    # that date would show up in the returned dataframe.
    
    # Set weather Events field null values to empty strings
    wdf.Events = wdf.Events.replace(np.nan, 'None', regex=True)
    
    # Dates with the specified weather conditions
    dfDates = pd.Series(df.index.date) # All dates in dataset
    
    filterDates = [] # List to store dates meeting filters
    
    # Create list of lists of dates satisfying filters
    for event in weatherList:
        filterDates.append(wdf.index[wdf['Events'].str.contains(event)])
    
    # Convert list of lists into flat list
    filterDates = [item for sublist in filterDates for item in sublist]
    
    # Sort dates list
    filterDates.sort()    
        
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))
    
    # Create new dataframe containing only the dates that meet the filter criteria
    filterDF = df[filterBools]
    
    return filterDF

def subsetDaylight(df = histDF, ddf = daylightDF, low=8, high=16):
    # Function for filtering dataset by hours of sunlight for each date
    
    # Create list of dates that meet filter criteria
    filterDates = ddf[(ddf.daylightHours >= low) & 
                      (ddf.daylightHours <= high)].index
    
    dfDates = pd.Series(df.index.date) # All dates in dataset
     
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))

    # Return dataframe containing only the dates that meet the filter criteria    
    return df[filterBools] 

def plotTypicalDay(df = histDF): 
    
    # Aggregate data by hour of the day
    df = df.groupby([df.index.hour])[df.columns].mean()
    
    # Create x-axis values from index which contains hours
    xs = df.index*1000*60*60 # Convert milliseconds to hours
        
    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Count By Hour for One Day")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(hours = '%a %-I %p')
    
    # show(p)
    return p

def plotTypicalWeek(df = histDF): 
    # Plots average count by hour and day of week
    
    # Aggregate data by day of the week and hour
    df = df.groupby([df.index.weekday, df.index.hour])[df.columns].mean()

    # Create x-axis values from index which contains hours
    #xs = pd.Series(range(len(df)))*1000*60*60 # Convert milliseconds to hours
    xs = (np.array(range(len(df))) + 4*24)*1000*60*60
    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Count By Hour, for One Week")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(hours = '%a %-I %p',
                                                     days = '%a')
    
    show(p)
    return

def plotTypicalYear(df = histDF):
    # Plots average count of one full typical year

    # Aggregate data by day of the week and hour
    df = df.groupby([df.index.week])[df.columns].mean()

    # Create x-axis values from index which contains hours
    xs = (df.index - 1) * 1000*60*60*24*7

    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Counts By Week, for One Year")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(months = '%B')
    show(p)
    return

def plotHistory(df = histDF):
    # Plots entire history
    
    # Downsample into one week segments
    df = df.resample('7d').sum()

    p = figure(plot_width = 800, tools = MyTools, 
               title = "Historical Bicycle Counts By Week")
    for i in range(len(df.columns)):
        p.line(x = df.index,y = df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(months = '%B',
                                                     years = '%Y')
    show(p)
    return 

def TypicalDay(df = histDF):
    df = df.groupby([df.index.hour])[df.columns].mean()
    return df

def TypicalWeek(df = histDF):
    df = df.groupby([df.index.weekday, df.index.hour])[df.columns].mean()
    
    indx = np.array([])
    for i in range(len(df.index)):
        indx = np.append(indx, df.index[i][0]*24 + df.index[i][1] + 4*24)
    
    df.index = indx
    return df

# Set up data
mydf = TypicalDay()  
x =  np.array(mydf.index)*1000*60*60
#x = list(np.array(range(24))*1000*60*60)
y = mydf.Fremont
source = ColumnDataSource(data=dict(x=x, y=y))

# Set up plot
plot = figure(plot_height=600, plot_width=750, title="Bicycle Counts",
              tools=MyTools, y_range=[0,700])
              #x_range=[0, 23]
plot.xaxis.axis_label = "Hour of the Day" # x axis label
#plot.xaxis.ticker = list(np.array([0, 6, 8, 10, 12, 14, 16, 18, 20, 
#                              22]*1000*60*60)) # x axis tick marks
plot.xaxis.formatter = DatetimeTickFormatter(hours = ['%I %p'], days = ['%a'])
plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)


# Widgets section

# Drop down for selecting viewing a typical week or typical day
ViewDropdown = Select(title = "View by Average...", value = "Day",
              options = ["Day", "Week", "Year", "Historical"])

CounterRadio = RadioGroup(labels = list(histDF.columns), 
                                   active = 3)

DateSlider = DateRangeSlider(title="Date range", value=(date(2013, 10, 3), 
                            date(2017, 10, 31)), start=date(2013, 10, 3), 
                            end=date(2017, 10, 31), step=1)

MonthBoxes = CheckboxButtonGroup(labels = ["Jan.", "Feb.", "March", "April", 
                                           "May", "June", "July", "Aug.", "Sep.",
                                           "Oct.", "Nov.", "Dec."], 
                                 active = list(range(12)))
WeekdayBoxes = CheckboxButtonGroup(labels = ["Monday", "Tuesday", "Wednesday",
                                              "Thursday", "Friday", "Saturday",
                                              "Sunday"], 
                                   active=list(range(5)))
HourSlider = RangeSlider(title="Hour Range", start=0, end=23, value=(0, 23), 
                         step=1, format='0')

DaylightSlider = RangeSlider(title = "Hours of Daylight", start = 8, end = 16, 
                             value = (8,16), step = 1, format = "0")

WeatherBoxes = CheckboxButtonGroup(labels = ["None", "Fog", "Rain", "Snow", 
                                             "Thunderstorm"], 
                                   active = [0,1,2,3,4])

RainSlider = RangeSlider(title="Inches of Rain per Day", start = 0, end = 2.5, 
                         value = (0,3), step = 0.05, format = "0.00")

# Set up callbacks
def update_data(attrname, old, new):

    # Get the current slider values
    view = ViewDropdown.value
    counter = CounterRadio.active
    dates = DateSlider.value
    months = MonthBoxes.active
    weekdays = WeekdayBoxes.active
    hours = np.round(HourSlider.value)
    weather = WeatherBoxes.active
    light = DaylightSlider.value
    rain = RainSlider.value

    # Translate weather list of ints to list of strings, eg ["Fog", "Rain"]
    weatherList = []
    for i in weather: weatherList.append(weatherDict[i])

    # Generate the new dataframe
    mydf = histDF.copy(deep = True)
    mydf = mydf.loc[dates[0]:dates[1]] # Subset dates 
    mydf = mydf[mydf.index.month.isin(months)] # Subset months
    mydf = mydf[mydf.index.weekday.isin(weekdays)] # Subset weekdays 
    mydf = subsetHours(start = hours[0], end = hours[1], df = mydf) # Subset hours
    mydf = subsetDaylight(df = mydf, low = light[0], high = light[1])
    mydf = subsetWeather(weatherList, df = mydf)
    mydf = subsetRain(df = mydf, low = rain[0], high = rain[1])
    
    if view == "Week":
        mydf = TypicalWeek(df = mydf)
    else:
        mydf = TypicalDay(df = mydf)
        
    x =  np.array(mydf.index)*1000*60*60 # Convert ms to hours
    y = mydf.iloc[:, counter].astype(float)
    
    #x =  np.array(mydf.index)*1000*60*60 # Convert ms to hours
    
    #x = range(int(hours[0]),int(hours[1] + 1)) 
    #y = TypicalDay(mydf).iloc[:, counter].astype(float)
    #x = np.array(range(int(hours[0]),int(hours[1] + 1)))*7
        
    source.data = dict(x=x, y=y)
    
for w in [ViewDropdown, DateSlider, HourSlider, DaylightSlider, RainSlider]:
    w.on_change('value', update_data)
    
for z in [MonthBoxes, WeekdayBoxes, WeatherBoxes, CounterRadio]:
    z.on_change('active', update_data)

# Set up layouts and add to document
inputs = widgetbox(ViewDropdown, CounterRadio, DateSlider, MonthBoxes, WeekdayBoxes, 
                   HourSlider, DaylightSlider, WeatherBoxes, RainSlider)


lay = layout([
        [inputs, plot]
        ], sizing_mode = 'fixed')
#curdoc().add_root(row(inputs, plot, width=800))
curdoc().add_root(lay)    
curdoc().title = "Bicycle Counts"

