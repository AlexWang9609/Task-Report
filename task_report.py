import numpy as np
import pandas as pd
import os
import streamlit as st
import plotly.express as px

# --- Data Loading and Initial Filtering ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: Ensure 'AllTasks.csv' exists in the same directory as the script.
file_path = os.path.join(BASE_DIR, "AllTasks.csv")
# Check if file exists before reading
if not os.path.exists(file_path):
    st.error(f"File not found: {file_path}")
    st.stop()
    
df_1 = pd.read_csv(file_path)
df_1 = df_1.rename(columns={'Number_of_days_overdue__c': 'Duration of Task'})

df = df_1

# Filter Conditions (based on previous user request)
# 1. ActivityDate (equivalent to 'Date' in filter image) <= Dec 3, 2025
# NOTE: Ensure 'ActivityDate' is a datetime object or a string format recognized by pandas for comparison.
date_filter = df['ActivityDate'] <= '2025-12-03'
# 2. Task_Category__c (equivalent to 'Task Category' in filter image) in list
category_list = ['CW', 'CD', 'TRIN', 'TRO', 'RQ', 'NEW', 'MC', 'FPC']
category_filter = df['Task_Category__c'].isin(category_list)
# 3. CreatedDate >= Nov 1, 2025
# NOTE: Ensure 'CreatedDate' is a datetime object or a string format recognized by pandas for comparison.
created_date_filter = df['CreatedDate'] >= '2025-11-01'
# Combine all filters using logical AND (&)
filtered_df = df[date_filter & category_filter & created_date_filter]

# --- Owner ID Mapping and Replacement ---
owner_mapping = {
    "Nicole De Munck": "005Hs00000CkSZ5IAN",
    "Rosella Colley": "005OJ00000CQRVVYA5",
    "Client Relations": "005Hs00000BdOuBIAV",
    "Arigail Sepion": "005Hs00000CkhEXIAZ"
}
# 1. Filter: Keep only rows where OwnerId is in the mapping's value list
filtered_df = filtered_df[filtered_df['OwnerId'].isin(owner_mapping.values())]
# 2. Reverse mapping: value → key
reverse_mapping = {v: k for k, v in owner_mapping.items()}
# 3. Replace OwnerId with the corresponding key
filtered_df['OwnerId'] = filtered_df['OwnerId'].map(reverse_mapping)

# --- SLA Calculation ---
# 1. Define SLA mapping
sla_mapping = {
    "CW": 3,
    "CD": 3,
    "NEW": 5,
    "TRO": 7,
    "TRIN": 15,
    "MC": 3,
    "RQ": 0
}
# 2. Map to get SLA Days column
filtered_df["SLA_Days"] = filtered_df["Task_Category__c"].map(sla_mapping)
# 3. Calculate (Duration of Task - SLA)
filtered_df["Over_SLA_Days"] = filtered_df["Duration of Task"] - filtered_df["SLA_Days"]
# 4. Set values <= 0 to 0
filtered_df["Over_SLA_Days"] = filtered_df["Over_SLA_Days"].clip(lower=0)

df1 = filtered_df

# 1. 分箱（你原来的代码稍微改一下，确保是数值）
df1['Over_SLA_Days'] = pd.to_numeric(df1['Over_SLA_Days'], errors='coerce')

bins = [-1, 0, 3, 5, 10, 20, 30, float('inf')]
labels = ['0', '1-3', '3-5', '5-10', '10-20', '20-30', '30+']

df1['Over_SLA_Days_bin'] = pd.cut(
    df1['Over_SLA_Days'],
    bins=bins,
    labels=labels,
    right=True,
    include_lowest=True
)

# 2. 统计每个 (区间, Task Category) 的数量
bin_counts = (
    df1
    .groupby(['Over_SLA_Days_bin', 'Task_Category__c'])
    .size()
    .reset_index(name='Count')
)

# 3. 画堆叠柱状图
st.title("Over SLA Days Histogram by Task Category")

fig = px.bar(
    bin_counts,
    x='Over_SLA_Days_bin',
    y='Count',
    color='Task_Category__c',
    category_orders={'Over_SLA_Days_bin': labels},
    barmode='stack',
    labels={
        'Over_SLA_Days_bin': 'Over SLA Days',
        'Count': 'Number of Records',
        'Task_Category__c': 'Task Category'
    },
    title='Over SLA Days Histogram'
)

st.plotly_chart(fig, use_container_width=True)


# User Selection
task_options = ['All'] + list(df1['Task_Category__c'].unique())
selected_task = st.multiselect("Select Task Category to show records:", task_options, default='All')

if selected_task:
    # Filter data based on selection
    if 'All' in selected_task:
        filtered_df = df1
        display_categories = sorted(df1['Task_Category__c'].unique())
    else:
        filtered_df = df1[df1['Task_Category__c'].isin(selected_task)]
        display_categories = selected_task

    st.header(f"📊 Task Category Distribution within Over SLA Days Bins")

    # Determine if 'Total' row should be included
    add_total_row = 'All' in selected_task or len(display_categories) > 1

    # =================================================================================
    # 1. Create and Display Count Distribution Table
    # =================================================================================

    # Create the contingency table
    distribution_table_count = pd.crosstab(
        filtered_df['Task_Category__c'],
        filtered_df['Over_SLA_Days_bin'],
        dropna=False
    )
    # Reindex columns to ensure correct bin order
    distribution_table_count = distribution_table_count.reindex(columns=labels, fill_value=0)

    # Calculate and add Total count row if needed
    if add_total_row:
        total_row_count = distribution_table_count.sum(axis=0).rename('Total')
        distribution_table_count.loc['Total'] = total_row_count

    st.markdown(f"### **1. Over SLA Days Bin Count**")
    distribution_df_count = distribution_table_count.reset_index().rename(columns={'Task_Category__c': 'Task Category'})
    st.dataframe(distribution_df_count)

    # =================================================================================
    # 2. Create and Display Mixed Percentage Distribution Table
    # =================================================================================

    st.markdown(f"### **2. Mixed Percentage Distribution**")
    st.markdown(f"**Task Category Rows:** Percentage of category count relative to the **Column (Bin) Total**.")
    st.markdown(f"**Total Row:** Percentage of the column total relative to the **Grand Total of all records**.")

    # 2a. Get the base table for percentage calculation (excluding 'Total' row)
    base_df = distribution_table_count.loc[distribution_table_count.index != 'Total']

    # 2b. Calculate Column Totals (used as denominator for Task Category Rows)
    if add_total_row:
        column_totals = distribution_table_count.loc['Total']
    else:
        # If only one category is selected and 'Total' row is not present
        column_totals = distribution_table_count.sum(axis=0)

    # 2c. Calculate Task Category Row Percentages (Cell Count / Column Total)
    # Use replace to handle division by zero (where column_totals is 0)
    denominator = column_totals.replace(0, np.nan)
    # Perform division, multiply by 100, and fill NaN (from division by zero) with 0
    distribution_table_percentage = (base_df.div(denominator, axis=1) * 100).fillna(0)

    # 2d. Prepare Total Row (Total Count Percentage)
    if add_total_row:
        grand_total = column_totals.sum()

        if grand_total > 0:
            # Calculate Total Row Percentage: (Column Total / Grand Total) * 100
            total_percentage_row = (column_totals / grand_total) * 100
        else:
            total_percentage_row = pd.Series([0.0] * len(labels), index=labels)

        total_percentage_row.rename('Total', inplace=True)
        distribution_table_percentage.loc['Total'] = total_percentage_row

    # 2e. Format and display the percentage table
    distribution_df_percentage = distribution_table_percentage.reset_index().rename(columns={'Task_Category__c': 'Task Category'})

    # Use Styler to format the percentages for display
    percentage_format = {col: '{:.2f}%'.format for col in labels}
    st.dataframe(distribution_df_percentage.style.format(percentage_format))

    # =================================================================================
    # 3. Display Raw Records
    # =================================================================================

    st.header(f"📋 Records for Selected Task Categories")
    st.write(f"Showing **{len(filtered_df)}** records for selected categories ({', '.join(display_categories)})")
    st.dataframe(filtered_df)