import streamlit as st
import pandas as pd
import seaborn as sns
import mysql.connector as db
import matplotlib.pyplot as plt

# Streamlit

st.set_page_config(page_title= "SecureCheck Dashboard", layout="wide")
st.title("Digital Ledger For Police Post Logs")

st.markdown("Real-Time Monitoring System")

#Show table

st.header("Police Post Logs Overview")
df = pd.read_csv("seccheck_data.csv")
data = df.head(1000)

data.drop(["driver_age_raw","violation_raw"],axis = 1,inplace = True)
st.table(data)


# Database connection

def create_connection():
    try:
        connection = db.connect(
            host = "localhost",
            user = "root",
            password = "sandy2505",
            database = "db1"
        )
        return connection
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None
    
# Fetch data from database

def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                df = pd.DataFrame(result)
                return df
        finally:
                connection.close()
    else:
        return pd.DataFrame()
    
    
# Quick Metrics
st.header("Key Metrics")

col1, col2, col3, col4 =st.columns(4)

with col1:
    total_stops = df.shape[0]
    st.metric("Total police stops", total_stops)    
with col2:
    drug_related = df[df['drugs_related_stop'] == 1].shape[0]
    st.metric("Drug related stops", drug_related)    
with col3:
    arrests = df[df['stop_outcome'].str.contains("arrest", case=False, na=False)].shape[0]
    st.metric("Total arrests", arrests)  
with col4:
    warnings = df[df['stop_outcome'].str.contains("warning", case=False, na=False)].shape[0]
    st.metric("Total warnings", warnings)
    
# Medium insights

st.header("Medium Insights")

selected_query = st.selectbox("Select a Query to Run", [
    "Top 10 Vehicle number in drug_related stops",
    "Most frequent searched vehicle",
    "Highest arrest rate in driver age group",
    "Gender distribution of each country",
    "violation most associate with search or arrests",
    "Violation among young drivers",
    "Arrest rate by country and violation"
    ])

query_map = {
    "Top 10 Vehicle number in drug_related stops": "SELECT TOP 10 vehicle_number FROM digital_logs GROUP BY vehicle_number DESC",
    "Most frequent searched vehicle":"SELECT COUNT(*) AS COUNT FROM digital_logs where search_type == 'vehicle search'",
    "Highest arrest rate in driver age group": "SELECT driver_age MAX(is_arrested ==True) FROM digital_logs",
    "Gender distribution of each country": "SELECT country,COUNT(gender = 'male') as male_stops COUNT(gender = 'female') FROM digital_logs GROUP BY country",
    "violation most associate with search or arrests": "SELECT violation FROM digital_logs WHERE warning OR arrest GROUP BY stop_outcome",
    "Violation among young drivers": "SELECT violation FROM digital_logs where (driver_age <= 25)",
    "Arrest rate by country and violation":"SELECT COUNT(*) AS COUNT FROM digital_logs WHERE country_name AND violation"
    }

if st.button("Run Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.write(result)
    else:
        st.warnings("No result found in selected query.")
        
st.markdown("Build with Law Enforcement by SecureCheck")


st.markdown("Natural Language Prediction of the stop outcome based on existing data.")


st.header(" Add New Police Log & Predict Outcome and Violation")

# Input form for fields

with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")               
    country_name = st.text_input("Country Name")        
    driver_gender = st.selectbox("Driver Gender",["Male", "Female"])
    driver_age = st.number_input("Driver Age", min_value=16,max_value=100,value=27)
    driver_race =st.text_input("Driver Race")
    search_conducted = st.selectbox("was search conducted", ["0", "1"])
    search_type = st.text_input("Search Type")
    stop_duration = st.selectbox("Stop Duration", data['stop_duration'].dropna().unique())
    drugs_related_stop = st.selectbox("was drug related", ["0", "1"])
    vehicle_number = st.text_input("Vehicle Number")
    
    submitted = st.form_submit_button("Predict Stop Outcome & Violation")
    
    if submitted:
        filtered_data = data[
            (data['driver_gender'] == driver_gender) &
            (data['driver_age'] == driver_age) &
            (data['search_conducted'] == int(search_conducted)) &
            (data['stop_duration'] == stop_duration) &
            (data['drugs_related_stop'] == int(drugs_related_stop))
        ]
        
        
# Predict Stop_Outcome

        if not filtered_data.empty:
            predicted_outcome = filtered_data['stop_outcome'].mode()[0]
            predicted_violation = filtered_data['violation'].mode()[0]
        else:
            predicted_outcome = "Warning"
            predicted_violation = "Speeding"
            
            
# summary

search_text = "A Search Was Conducted" if int(search_conducted) else "No Search Was Conducted"
drug_text = "Was drug_related" if int(drugs_related_stop) else "Not Drug Related"

st.markdown("""
            ** prediction summary**
            
            ** predicted violation: ** (predicted_violation)
            ** predicted stop outcome: ** (predicted_outcome)
            
            A (driver_age)-year-oldn(driver_gender) driver in(country_name) was stopped at (stop_time.strftime(%I:%M %P)) on (stop_date)
            (search_text), and the stop (drug_text).
            Stop duration: **(stop_duration)**,
            Vehicle number: **(vehicle_number)**
            """ )