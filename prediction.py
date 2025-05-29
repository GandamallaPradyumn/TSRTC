import streamlit as st
import mysql.connector

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",    
    user="root", 
    password="12345",
    database="tgsrtc"
)
cursor = conn.cursor()

st.title("🚍 Driver Productivity Predictor")
st.subheader("Predicting driver productivity in hours based on health & operational parameters")

st.markdown("### 🧬 Driver Health and Productivity Inputs")

# Medical inputs
age = st.slider("Age", 35, 70 , 45)
creatinine = st.selectbox("Creatinine", ["Normal", "Abnormal"])
bp = st.selectbox("Blood Pressure (BP)", ["Normal", "Elevated", "Stage-1 Hypertension", "Stage-2 Hypertension", "Hypertension Critical"])
glucose = st.selectbox("Glucose", ["Normal", "Prediabetes", "Diabetes"])
bilirubin = st.selectbox("Bilirubin", ["Normal", "High"])
cholesterol = st.selectbox("Cholesterol", ["Normal", "Borderline", "High"])
ecg = st.selectbox("ECG", ["Within Limits", "Abnormal"])

st.markdown("### 📅 Driver Shift and Schedule Metrics")

night_shift = st.slider("Night Shift %", 0, 100, 20)
palle = st.slider("Pallevelugu Schedules %", 0, 100, 25)
city_ord = st.slider("City Ordinary %", 0, 100, 30)
metro = st.slider("Metro Express %", 0, 100, 25)

# Save to MySQL
if st.button("Submit & Predict"):
    insert_query = """
    INSERT INTO driver_inputs (
        age, creatinine, bp, glucose, bilirubin, cholesterol, ecg, 
        night_shift, pallevelugu, city_ordinary, metro_express
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        age, creatinine, bp, glucose, bilirubin, cholesterol, ecg,
        night_shift, palle, city_ord, metro
    )
    cursor.execute(insert_query, values)
    conn.commit()
    
    st.success("✅ Data saved to MySQL successfully!")
    st.write("🛣️ **Annual Driver Productivity (in Kilometers): 85000**")
 
