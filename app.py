import streamlit as st
import pandas.io.sql as sqlio
import altair as alt
import folium
from streamlit_folium import st_folium
import pandas as pd

from db import conn_str

st.title("Seattle Events")

df = sqlio.read_sql_query("SELECT * FROM events", conn_str)

# 1-a. What category of events are most common in Seattle?
st.subheader('💡 What category of events are most common in Seattle?')
st.altair_chart(
    alt.Chart(df).mark_bar().encode(x="count()", y=alt.Y("category").sort('-x')).interactive(),
    use_container_width=True,
)

# 1-b. What month has the most number of events?
st.subheader('💡 What month has the most number of events?')
df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year
# Group by month and year, then count the number of events
monthly_events = df.groupby(['year', 'month']).size().reset_index(name='counts')
# Create a new column for displaying the month and year together for better clarity
monthly_events['month_year'] = monthly_events['month'].astype(str) + '/' + monthly_events['year'].astype(str)

chart = alt.Chart(monthly_events).mark_bar().encode(
    x=alt.X('month_year:N', sort='-y', title='Month-Year'),
    y=alt.Y('counts:Q', title='Number of Events'),
    tooltip=['month_year', 'counts']
).interactive()
st.altair_chart(chart, use_container_width=True)

# 1-c. What day of the week has the most number of events?
st.subheader('💡 What day of the week has the most number of events?')
df['date'] = pd.to_datetime(df['date'])
df['day_of_week'] = df['date'].dt.day_name()
day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
df['day_of_week_num'] = df['day_of_week'].map(day_order)
weekly_events = df.groupby(['day_of_week', 'day_of_week_num'], as_index=False).size()
weekly_events = weekly_events.sort_values('day_of_week_num')

chart = alt.Chart(weekly_events).mark_bar().encode(
    x=alt.X('day_of_week:N', sort=alt.SortField('day_of_week_num', order='ascending'), title='Day of the Week'),
    y=alt.Y('size:Q', title='Number of Events'),
    tooltip=['day_of_week', 'size']
).interactive()

st.altair_chart(chart, use_container_width=True)

# Create a copy of the DataFrame for filtering
filtered_df = df.copy()

# 2-a. Dropdown to Filter by Category
categories = df['category'].unique()
selected_category = st.selectbox("Select a category", options=categories)

# Apply category filter immediately
filtered_df = filtered_df[filtered_df['category'] == selected_category]

# 2-b. Date Range Selector for Event Date
min_date = df['date'].min().date()
max_date = df['date'].max().date()
selected_date_range = st.date_input("Select date range", value=[min_date, max_date], min_value=min_date, max_value=max_date)

# Apply date range filter
filtered_df = filtered_df[(filtered_df['date'].dt.date >= selected_date_range[0]) & (filtered_df['date'].dt.date <= selected_date_range[1])]

# 2-c. Dropdown to Filter by Location
locations = ['All'] + list(df['location'].unique())
selected_location = st.selectbox("Select a location", options=locations)

if selected_location != 'All':
    filtered_df = filtered_df[filtered_df['location'] == selected_location]

# 2-d. (Optional) Filter by Weather Condition
weather_conditions = ['All'] + list(df['weathercondition'].unique())
selected_weather_condition = st.selectbox("Select a weather condition", options=weather_conditions)

if selected_weather_condition != 'All':
    filtered_df = filtered_df[filtered_df['weathercondition'] == selected_weather_condition]

# Display the filtered DataFrame
st.write(filtered_df)


m = folium.Map(location=[47.6062, -122.3321], zoom_start=12)
folium.Marker([47.6062, -122.3321], popup='Seattle').add_to(m)
st_folium(m, width=1200, height=600)