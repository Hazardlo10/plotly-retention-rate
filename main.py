# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dash.dependencies import Input, Output


df_init = pd.read_excel('TZ_Analitik.xlsx', sheet_name='dataset исправленный')
# Проверка того, что столбцы 'install_date', 'event_date', 'platform' уникальны. Мы предварительно удалили
# дубль (26.06.2018 26.06.2018 IOS):
df_init.groupby(['install_date', 'event_date', 'platform']).size().value_counts()

# Убеждаемся в том, что столбец period_day посчитан верно:
((df_init['event_date'] - df_init['install_date']).dt.days != df_init['period_day']).sum()

# Удаляем те install_date, для которых неизвестна активность в самый первый день:
dates_with_info = df_init[df_init['install_date'] == df_init['event_date']]['install_date']
df_init = df_init[df_init['install_date'].isin(dates_with_info)]

# Собственно строим графики в Plotly
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    dcc.Graph(id='retention'),
    dcc.Checklist(id='check_list', options=[{'label': 'IOS', 'value': 'IOS'}, {'label': 'ANDROID', 'value': 'ANDROID'}],
                  value=['IOS', 'ANDROID'], labelStyle={'display': 'block'}, style={'padding-left': 50}),
    dcc.DatePickerRange(id='date_range', start_date=date(2018, 6, 12), end_date=date(2018, 10, 4),
                        style={'padding-left': 50}, )
])


@app.callback(
    Output('retention', 'figure'),
    [Input('check_list', 'value'),
     Input('date_range', 'start_date'),
     Input('date_range', 'end_date'), ])
def update_graph(check_list, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df = df_init[df_init['platform'].isin(check_list)]
    df = df[(df['install_date'] >= start_date) & (df['install_date'] <= end_date)]
    ret = df.groupby('period_day')['cohort_size'].sum().to_frame()
    fig = go.Figure()
    if 0 not in ret.index:
        return fig
    ret['zero_day_cohort_size'] = ret.loc[0, 'cohort_size']
    ret['retention_rate'] = ret['cohort_size'] / ret['zero_day_cohort_size'] * 100
    fig.add_trace(go.Scatter(x=ret.index, y=ret['retention_rate'], mode='lines+markers'))

    fig.update_layout(
        title="Retention rate",
        xaxis_title="Количество дней",
        yaxis_title="%",
    )
    return fig


app.run_server(host='0.0.0.0', debug=False)
