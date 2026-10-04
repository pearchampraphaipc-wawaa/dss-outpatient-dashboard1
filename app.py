import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

os.environ["PYTHONIOENCODING"] = "utf-8"

# ---------------------------------------------------------
# 1. ตั้งค่าการเชื่อมต่อ Supabase
# ---------------------------------------------------------
SUPABASE_URL = "https://djkapqcwcdnvunrebjwu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRqa2FwcWN3Y2RudnVucmViand1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEwNDQxNjMsImV4cCI6MjEwNjYyMDE2M30.QuImBU0U9b9aOAfAhUEY8r3VmF24m3sjrXC_kyeHSbE"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------
# 2. ระบบสลับภาษา (Multilingual Dictionary)
# ---------------------------------------------------------
st.set_page_config(page_title="DSS Queue Management System", layout="wide")

# แถบเลือกภาษาใน Sidebar
lang = st.sidebar.radio("🌐 Language / ภาษา", ["TH", "EN"], horizontal=True)

# พจนานุกรมข้อความ 2 ภาษา
TEXTS = {
    "TH": {
        "title": "🏥 ระบบสนับสนุนการตัดสินใจ (DSS) บริหารจัดการคิวผู้ป่วยนอก",
        "filter_header": "🔍 ตัวกรองข้อมูล (Filters)",
        "select_dept": "เลือกแผนก:",
        "select_time": "เลือกช่วงเวลา:",
        "kpi_header": "📊 ดัชนีชี้วัดผลการดำเนินงาน (KPIs)",
        "total_patients": "จำนวนผู้ป่วยทั้งหมด",
        "avg_wait": "เวลารอคิวเฉลี่ย",
        "overdue_rate": "อัตราคิวเกินมาตรฐาน (>45น.)",
        "satisfaction": "คะแนนความพึงพอใจ",
        "unit_person": "คน",
        "unit_min": "นาที",
        "analytics_header": "📈 การวิเคราะห์ข้อมูลเชิงลึก (Analytics Dashboard)",
        "chart1_title": "1. เวลารอคิวเฉลี่ยแยกตามแผนก (นาที)",
        "chart2_title": "2. สัดส่วนประเภทสิทธิการรักษาของผู้ป่วย",
        "chart3_title": "3. ความหนาแน่นของผู้ป่วยแบ่งตามช่วงเวลา",
        "chart4_title": "4. การกระจายตัวของสถานะคิวบริการ",
        "chart5_title": "5. ระดับความพึงพอใจแยกตามกลุ่มอายุผู้ป่วย",
        "view_data": "📄 ดูข้อมูลตารางทั้งหมด",
        "err_msg": "เกิดข้อผิดพลาดในการดึงข้อมูล:"
    },
    "EN": {
        "title": "🏥 Decision Support System (DSS) for Outpatient Queue Management",
        "filter_header": "🔍 Data Filters",
        "select_dept": "Select Department:",
        "select_time": "Select Time Slot:",
        "kpi_header": "📊 Key Performance Indicators (KPIs)",
        "total_patients": "Total Patients",
        "avg_wait": "Avg Wait Time",
        "overdue_rate": "Overdue Rate (>45 mins)",
        "satisfaction": "Satisfaction Score",
        "unit_person": "patients",
        "unit_min": "mins",
        "analytics_header": "📈 Analytics Dashboard",
        "chart1_title": "1. Average Wait Time by Department (Mins)",
        "chart2_title": "2. Patient Insurance Type Distribution",
        "chart3_title": "3. Patient Density by Time Slot",
        "chart4_title": "4. Queue Status Distribution",
        "chart5_title": "5. Satisfaction Level by Age Group",
        "view_data": "📄 View Raw Data",
        "err_msg": "Data Fetching Error:"
    }
}

t = TEXTS[lang]

st.title(t["title"])

try:
    supabase = init_connection()

    @st.cache_data(ttl=60)
    def load_data():
        res_queue = supabase.table("fact_outpatient_queue").select("*").execute()
        df = pd.DataFrame(res_queue.data)

        try:
            res_dept = supabase.table("dim_department").select("*").execute()
            df_dept = pd.DataFrame(res_dept.data)
            if not df_dept.empty and "department_id" in df.columns and "department_id" in df_dept.columns:
                df = df.merge(df_dept, on="department_id", how="left")
        except Exception:
            pass

        try:
            res_patient = supabase.table("dim_patient").select("*").execute()
            df_patient = pd.DataFrame(res_patient.data)
            if not df_patient.empty and "patient_id" in df.columns and "patient_id" in df_patient.columns:
                df = df.merge(df_patient, on="patient_id", how="left")
        except Exception:
            pass

        try:
            res_date = supabase.table("dim_date").select("*").execute()
            df_date = pd.DataFrame(res_date.data)
            if not df_date.empty and "date_id" in df.columns and "date_id" in df_date.columns:
                df = df.merge(df_date, on="date_id", how="left")
        except Exception:
            pass

        return df

    df = load_data()

    # ---------------------------------------------------------
    # 3. ตัวกรองข้อมูล (Sidebar Filters)
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header(t["filter_header"])

    dept_col = "department_name" if "department_name" in df.columns else ("department_id" if "department_id" in df.columns else None)
    if dept_col:
        selected_dept = st.sidebar.multiselect(
            t["select_dept"],
            options=df[dept_col].unique(),
            default=df[dept_col].unique()
        )
        df = df[df[dept_col].isin(selected_dept)]

    time_col = "time_slot" if "time_slot" in df.columns else None
    if time_col:
        selected_time = st.sidebar.multiselect(
            t["select_time"],
            options=df[time_col].unique(),
            default=df[time_col].unique()
        )
        df = df[df[time_col].isin(selected_time)]

    # ---------------------------------------------------------
    # 4. แสดงผล KPIs
    # ---------------------------------------------------------
    st.subheader(t["kpi_header"])
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    total_patients = len(df)
    wait_col = "wait_time_minutes" if "wait_time_minutes" in df.columns else None
    
    avg_wait_time = round(df[wait_col].mean(), 1) if wait_col and total_patients > 0 else 0
    overdue_pct = round((len(df[df[wait_col] > 45]) / total_patients) * 100, 1) if wait_col and total_patients > 0 else 0
    
    sat_col = "satisfaction_score" if "satisfaction_score" in df.columns else None
    avg_satisfaction = round(df[sat_col].mean(), 1) if sat_col and total_patients > 0 else 0

    kpi1.metric(t["total_patients"], f"{total_patients} {t['unit_person']}")
    kpi2.metric(t["avg_wait"], f"{avg_wait_time} {t['unit_min']}")
    kpi3.metric(t["overdue_rate"], f"{overdue_pct}%")
    kpi4.metric(t["satisfaction"], f"{avg_satisfaction} / 5")

    st.markdown("---")

    # ---------------------------------------------------------
    # 5. แสดงผล กราฟ
    # ---------------------------------------------------------
    st.subheader(t["analytics_header"])

    col1, col2 = st.columns(2)

    with col1:
        if dept_col and wait_col:
            fig1 = px.bar(
                df.groupby(dept_col)[wait_col].mean().reset_index(),
                x=dept_col, y=wait_col,
                title=t["chart1_title"],
                color=wait_col
            )
            st.plotly_chart(fig1, use_container_width=True)

        if "insurance_type" in df.columns:
            fig2 = px.pie(
                df, names="insurance_type",
                title=t["chart2_title"],
                hole=0.4
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        if time_col and "queue_id" in df.columns:
            fig3 = px.line(
                df.groupby(time_col)["queue_id"].count().reset_index(),
                x=time_col, y="queue_id",
                title=t["chart3_title"]
            )
            st.plotly_chart(fig3, use_container_width=True)

        if "queue_status" in df.columns:
            fig4 = px.histogram(
                df, x="queue_status", color="queue_status",
                title=t["chart4_title"]
            )
            st.plotly_chart(fig4, use_container_width=True)

    if "age_group" in df.columns and sat_col:
        fig5 = px.box(
            df, x="age_group", y=sat_col, color="age_group",
            title=t["chart5_title"]
        )
        st.plotly_chart(fig5, use_container_width=True)

    with st.expander(t["view_data"]):
        st.dataframe(df)

except Exception as e:
    st.error(f"{t['err_msg']} {e}")