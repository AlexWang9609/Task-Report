import numpy as np
import pandas as pd
import streamlit as st
import os
import plotly.express as px


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "AllTasks.csv")

df_1 = pd.read_csv(file_path)

df_1 = df_1.rename(columns={'Number_of_days_overdue__c': 'duration of task'})
df_1 = df_1.dropna(subset=['Task_Category__c'])

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

# 假设你的 DataFrame 是 df1
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
# 1. 增加 'All' 选项
task_options = ['All'] + list(df1['Task_Category__c'].unique())
selected_task = st.multiselect("Select Task Category to show records:", task_options, default='All')

if selected_task:
    # 2. 根据选择过滤数据
    if 'All' in selected_task:
        # 如果选择了 'All'，则显示所有 Task Category 的记录
        filtered_df = df1
        display_categories = sorted(df1['Task_Category__c'].unique())
    else:
        # 否则，只显示选择的 Task Category 的记录
        filtered_df = df1[df1['Task_Category__c'].isin(selected_task)]
        display_categories = selected_task

    st.header(f"📊 Task Category Distribution within Over SLA Days Bins")

    # 3. 创建分布表格
    # 按 'Task_Category__c' 和 'Over_SLA_Days_bin' 分组计数
    distribution_table = pd.crosstab(
        filtered_df['Task_Category__c'],
        filtered_df['Over_SLA_Days_bin'],
        dropna=False
    )

    # 重新索引列以确保 bin 的顺序正确
    distribution_table = distribution_table.reindex(columns=labels, fill_value=0)

    # === 关键修改部分开始 ===
    # 仅在选择了 'All' 或选择了多个任务类别时添加 'Total' 行
    # display_categories 列表包含实际要显示的任务类别（不包括 'All'）
    if 'All' in selected_task or len(display_categories) > 1:
        # 计算总计行
        total_row = distribution_table.sum(axis=0).rename('Total')
        distribution_table.loc['Total'] = total_row
    # === 关键修改部分结束 ===
    
    # 转换为 Streamlit 易读的格式（Task Category 作为常规列）
    # 注意：如果只选择一个类别，这里 Task Category 列中就只有一行数据，且不会有 'Total'
    distribution_df = distribution_table.reset_index().rename(columns={'Task_Category__c': 'Task Category'})

    # 格式化和展示分布表格
    st.markdown(f"**Over SLA Days Bin Count for Selected Task Categories:**")
    st.dataframe(distribution_df)

    # 显示现有记录表格
    st.header(f"📋 Records for Selected Task Categories")
    st.write(f"Showing **{len(filtered_df)}** records for selected categories ({', '.join(display_categories)})")
    st.dataframe(filtered_df)