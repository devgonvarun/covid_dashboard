import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark import Session
#from snowflake.snowpark.context import get_active_session


st.sidebar.title("Covid Dashboard :microbe:")

col1, col2 = st.columns(2)

# Get the current session credentials
#session = get_active_session()

@st.cache_resource
def create_session():
    return Session.builder.config("connection_name", "default").create()

@st.cache_data
def load_df():
    # Query data from Snowflake using raw SQL
    session = create_session()
    created_dataframe = session.sql("""
    SELECT 
        COUNTRY AS country,
        TOTAL_CASES AS total_cases,
        CASES_NEW AS new_cases,
        DEATHS AS total_deaths,
        DEATHS_NEW AS new_deaths,
        TRANSMISSION_CLASSIFICATION AS transmission_type,
        DATE AS date
    FROM COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.WHO_SITUATION_REPORTS
    """)
    return created_dataframe.to_pandas()

df = load_df()
df.columns = df.columns.str.lower()

df['transmission_type'] = df['transmission_type'].apply(
    lambda x: 'Cluster' if str(x).lower().startswith('clus') 
    else 'Community' if str(x).lower().startswith('com') 
    else 'Local' if str(x).lower().startswith('loc')
    else 'Pending' if str(x).lower().startswith('pen')
    else 'Other'
)

# Use multiselect in the sidebar to let the user select countries
selected_countries = st.sidebar.multiselect(
    label="Countries",
    label_visibility = "hidden",
    options=sorted(df['country'].unique()),
    max_selections=10,
    default=["Austria", "Czechia", "Poland"],
    placeholder="Choose Countries to compare"
)

# Filter the DataFrame based on the selected countries
if selected_countries:
    filtered_df = df[df['country'].isin(selected_countries)].copy()
else:
    filtered_df = pd.DataFrame(columns=df.columns)


chart_choice = st.sidebar.radio(
    "",
    ["Cases", "Deaths"],
    horizontal=True
)

y_column = "new_cases" if chart_choice == "Cases" else "new_deaths"

on = st.sidebar.toggle("per million population")

if on:
    st.sidebar.write("To do!")

# Proceed only if the filtered DataFrame is not empty
if not filtered_df.empty:

    # Ensure the date column is in datetime format
    filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    
    # Get the sorted unique dates from the filtered DataFrame
    months = sorted(filtered_df['date'].unique())
    
    # Convert the timestamps to date objects for the date_input widget
    min_date = months[0].date()
    max_date = months[-1].date()
    
    # Create a date range input in the sidebar
    selected_duration = st.sidebar.date_input(
        "",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )
    
    # Check if both start and end dates are provided.
    # If the user has not selected both dates, show an info message and stop further execution.
    if not (isinstance(selected_duration, (tuple, list)) and len(selected_duration) == 2):
        st.sidebar.info("Please select both start and end dates to proceed.")
        st.stop()
    
    # Unpack the start and end dates from the input
    start_date, end_date = selected_duration
    
    # Convert the selected dates back to pandas timestamps for filtering
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filter the DataFrame to include only rows within the selected date range
    filtered_df = filtered_df[
        (filtered_df['date'] >= start_date) & 
        (filtered_df['date'] <= end_date)
    ]

    summary_df = filtered_df.groupby('country', as_index=False).agg({
        'new_cases': 'sum',
        'new_deaths': 'sum'
    })

    chart = (
        alt.Chart(summary_df)
        .mark_bar()
        .encode(
            x=alt.X("country:N", sort="-y", title=""),  # Sort by y values in descending order
            y=alt.Y(y_column, title=chart_choice),
            color=alt.Color("country:N", legend=None),  # Remove legend if unnecessary
            tooltip=["country", y_column]  # Add tooltip for better interactivity
        )
        .properties(height=200)
    )
    
    with col1: 
        st.altair_chart(chart, use_container_width=True)

    with col2: 
        heatmap = alt.Chart(filtered_df).mark_rect().encode(
            x=alt.X('date:T', title=""),
            y=alt.Y('country:N', title=""),
            color=alt.Color(f"{y_column}:Q", title=""),
            tooltip=['country', 'date', 'new_cases']
        ).properties(
            height=167
        )
        st.altair_chart(heatmap, use_container_width=True)

    st.line_chart(filtered_df, x="date", x_label="", y=y_column, y_label=chart_choice, color="country", height=230)

    st.bar_chart(filtered_df, x="country", x_label="", y="new_cases", y_label="", color="transmission_type", stack="normalize", horizontal=True)