import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io

# Load label and index metadata
with open('labels.json', 'r', encoding='utf-8') as f:
    label_config = json.load(f)

with open('index_metadata.json', 'r', encoding='utf-8') as f:
    index_meta = json.load(f)

# Load merged master data
with open('banks-master.json', 'r', encoding='utf-8') as f:
    banks_data = json.load(f)['banks_data']

# Convert to DataFrame
df = pd.DataFrame(banks_data)

# Sidebar Controls
language = st.sidebar.radio("🌐 Choose Language / மொழியைத் தேர்ந்தெடுக்கவும்", ['English', 'Tamil'])
country = st.sidebar.selectbox("🌏 Select Country", sorted(df['country'].unique()))
flag = '🇮🇳' if country == 'India' else '🇺🇸'

# Label helpers
sector_map = label_config[language].get('sector_labels', {})
index_map = label_config[language].get('index_labels', {})

# Filters
sector_filter = st.sidebar.multiselect(
    label_config[language]['filter_by_sector'],
    options=sorted(df[df['country'] == country]['sector'].unique()),
    default=sorted(df[df['country'] == country]['sector'].unique())
)

cap_filter = st.sidebar.multiselect(
    "🏷️ Select Cap Segment",
    options=['Large', 'Mid', 'Small'],
    default=['Large', 'Mid', 'Small']
)

bank_filter = st.sidebar.multiselect(
    "🏦 Select Banks",
    options=df[df['country'] == country]['short_name'].tolist(),
    default=df[df['country'] == country]['short_name'].tolist()
)

# Language-specific column
df['Bank Name'] = df['full_name_ta'] if language == 'Tamil' else df['full_name_en']

# Filtered DataFrame
filtered_df = df[
    (df['country'] == country) &
    (df['sector'].isin(sector_filter)) &
    (df['cap_segment'].isin(cap_filter)) &
    (df['short_name'].isin(bank_filter))
].copy()

# Format index list safely
filtered_df['Indices'] = filtered_df['indices'].apply(
    lambda x: ', '.join(x) if isinstance(x, list) and x else '—'
)

# Translate sector and index names
filtered_df['Sector (Translated)'] = filtered_df['sector'].apply(lambda x: sector_map.get(x, x))
filtered_df['Indices (Translated)'] = filtered_df['Indices'].apply(
    lambda x: ', '.join([index_map.get(i.strip(), i.strip()) for i in x.split(',')]) if isinstance(x, str) else '—'
)

# Title
st.title(f"{label_config[language]['title']} {flag}")

# Plotly Scatter Plot
st.subheader(label_config[language]['graph_title'])
market_cap_col = 'market_cap_cr' if country == 'India' else 'market_cap_bn_usd'

fig = px.scatter(
    filtered_df,
    x='beta_5yr',
    y=market_cap_col,
    text='short_name',
    color='Sector (Translated)',
    hover_name='Bank Name',
    hover_data={
        'Country': filtered_df['country'],
        'ISIN': filtered_df['isin'],
    #    'Indices': filtered_df['Indices (Translated)'],
        'beta_5yr': False,
        'short_name': False
    },
    labels={
        'beta_5yr': label_config[language]['beta_label'],
        market_cap_col: label_config[language]['marketcap_label']
    }
)

fig.add_vline(
    x=1.0,
    line_dash="dash",
    line_color="red",
    annotation_text="Beta = 1",
    annotation_position="top right"
)

fig.update_traces(textposition='top center')
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

# Table
st.subheader(label_config[language]['table_title'])
filtered_df['Full Name'] = filtered_df['full_name_ta'] if language == 'Tamil' else filtered_df['full_name_en']
pivot_df = filtered_df[['short_name', 'Full Name', 'isin', 'Indices (Translated)', market_cap_col, 'beta_5yr', 'cap_segment']]
pivot_df.set_index('short_name', inplace=True)
pivot_df.columns = [
    label_config[language]['fullname_label'],
    'ISIN',
    'Indices',
    label_config[language]['marketcap_label'],
    label_config[language]['beta_label'],
    label_config[language]['capseg_label']
]
st.dataframe(pivot_df)

# Excel Export
excel_buffer = io.BytesIO()
pivot_df.reset_index().to_excel(excel_buffer, index=False, sheet_name='Bank Beta')
st.download_button(
    label=label_config[language]['export_excel'],
    data=excel_buffer.getvalue(),
    file_name=f"bank_beta_{country.lower()}.xlsx",
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
