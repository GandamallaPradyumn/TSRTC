import streamlit as st
import pandas as pd
from groq import Groq

st.set_page_config(page_title="KMM LLM Trend Analyzer", layout="wide")
# ✅ Securely load API key from secrets.toml

st.title("📈 Excel Trend Analyzer using LLM")

uploaded_file = st.file_uploader("Upload your KMM Excel file", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet_name = xls.sheet_names[0]
        df_raw = xls.parse(sheet_name)
        df_raw.columns = df_raw.columns.astype(str)
        st.subheader("📄 Raw Data")
        st.dataframe(df_raw)

        dates = pd.to_datetime(df_raw.columns[3:], errors='coerce')
        time_series_data = {}

        for i in range(3, df_raw.shape[0]):
            label = df_raw.iloc[i, 0]
            if pd.notna(label):
                metric_name = str(label).strip()
                values = pd.to_numeric(df_raw.iloc[i, 3:], errors='coerce').tolist()
                time_series_data[metric_name] = values

        df_ts = pd.DataFrame(time_series_data)
        df_ts['Date'] = dates
        df_ts.set_index('Date', inplace=True)
        st.subheader("📊 Time Series Data")
        st.line_chart(df_ts)

        label_series = df_raw.iloc[:, 0].to_list()

        def plot(y1_labels, y2_labels, r1, r2, heading):
            series_data = {}
            if pd.notna(y1_labels):
                y1_labels = str(y1_labels)
                y1_values = pd.to_numeric(df_raw.iloc[r1, 3:], errors='coerce').tolist()
                series_data[y1_labels] = y1_values
            if pd.notna(y2_labels):
                y2_labels = str(y2_labels)
                y2_values = pd.to_numeric(df_raw.iloc[r2, 3:], errors='coerce').tolist()
                series_data[y2_labels] = y2_values

            df = pd.DataFrame(series_data)
            df['Date'] = dates
            df.set_index('Date', inplace=True)
            st.subheader(f"📊 {heading}")
            st.line_chart(df)

        # Plotting sections
        plot(label_series[0], label_series[2], 0, 2, "(Actual Vs Planned) Services")
        plot(label_series[1], label_series[3], 1, 3, "(Actual Vs Planned) Kms")
        plot(label_series[4], label_series[5], 4, 5, "(Actual Vs Estimated) Weekly Offs %")
        plot(label_series[7], label_series[8], 7, 8, "(Actual Vs Estimated) Special Offs %")
        plot(label_series[10], label_series[11], 10, 11, "(Actual Vs Estimated) OD + Others %")
        plot(label_series[13], label_series[14], 13, 14, "(Actual Vs Estimated) Sick Leaves %")
        plot(label_series[16], label_series[17], 16, 17, "(Actual Vs Estimated) leave+absent %")
        plot(label_series[19], label_series[20], 19, 20, "(Actual Vs Estimated) Spot Absent %")
        plot(label_series[22], label_series[23], 22, 23, "(Actual Vs Estimated) Double Duty %")
        plot(label_series[25], label_series[26], 25, 26, "(Actual Vs Estimated) Off Cancellation %")

        

        client = Groq(
                        api_key= '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',
                    )
        if st.button("🔍 Analyze Trends with LLM"):
            st.info("Sending data to LLM...")

            try:
                description = df_ts.tail(10).to_string()
                prompt = f"""
                You are a data analyst. Below is a time series of transportation metrics.
                Analyze trends and anomalies. Summarize in plain language:

                {description}

                Give actionable insights if possible.
                """

                response = client.chat.completions.create(
                messages=[
                        {"role": "system", "content": "You are a transportation data analyst."},
                        {"role": "user", "content": prompt}
                ],
                model="llama3-70b-8192"
                )

                insights = response.choices[0].message.content
                st.subheader("📋 LLM Insights")
                st.markdown(insights)

            except Exception as e:
                st.error(f"LLM Error: {e}")

    except Exception as e:
        st.error(f"Failed to read the file: {e}")
