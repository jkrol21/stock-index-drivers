import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3

def read_sql_query(sql, db_path):
    with sqlite3.connect(db_path) as con:
        return pd.read_sql(sql, con)


def index_components_shap_values(index_components_history, index_components_metadata, reference_date, performance_since_date):
    
    prices_at_start = index_components_history.loc[index_components_history.Date.dt.date == performance_since_date, ['Ticker','Open']]
    prices_at_end = index_components_history.loc[index_components_history.Date.dt.date == reference_date, ['Ticker','Close']]

    points_performance_start = pd.merge(
                                        prices_at_start, 
                                        index_components_metadata[['Ticker', 'Index_Price_Factor']])
    
    points_performance_start['Points_Start'] = points_performance_start['Open'] * points_performance_start['Index_Price_Factor']

    points_performance_end = pd.merge(
                                        prices_at_end, 
                                        index_components_metadata[['Ticker', 'Index_Price_Factor']])
    points_performance_end['Points_End'] = points_performance_end['Close'] * points_performance_end['Index_Price_Factor']
    
    points_performance = pd.merge(
                                    points_performance_start[['Ticker', 'Points_Start']],
                                    points_performance_end[['Ticker', 'Points_End']])

    points_performance['Stock_Performance'] = points_performance['Points_End'] - points_performance['Points_Start']
    
    # let's use the nice naming for plotting
    points_performance = pd.merge(points_performance, index_components_metadata[['Ticker', 'Name']], how='left', on='Ticker')

    points_performance = points_performance[['Name', 'Stock_Performance']]

    points_performance.columns = ['Stock', 'Stock_Performance']

    return points_performance


def plot_candlestick(plot_df, subject_name=''):
    candlesticks = go.Candlestick(
        x=plot_df['Date'],
        open=plot_df['Open'],
        high=plot_df['High'],
        low=plot_df['Low'],
        close=plot_df['Close'],
        showlegend=False
    )

    volume_bars = go.Bar(
        x=plot_df['Date'],
        y=plot_df['Volume'],
        showlegend=False,
        marker={
            "color": "#b3b3b3",
        }
    )

    fig = go.Figure(candlesticks)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    #fig.update_layout(
    #    autosize=False,
    #    width=900,
    #    height=600
    #)
    fig.add_trace(candlesticks, secondary_y=True)
    fig.add_trace(volume_bars, secondary_y=False)
    fig.update_layout(title="Kursentwicklung - " + subject_name, 
                        height=800,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)')
    fig.update_yaxes(title="Kurs", secondary_y=True, showgrid=True)
    fig.update_yaxes(title="Volumen", secondary_y=False, showgrid=False)
    
    return fig