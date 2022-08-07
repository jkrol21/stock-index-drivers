import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.io as pio
import plotly.express as px

from utils import index_components_shap_values, plot_candlestick, read_sql_query
pio.templates.default = "plotly_white"

prices_db_path = './data/PriceData.sqlite'

base_index_table = 'Index_GER'
stock_prices_table = 'Equity_Prices_GER'
index_components_metadata_table = 'Index_DAX_Metadata'

## App Functions
@st.cache
def load_stock_prices():
    sql = """
        SELECT 
            *
        FROM {}

        WHERE Date >= '2000-01-01'
    """.format(stock_prices_table)
    stock_prices = read_sql_query(sql, prices_db_path).sort_values('Date').reset_index(drop=True)

    stock_prices['Date'] = stock_prices['Date'].apply(lambda x: x[:-11] + '01')

    stock_prices = stock_prices.groupby(['Date', 'Ticker']).agg({
            'Open':'first',    
            'High':max,
            'Low':min,
            'Close':'last',    
            'Volume':sum
        }).reset_index()

    stock_prices['Date'] = pd.to_datetime(stock_prices['Date'])

    return stock_prices


## App Functions
@st.cache
def load_index_components_metadata():
    sql = """
        SELECT 
            *
        FROM {}
    """.format(index_components_metadata_table)
    return read_sql_query(sql, prices_db_path)


## App Functions
@st.cache
def load_stock_index():
    sql = """
        SELECT 
            *
        FROM {}

        WHERE Date >= '2000-01-01'
        AND Ticker = '^GDAXI'
    """.format(base_index_table)
    index_data = read_sql_query(sql, prices_db_path)

    index_data = index_data.sort_values('Date')
    index_data['Date'] = index_data['Date'].apply(lambda x: x[:-11] + '01')

    index_data = index_data.groupby(['Date', 'Ticker']).agg({
            'Open':'first',    
            'High':max,
            'Low':min,
            'Close':'last',    
            'Volume':sum
        }).reset_index()

    index_data['Date'] = pd.to_datetime(index_data['Date'])

    return index_data

#@st.cache
#def prepare_commodities_download():
#    download_data = pd.read_csv(commodities_download_path)
#    return download_data.to_csv(index=False).encode('utf-8')


st.set_page_config(page_title='DAX Wertveränderung',
                    layout="wide")

st.markdown("## DAX Kursentwicklung")

index_data = load_stock_index()
candlestick_plotly_fig = plot_candlestick(index_data, subject_name='DAX')
st.plotly_chart(candlestick_plotly_fig, use_container_width=True)

# Metadata for stocks in index 
index_components_metadata = load_index_components_metadata()

index_components_price_history = load_stock_prices()

st.markdown("""
    ## Welche Aktien haben den DAX bewegt?

    #### Veränderung im Zeitraum:
    """)

col1, col2, _ = st.columns([1,1,3])

with col1:
    start_date = st.selectbox("Beginn", index_data.Date.dt.date.unique())
with col2:
    end_date = st.selectbox("Ende", index_data.Date.dt.date.sort_values(ascending=False).unique())

index_at_beginning = int(index_data.loc[index_data.Date.dt.date == start_date, 'Open'].iloc[0])
index_at_end = int(index_data.loc[index_data.Date.dt.date == end_date, 'Close'].iloc[0])

performance_absolute = index_at_end - index_at_beginning
performance_percentage = round((performance_absolute / index_at_beginning) * 100, 2)

st.markdown("""
+ Kursstand Beginn: {0}
+ Kursstand Ende: {1}
+ Performance: {2} ({3} %)

""".format('{:,}'.format(index_at_beginning), '{:,}'.format(index_at_end), '{:,}'.format(performance_absolute), str(performance_percentage)))


st.markdown("## Einfluss der Einzelwerte auf den Index")

#stocks_shap_values = index_components_shap_values(index_components_price_history, index_components_metadata[['Ticker', 'Index_Price_Factor']], end_date, start_date)
stocks_shap_values = index_components_shap_values(index_components_price_history, index_components_metadata, end_date, start_date)

plot_df = stocks_shap_values.sort_values('Stock_Performance', key=abs, ascending=True)[['Stock', 'Stock_Performance']]

#import numpy as np
#plot_df["Sign"] = np.where(plot_df["Stock_Performance"]<0, 'negative', 'positive')

fig = px.bar(plot_df,
             x="Stock_Performance", 
             y="Stock",
             #color='Sign',
             #color_discrete_map={'negative':'red', 'positive':'blue'},
             width=1000, 
             height=1000
            )

fig.update_yaxes(title="")
fig.update_xaxes(title="Einfluss auf Index")
fig.update_layout(title="Einfluss der Einzelwerte auf den DAX (" + str(start_date) + " - " + str(end_date) + ")",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)')

st.plotly_chart(fig)

st.markdown("## Entwicklung der Einzelwerte")

col_1, _ = st.columns([1,4])
with col_1:
    stock_of_interest = st.selectbox('Aktie', list(index_components_metadata['Name']))

stock_ticker = index_components_metadata.loc[index_components_metadata['Name'] == stock_of_interest, 'Ticker'].iloc[0]

stock_price_df = index_components_price_history.loc[index_components_price_history['Ticker'] == stock_ticker]
candlestick_plotly_fig = plot_candlestick(stock_price_df, subject_name=stock_of_interest)
st.plotly_chart(candlestick_plotly_fig, use_container_width=True)
