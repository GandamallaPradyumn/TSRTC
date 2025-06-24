from datetime import datetime
import streamlit as st
import pandas as pd
import altair as alt

class Dashboard:

    def __init__(self):
        # Load data
        self.annual_df = pd.read_csv("ANNUAL_DRI_DATA.csv")
        self.monthly_df = pd.read_csv("DRI_DUTY.csv")
        self.lsa_df = pd.read_csv("LSA.csv")

        # Standardize columns
        self.annual_df.columns = self.annual_df.columns.str.upper()
        self.monthly_df.columns = self.monthly_df.columns.str.upper()
        self.lsa_df.columns = self.lsa_df.columns.str.upper()

        # Preprocess monthly data
        self.monthly_df.dropna(subset=['DATE', 'KMS', 'HOURS','D/N_OUT'], inplace=True)
        self.monthly_df['DATE'] = pd.to_datetime(self.monthly_df['DATE'],dayfirst=True)
        self.monthly_df['KMS'] = pd.to_numeric(self.monthly_df['KMS'])
        self.monthly_df['HOURS'] = pd.to_numeric(self.monthly_df['HOURS'])
        self.monthly_df['MONTH_YEAR'] = self.monthly_df['DATE'].dt.strftime('%B %Y')

        # Preprocess LSA data
        self.lsa_df['DATE'] = pd.to_datetime(self.lsa_df['DATE'],dayfirst=True)
        self.lsa_df = self.lsa_df[self.lsa_df['DATE'] < '2024-04-01']
        self.lsa_df['MONTH_YEAR'] = self.lsa_df['DATE'].dt.strftime('%B %Y')

        # Extract and sort month order
        self.month_order = self.monthly_df['MONTH_YEAR'].unique().tolist()
        self.months_order = sorted(self.month_order, key=lambda x: datetime.strptime(x, '%B %Y'))

        self.depots = ['ADB', 'FLK', 'HYD2', 'JGIT', 'KMM', 'KMR', 'MBNR', 'MHBD', 'MLG', 'RNG', 'SRD']
        self.ui()

    def ui(self):
        st.sidebar.title("🔎 Filters")
        selected_depot = st.sidebar.selectbox("Select Depot", self.depots)

        self.filtered_df = self.annual_df[self.annual_df['DEPOT'] == selected_depot]
        driver_ids = self.filtered_df['EMP_ID'].unique()
        self.selected_driver = st.sidebar.selectbox("Select Driver ID", driver_ids)

        driver_data_row = self.filtered_df[self.filtered_df['EMP_ID'] == self.selected_driver]
        if driver_data_row.empty:
            st.error("Driver not found.")
            return

        driver_data = driver_data_row.iloc[0].copy()
        driver_data['HOURS'] = self.monthly_df[self.monthly_df['EMP_ID'] == self.selected_driver]['HOURS'].sum()

        logo_path = "LOGO.png"
        lsa_count = self.lsa_df.groupby('EMP_ID')['LSA'].sum()
        lsa_count = lsa_count.reset_index()
        lsa_count = lsa_count[lsa_count['EMP_ID'] == self.selected_driver]
        lsa_count = 0 if lsa_count.empty else lsa_count['LSA'].iloc[0]
        
        c1, c2 = st.columns([1, 4])
        with c1:
            st.image(logo_path, width=80)
        with c2:
            st.title("TGSRTC DRIVER PRODUCTIVITY & HEALTH")

        st.text(f"Depot: {driver_data['DEPOT'].upper()}")
        st.subheader(f"Driver: {driver_data['DRIVER_NAME']} (ID: {driver_data['EMP_ID']})")

        col1, col2 = st.columns(2)
        col1.metric("KM Driven (APR23 - MAR24)", f"{driver_data['KMS_DRIVEN']} km ")
        col2.metric("Hours", f"{driver_data['HOURS']} hrs")

        col3, col4 = st.columns(2)
        col3.metric("Leaves Taken", f"{lsa_count} days")
        col4.metric("Health Score", f"{driver_data['HEALTH_SCORE']} Grade")

        grade_map = {'A': "Excellent", 'B': "Good", 'C': "Average", 'D': "Bad"}
        grade = grade_map.get(driver_data['HEALTH_SCORE'], "Needs Attention")
        st.info(f"Health Grade: {grade}")

        self.bar_chart("Monthly KM Driven", "Month-Year", "KMs Driven", self.monthly_df, 'KMS', 'aqua')
        self.bar_chart("Monthly Hours Worked", "Month-Year", "Hours", self.monthly_df, 'HOURS', 'lightgreen')

        if 'DOUBLE_DUTY' in self.monthly_df.columns:
            self.bar_chart("Monthly Double Duties", "Month-Year", "Double Duties", self.monthly_df, 'DOUBLE_DUTY', 'orange')

        if 'LSA' in self.lsa_df.columns:
            self.bar_chart("LSA Summary", "Month-Year", "Leaves", self.lsa_df, 'LSA', "pink")
        else:
            st.warning("LSA column not found in LSA data.")

        self.grp_bar_chart(self.monthly_df)

        with st.expander("View All Drivers in Selected Depot"):
            styled_df = (
                self.filtered_df.style
                .applymap(self.highlight_health_grade, subset=['HEALTH_SCORE'])
                .applymap(self.highlight_low_km, subset=['KMS_DRIVEN'])
                .apply(self.highlight_selected_row, axis=1)
            )
            st.dataframe(styled_df)

    def bar_chart(self, title, x_title, y_title, df, value_col, color='skyblue'):
        df = df[df['EMP_ID'] == self.selected_driver]
        
        base_df = pd.DataFrame({'MONTH_YEAR': self.months_order})
        summary = df.groupby('MONTH_YEAR', as_index=False)[value_col].sum()
        summary = base_df.merge(summary, on='MONTH_YEAR', how='left')
        summary[value_col] = summary[value_col].fillna(0)
        summary['MONTH_YEAR'] = pd.Categorical(summary['MONTH_YEAR'], categories=self.months_order, ordered=True)
        summary = summary.sort_values('MONTH_YEAR')
        average = summary[value_col].mean()

        bars = alt.Chart(summary).mark_bar(color=color).encode(
            x=alt.X('MONTH_YEAR:N', title=x_title, sort=self.months_order),
            y=alt.Y(f"{value_col}:Q", title=y_title),
            tooltip=['MONTH_YEAR', value_col]
        )

        avg_line = alt.Chart(pd.DataFrame({'average': [average]})).mark_rule(
            color='crimson', strokeDash=[6, 6]
        ).encode(y='average:Q')

        st.subheader(title)
        st.altair_chart((bars + avg_line).properties(width=700, height=400), use_container_width=True)

    def grp_bar_chart(self, df):
        df = df[df['EMP_ID'] == self.selected_driver]

        # Ensure MONTH_YEAR column exists
        if 'MONTH_YEAR' not in df.columns:
            df['MONTH_YEAR'] = df['DATE'].dt.strftime('%B %Y')

        base_df = pd.DataFrame({'MONTH_YEAR': self.months_order})

        # DAY OUT
        summary_day = df[df['D/N_OUT'] == 'D'].groupby('MONTH_YEAR').size().reset_index(name='Count')
        summary_day = base_df.merge(summary_day, on='MONTH_YEAR', how='left')
        summary_day['Shift'] = 'DAY OUT'

        # NIGHT OUT
        summary_nig = df[df['D/N_OUT'] == 'N'].groupby('MONTH_YEAR').size().reset_index(name='Count')
        summary_nig = base_df.merge(summary_nig, on='MONTH_YEAR', how='left')
        summary_nig['Shift'] = 'NIGHT OUT'

        # Combine both
        summary_df = pd.concat([summary_day, summary_nig])
        summary_df['Count'] = summary_df['Count'].fillna(0)

        # Categorical month ordering
        summary_df['MONTH_YEAR_STR'] = pd.Categorical(
            summary_df['MONTH_YEAR'], categories=self.months_order, ordered=True
        )
        summary_df.sort_values('MONTH_YEAR_STR', inplace=True)

        # Base bar chart
        bar_chart = alt.Chart(summary_df).mark_bar().encode(
            x=alt.X('MONTH_YEAR_STR:N', title='Month-Year', sort=self.months_order),
            y=alt.Y('Count:Q', title='Number of Duties'),
            color=alt.Color('Shift:N', scale=alt.Scale(range=['lightblue', 'blue'])),
            tooltip=['MONTH_YEAR_STR', 'Shift', 'Count']
        )

        # Average lines
        avg_lines = alt.Chart(summary_df).mark_rule(strokeDash=[6, 3], color='lime').encode(
            y='mean(Count):Q'
        ).transform_filter(
            alt.datum.Shift == 'DAY OUT'
        ) + alt.Chart(summary_df).mark_rule(strokeDash=[6, 3], color='crimson').encode(
            y='mean(Count):Q'
        ).transform_filter(
            alt.datum.Shift == 'NIGHT OUT'
        )

        # Combine and display
        chart = (bar_chart + avg_lines).properties(width=800, height=400)

        st.header('Day vs Night Duties per Month')
        st.altair_chart(chart, use_container_width=True)


    def highlight_health_grade(self, val):
        return 'background-color: red; color: white; font-weight: bold' if val == 'D' else ''

    def highlight_low_km(self, val):
        return 'background-color: orange; color: black; font-weight: bold' if isinstance(val, (int, float)) and val < 1000 else ''

    def highlight_selected_row(self, row):
        return ['background-color: green' if row['EMP_ID'] == self.selected_driver else '' for _ in row]


# Run the app
if __name__ == '__main__':
    Dashboard()