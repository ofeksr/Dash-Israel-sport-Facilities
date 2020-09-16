import re
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


def most_common_facility_type():
    # איזה סוג מגרש הוא הנפוץ ביותר ?
    df_copy = df
    df_copy['סוג מתקן חדש'] = df_copy['סוג מתקן'].apply(
        lambda fac_type: ''.join(fac_type.replace('-', '–').split('–')[0]).strip())
    df_copy = df_copy[df_copy['סוג מתקן חדש'].str.contains('אחר:') == 0]
    df_copy = df_copy['סוג מתקן חדש'].value_counts()

    fig = px.bar(df_copy)
    fig.update_traces(text=df_copy.values, textposition='outside')
    fig.update_layout(
        title=dict(
            text='<b>שכיחות סוגי המתקנים בישראל</b>',
            xanchor='center',
            yanchor='top',
            y=1,
            x=0.5
        ),
        yaxis_title='מספר מתקנים',
        xaxis_title='סוג מתקן',
        showlegend=False,
    )
    # fig.write_html('most_common_facility_type.html', auto_open=True)
    return fig


def fewest_good_facilities():
    # הכי פחות מתקנים תקינים
    facility_status = df.groupby(['מצב המתקן', 'רשות מקומית']).count()['סוג מתקן'].unstack(0, fill_value=0)
    facility_status['סהכ'] = facilities_per_city
    facility_status = facility_status.sort_values(['לא תקין ולא פעיל', 'לא פעיל']).tail(10)[
        ['לא תקין ולא פעיל', 'לא פעיל', 'סהכ']]

    fig = px.bar(facility_status)
    fig.update_layout(barmode='group')
    fig.update_layout(
        title=dict(
            text='<b>שכיחות הלא תקינים הגבוהה ביותר</b>',
            xanchor='center',
            yanchor='top',
            y=1,
            x=0.5
        ),
        yaxis_title='מספר מתקנים',
        xaxis_title='רשות מקומית',
    )
    # fig.write_html('fewest_good_facilities.html', auto_open=True)
    return fig


def established_vs_condition():
    # שנת הקמה מול מצב מתקן
    established = df.groupby(['שנת הקמה', 'מצב המתקן']).count()['סוג מתקן'].unstack(fill_value=0)
    established = established.drop(columns=['תקין ופעיל']).sort_values(['לא תקין ולא פעיל', 'לא פעיל'],
                                                                       ascending=True).tail(12)
    established = established.sort_index()

    fig = px.bar(established)
    fig.update_layout(
        xaxis_type='category',
        title=dict(
            text='<b>תקינות המתקנים מאז הקמתם</b>',
            xanchor='center',
            yanchor='top',
            y=1,
            x=0.5
        ),
        yaxis_title='מספר מתקנים',
        xaxis_title='שנת הקמה'
    )
    # fig.write_html('established_vs_condition.html', auto_open=True)
    return fig


def lights_nor_fences():
    # לא תאורה ולא גידור מתוך סהכ מתקנים
    light_n_fences = df[(df['גידור קיים'] == 'לא') & (df['תאורה קיימת'] == 'לא')].groupby(
        'רשות מקומית').count()
    light_n_fences['סהכ מתקנים'] = facilities_per_city
    light_n_fences = light_n_fences[['גידור קיים', 'סהכ מתקנים']].sort_values('גידור קיים', ascending=False).head(
        10).rename(columns={'גידור קיים': 'לא גידור ולא אורות'})

    fig = px.bar(light_n_fences)
    fig.update_layout(
        title=dict(
            text='<b>לא תאורה ולא גידור</b>',
            xanchor='center',
            yanchor='top',
            y=1,
            x=0.5
        ),
        yaxis_title='מספר מתקנים',
        xaxis_title='רשות מקומית',
        legend_title_text=''
    )
    # fig.write_html('lights_nor_fences.html', auto_open=True)
    return fig


def accessible_facilities_status():
    # היכן כמות המתקנים הנגישים הכי גבוהה
    top_accessible = df.groupby(['נגישות לנכים', 'רשות מקומית']).count()['סוג מתקן'].unstack(0)
    top_accessible['סהכ מתקנים'] = facilities_per_city
    top_accessible = top_accessible[['כן', 'סהכ מתקנים']].sort_values('כן', ascending=False).head(10)

    bottom_accessible = df.groupby(['נגישות לנכים', 'רשות מקומית']).count()['סוג מתקן'].unstack().loc[
        'כן'].sort_values(
        ascending=False).fillna(0)
    all_bottom_accessible = bottom_accessible[bottom_accessible <= 1]

    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "bar"}, {"type": "table"}]],
                        column_widths=[0.8, 0.2],
                        subplot_titles=("<b>הכי הרבה מתקנים נגישים</b>", "<b>פחות ממתקן נגיש יחיד</b>"),
                        y_title='כמות מתקנים')
    fig_1 = go.Bar(x=top_accessible.index, y=top_accessible['כן'], name='מתקנים נגישים')
    fig_2 = go.Bar(x=top_accessible.index, y=top_accessible['סהכ מתקנים'], name='סהכ מתקנים')
    fig.add_trace(
        fig_1,
        row=1, col=1
    )
    fig.add_trace(
        fig_2,
        row=1, col=1
    )
    fig.add_trace(
        go.Table(
            header=dict(
                values=['רשות מקומית'],
                font=dict(size=12),
                align="right",
            ),
            cells=dict(
                values=[all_bottom_accessible.index.tolist()],
                align="right"
            ),
        ),
        row=1, col=2
    )
    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01)
    )
    # fig.write_html('accessible_facilities_status.html', auto_open=True)
    return fig


def email_domain_of_workers():
    # מהו דומיין האינטרנט הנפוץ ביותר בקרב מפעילי המתקנים
    email_domains = df['דואל איש קשר'].apply(
        lambda e: re.findall("@\w*([\.\w*]*)", str(e)))
    email_domains = email_domains.value_counts().iloc[1:]

    fig = px.pie(email_domains, values=email_domains.values, names=email_domains.index)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    # fig.write_html('email_domains.html', auto_open=True)

    return fig


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

df = pd.read_excel('datasets/sport_facilities.xlsx', encoding='UTF-8')
cities = df['רשות מקומית'].unique()
facilities_per_city = df['רשות מקומית'].value_counts()

graphs = ['most_common_facility_type', 'fewest_good_facilities', 'established_vs_condition', 'lights_nor_fences',
          'accessible_facilities_status', 'email_domain_of_workers']
opts = [{'label': i, 'value': i} for i in graphs]

fig = email_domain_of_workers()

app.layout = html.Div(children=[
    html.H1(children='Sport Facilities Stats in Israel'),

    html.Div(children='''
                    built with Dash: A web application framework for Python.
                '''),

    html.Br(),

    html.P("""
        בתור אחד שמשחק כדורסל במגרשים העירוניים,
    """,
           dir='rtl'),
    html.P("""
            עניין אותי לדעת איפה עומדת העיר שלי ביחס לערים האחרות מבחינת היצע מגרשים תקניים.
     """,
           dir='rtl'),

    html.Br(),
    html.P('''
        קוד הפרויקט זמין כאן: 
        ''',
           dir='rtl'),
    html.P(html.A('github/ofeksr/Dash-Israel-sport-Facilities',
                  href='https://github.com/ofeksr/Dash-Israel-sport-Facilities'),
           dir='rtl'),
    html.P('''
        מאגר הנתונים נלקח מאתר מאגרי המידע המששלתיים:
        ''',
           dir='rtl'),
    html.P(html.A('data.gov.il',
                  href='https://data.gov.il/'),
           dir='rtl'),
    html.Br(),

    html.P([
        html.Label("Choose a graph"),
        dcc.Dropdown(id='opt', options=opts,
                     value=graphs[0])
    ], style={'width': '400px',
              'fontSize': '20px',
              'padding-left': '100px',
              'display': 'inline-block'}),

    dcc.Graph(
        id='main',
        figure=fig
    ),

])


@app.callback(Output('main', 'figure'),
              [Input('opt', 'value')])
def update_figure(input1):
    return getattr(sys.modules[__name__], input1)()


if __name__ == '__main__':
    email_domain_of_workers()
    app.run_server(debug=True)
