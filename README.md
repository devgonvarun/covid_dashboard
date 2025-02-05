# Covid Dashboard

This Streamlit app compares selected countries over a chosen time period for COVID-19 cases and deaths, pulling data directly from a Snowflake Marketplace dataset.

## How It Works

- **Session & Data:** Establishes a Snowflake session to run a SQL query and loads data into a Pandas DataFrame.
- **Data Processing:** Cleans and categorizes data and filters based on user selections.
- **Visualization:** Uses Altair and built-in Streamlit charts to display trends in new cases and deaths.

## Running the App

### Directly with Streamlit

streamlit run covid_dashboard.py

## Running the App from a Docker image

docker run -v ~/.snowflake:/home/appuser/.snowflake -p 8080:8080 covid_docker