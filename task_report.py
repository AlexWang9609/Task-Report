import pandas as pd
import streamlit as st
import os
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "AllTasks.csv")

df_1 = pd.read_csv(file_path)

df_1 = df_1.rename(columns={'Number_of_days_overdue__c': 'duration of task'})

owner_mapping = {
    "Nicole De Munck":"005Hs00000CkSZ5IAN",
    "Rosella Colley":"005OJ00000CQRVVYA5",
    "Client Relations":"005Hs00000BdOuBIAV",
    "Arigail Sepion":"005Hs00000CkhEXIAZ"
}

df_1 = df_1[df_1['OwnerId'].isin(owner_mapping.values())]

reverse_mapping = {v: k for k, v in owner_mapping.items()}

df_1['OwnerId'] = df_1['OwnerId'].map(reverse_mapping)

df_r = df_1[df_1['Task_Category__c'].str.startswith("R-", na=False)]

df1 = df_1[~df_1['Task_Category__c'].str.startswith("R-", na=False)]

df1 = df1[~df1['Task_Category__c'].str.startswith("RQ", na=False)]

sla_mapping = {
    "CW": 3,
    "CD": 3,
    "NEW": 5,
    "TRO": 7,
    "TRIN": 15,
    "MC": 3
}

df1["SLA_Days"] = df1["Task_Category__c"].map(sla_mapping)

df1["Over_SLA_Days"] = df1["duration of task"] - df1["SLA_Days"]

df1["Over_SLA_Days"] = df1["Over_SLA_Days"].clip(lower=0)

task_options = list(df1['Task_Category__c'].unique())


# 假设你的 DataFrame 是 df
# 创建分箱
bins = [-1, 0, 3, 5, 10, 20, 30, float('inf')]
labels = ['0', '1-3', '3-5', '5-10', '10-20', '20-30', '30+']
df1['Over_SLA_Days_bin'] = pd.cut(df1['Over_SLA_Days'], bins=bins, labels=labels, right=True)

# Streamlit 页面
st.title("Over SLA Days Histogram by Task Category")

# 绘制交互式直方图
fig = px.histogram(
    df1,
    x='Over_SLA_Days_bin',
    color='Task_Category__c',
    category_orders={'Over_SLA_Days_bin': labels},  # 固定顺序
    barmode='stack',
    labels={'Over_SLA_Days_bin': 'Over SLA Days', 'count':'Number of Records'},
    title='Over SLA Days Histogram'
)
st.plotly_chart(fig, use_container_width=True)

# 用户选择某个类别查看对应记录
task_options = df1['Task_Category__c'].unique()
selected_task = st.multiselect("Select Task Category to show records:", task_options)

if selected_task:
    filtered_df = df1[df1['Task_Category__c'].isin(selected_task)]
    st.write(f"Showing {len(filtered_df)} records for selected categories")
    st.dataframe(filtered_df)
