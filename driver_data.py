import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt

def driver_data():
     # --- Config ---
        DEPOTS = ['ADB', 'FLK', 'HYD2', 'JGIT', 'KMM', 'KMR', 'MBNR', 'MHBD', 'MLG', 'RNG', 'SRD']
        HEALTH_MAP = {'A': 95, 'B': 85, 'C': 75, 'D': 60, 'E': 50}

        # --- Load Driver Summary Data ---
        @st.cache_data
        def load_data():
            df = pd.read_excel(r"C:\ai\TGSRTC_AIProject_Absenteeism_All_KMM.xlsx")
            df['depot'] = df['depot'].str.upper()
            df['health_numeric'] = df['health_score'].map(HEALTH_MAP)
            return df

        df = load_data()
        avg = df['km_driven'].mean()

        # --- Sidebar Filters ---
        st.sidebar.title("Filters")
        selected_depot = st.sidebar.selectbox("Select Depot", DEPOTS)
        filtered_df = df[df['depot'] == selected_depot]

        driver_ids = filtered_df['employee_id'].unique()
        selected_driver = st.sidebar.selectbox("Select Driver ID", driver_ids)
        driver_data = filtered_df[filtered_df['employee_id'] == selected_driver].iloc[0]

        # --- Dashboard Display ---
        logo_path=r'C:\ai\LOGO.png'
        c1,c2 = st.columns([1,4])
        with c1:
            st.image(logo_path,width=80)
        with c2:
            st.title("TGSRTC DRIVER PRODUCTIVITY & HEALTH")
        st.subheader(f"Driver: {driver_data['driver_name']} (ID: {driver_data['employee_id']})")
        st.text(f"Depot: {driver_data['depot'].upper()}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("KM Driven", f"{driver_data['km_driven']} km")
        with col2:
            st.metric("Leaves Taken", f"{driver_data['leaves_taken']} days")
        with col3:
            st.metric("Health Score", f"{driver_data['health_score']} ({driver_data['health_numeric']}/100)")

        # Health grade logic
        score = driver_data['health_numeric']
        if score >= 90:
            grade = "Excellent"
        elif score >= 85:
            grade = "Good"
        elif score >= 70:
            grade = "Average"
        elif score >= 60:
            grade = "Bad"
        else:
            grade = "Needs Attention"

        st.info(f"**Health Grade:** {grade}")

        # --- Driver Table with Highlights ---
        def highlight_health_grade(val):
            return 'background-color: red; color: white; font-weight: bold' if val == 'D' else ''

        def highlight_low_km(val):
            return 'background-color: orange; color: black; font-weight: bold' if isinstance(val, (int, float)) and val < avg else ''

        def highlight_selected_row(row):
            return ['background-color: Green' if row['employee_id'] == selected_driver else '' for _ in row]

        # --- Load Monthly KM Data ---
        @st.cache_data
        def load_monthly_km_data():
            duty_df = pd.read_excel(r"C:\ai\MHBD_OPRNS_HSD_2023-2024.xlsx", sheet_name="DRI-DUTY", skiprows=2)
            duty_df = duty_df.rename(columns={
                'Unnamed: 2': 'date',
                'Unnamed: 3': 'driver_id',
                'Unnamed: 6': 'kms'
            })
            duty_df = duty_df[['date', 'driver_id', 'kms']].dropna()
            duty_df['date'] = pd.to_datetime(duty_df['date'], errors='coerce')
            duty_df['kms'] = pd.to_numeric(duty_df['kms'], errors='coerce')
            duty_df.dropna(inplace=True)
            duty_df['month'] = duty_df['date'].dt.strftime('%B')
            return duty_df

        monthly_df = load_monthly_km_data()
        driver_monthly_df = monthly_df[monthly_df['driver_id'] == selected_driver]

        driver_monthly_summary = (
            driver_monthly_df.groupby('month', as_index=False)['kms'].sum()
        )

        # Define months
        month_order = ['April', 'May', 'June', 'July', 'August', 'September',
                    'October', 'November', 'December', 'January', 'February', 'March']

        # Ensure all months are included
        base_df = pd.DataFrame({'month': month_order})
        driver_monthly_summary = base_df.merge(driver_monthly_summary, on='month', how='left')
        driver_monthly_summary['kms'] = driver_monthly_summary['kms'].fillna(0)

        # Set month ordering
        driver_monthly_summary['month'] = pd.Categorical(driver_monthly_summary['month'], categories=month_order, ordered=True)
        driver_monthly_summary = driver_monthly_summary.sort_values('month')

        # Calculate average KMs
        average_kms = driver_monthly_summary['kms'].mean()

        # Main bar chart
        bars = alt.Chart(driver_monthly_summary).mark_bar().encode(
            x=alt.X('month:N', title='Month'),
            y=alt.Y('kms:Q', title='Total KM Driven'),
            tooltip=['month', 'kms']
        )

        # Average line
        avg_line = alt.Chart(pd.DataFrame({'average': [average_kms]})).mark_rule(
            color='red',
            strokeDash=[6, 6]
        ).encode(
            y='average:Q'
        ).properties()

        # Combine chart
        final_chart = (bars + avg_line).properties(width=700, height=400)

        # Display in Streamlit
        st.subheader("Monthly KM Performance")
        if not driver_monthly_summary.empty:
            st.altair_chart(final_chart, use_container_width=True)
        else:
            st.warning("No monthly KM data found for this driver.")

        # --- Load and Plot LSA Data ---
        @st.cache_data
        def load_lsa_data():
            df = pd.read_excel(r"C:\ai\Book1.xlsx")
            df.dropna(inplace=True)
            df['DATE_OF_ABSENCE'] = pd.to_datetime(df['DATE_OF_ABSENCE'], errors='coerce')
            df['STAFF_NO'] = df['STAFF_NO'].astype(int)
            df['Month'] = df['DATE_OF_ABSENCE'].dt.strftime('%B')
            return df

        lsa_df = load_lsa_data()

        lsa_monthly_df = lsa_df[lsa_df['STAFF_NO'] == selected_driver]

        lsa_monthly_summary = (
            lsa_monthly_df.groupby('Month', as_index=False)['LSA'].sum()
        )


        st.subheader("Total LSA vs. Month (Bar Chart)")

        # Define all months
        # Define all months
        month_order = ['April', 'May', 'June', 'July', 'August', 'September',
                    'October', 'November', 'December', 'January', 'February', 'March']

        # Ensure the months column exists and fill in missing months with 0
        if not lsa_df.empty:
            # Create a base DataFrame with all months
            base_df = pd.DataFrame({'Month': month_order})
            
            # Merge with your summary
            lsa_monthly_summary = base_df.merge(lsa_monthly_summary, on='Month', how='left')
            
            # Fill missing LSA values with 0
            lsa_monthly_summary['LSA'] = lsa_monthly_summary['LSA'].fillna(0)

            # Ensure correct ordering
            lsa_monthly_summary['Month'] = pd.Categorical(lsa_monthly_summary['Month'], categories=month_order, ordered=True)
            lsa_monthly_summary = lsa_monthly_summary.sort_values('Month')

            # Calculate average LSA
            avg_lsa = lsa_monthly_summary['LSA'].mean()

            # Bar chart
            bars = alt.Chart(lsa_monthly_summary).mark_bar(color="tomato").encode(
                x=alt.X('Month:N', title='Month', sort=month_order),
                y=alt.Y('LSA:Q', title='Total LSA(days)'),
                tooltip=['Month', 'LSA']
            )

            # Average line
            avg_line = alt.Chart(pd.DataFrame({'average': [avg_lsa]})).mark_rule(
                color='red',
                strokeDash=[6, 6]
            ).encode(
                y='average:Q'
            )

            # Combine both
            lsa_bar_chart = (bars + avg_line).properties(width=700, height=400)

            # Show in Streamlit
            st.altair_chart(lsa_bar_chart, use_container_width=True)

        else:
            st.warning("No LSA data available.")

        with st.expander("View All Drivers in Selected Depot"):
            styled_df = (
                filtered_df.style
                .applymap(highlight_health_grade, subset=['health_score'])
                .applymap(highlight_low_km, subset=['km_driven'])
                .apply(highlight_selected_row, axis=1)
            )
            st.dataframe(styled_df)

if __name__ == '__main__':
    driver_data()
