import datetime
from datetime import timedelta, date

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from current_data import CURRENT_DATA_COLUMNS
from current_data import dashboard_html
from get_data import get_hourly_values, get_daily_values, get_current_data, EARLIEST_DATE

external_scripts = ["https://cdn.plot.ly/plotly-locale-de-latest.js"]
external_stylesheets = [
    "https://use.fontawesome.com/releases/v5.9.0/css/all.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"
]
app = dash.Dash(__name__, external_scripts=external_scripts, external_stylesheets=external_stylesheets)
server = app.server

config_plots = dict(locale="de")
app.layout = dbc.Container(children=[
    html.H1(children="Wetta Wilsum"),
    dbc.Tabs(children=[
        dbc.Tab(label="Aktuelle Daten", children=[
            html.Div(id="current-time", children="Lädt..."),
            html.Div(children=dashboard_html()),
            dcc.Interval(id="minute-interval", interval=60 * 1000),
        ]),
        dbc.Tab(label="Historische Daten", children=[
            dbc.Card(
                children="Zeitraum für Wetterdaten angeben:"
            ),
            dbc.Form(children=[
                html.Div(className="mb-3", children=[
                    html.Label("Von"),
                    dbc.Input(id="date-from", type="date", value=date.today() - timedelta(days=8), min=EARLIEST_DATE,
                              max=date.today(), required=True),
                ]),

                html.Div(className="mb-3", children=[
                    html.Label("Bis"),
                    dbc.Input(id="date-to", type="date", value=date.today(), min=EARLIEST_DATE, max=date.today(),
                              required=True),
                ]),
                html.Div(className="mb-3", children=[
                    dbc.RadioItems(
                        options=[
                            {'label': 'Täglich', 'value': 'daily'},
                            {'label': 'Stündlich', 'value': 'hourly'},
                        ],
                        value='daily',
                        id="check-period",
                    )]),
            ]),
            html.Div(className="row", children=[
                dcc.Graph(id="rain-graph", config=config_plots, className="col-xl-12")]),
            dcc.Graph(id="outdoor-temp-graph", config=config_plots, className="col-xl-12"),
        ]
                )])]
)


def draw_temp_graph(df, time_label):
    fig = go.Figure()
    text_template = "%{y:.1f}°C" if len(df) <= 30 else None
    fig.add_trace(
        go.Scatter(
            x=df[time_label],
            y=df["temp_outdoor_c_avg"],
            name="Ø",
            mode="lines+markers",
            marker_color="grey",
            hovertemplate=None,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df[time_label],
            y=df["temp_outdoor_c_min"],
            name="Min",
            mode="markers+text",
            marker_color="blue",
            hovertemplate=None,
            texttemplate=text_template,
            textposition="bottom center"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df[time_label],
            y=df["temp_outdoor_c_max"],
            name="Max",
            mode="markers+text",
            marker_color="red",
            hovertemplate=None,
            texttemplate=text_template,
            textposition="top center"
        )
    )
    fig.update_layout(hovermode="x")
    fig.update_yaxes(title_text="Temperatur (°C)")
    return fig


def draw_rain_graph(df, time_label):
    fig = go.Figure()
    fig.add_bar(x=df[time_label], y=df["rain_mm"], textposition="auto", texttemplate="%{y:.2f}mm")
    fig.update_yaxes(title_text="Niederschlag (mm)")
    return fig


@app.callback(
    *[Output(c.html_id, "children") for c in CURRENT_DATA_COLUMNS],
    [Input("minute-interval", "n_intervals")],
)
def update_current(_):
    values = get_current_data().values[0]
    processed_values = []
    for value, dashboard_data in zip(values, CURRENT_DATA_COLUMNS):
        processed_values.append(dashboard_data.process_value(value))
    return processed_values


@app.callback(
    Output("date-from", "max"), Output("date-to", "max"),
    [Input("minute-interval", "n_intervals")],
)
def update_date_picker(_):
    return date.today(), date.today()


@app.callback(
    Output("date-from", "value"), Output("date-to", "value"),
    [Input("date-from", "value"), Input("date-to", "value")],
)
def update_date_from_picker(date_from_str, date_to_str):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    date_from = date.fromisoformat(date_from_str)
    date_to = date.fromisoformat(date_to_str)
    if date_from > date_to:
        match trigger:
            case "date-from":
                date_to = date_from
            case "date-to":
                date_from = date_to
            case _:
                raise PreventUpdate
    return date_from, date_to


@app.callback(
    Output("outdoor-temp-graph", "figure"),
    Output("rain-graph", "figure"),
    [Input("date-from", "value"), Input("date-to", "value"), Input("check-period", "value")],
)
def update_historical(date_from_str, date_to_str, check_period):
    date_from = datetime.date.fromisoformat(date_from_str)
    date_to = datetime.date.fromisoformat(date_to_str) + timedelta(days=1) - timedelta(minutes=1)

    match check_period:
        case "hourly":
            time_label, df = "timestamp_tz", get_hourly_values(date_from, date_to)
        case "daily":
            time_label, df = "date_tz", get_daily_values(date_from, date_to)
        case _:
            raise Exception("unknown time interval...")

    return draw_temp_graph(df, time_label), draw_rain_graph(df, time_label)


if __name__ == "__main__":
    app.run_server(debug=True)
