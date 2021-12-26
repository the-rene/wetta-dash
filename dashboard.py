from datetime import timedelta, date

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

from current_data import CURRENT_DATA_COLUMNS
from current_data import dashboard_html
from get_data import (
    get_hourly_values,
    get_daily_values,
    get_current_data,
    EARLIEST_DATE,
)

external_scripts = ["https://cdn.plot.ly/plotly-locale-de-latest.js"]
external_stylesheets = [
    "https://use.fontawesome.com/releases/v5.9.0/css/all.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
]
app = dash.Dash(
    __name__,
    external_scripts=external_scripts,
    external_stylesheets=external_stylesheets,
    title="Wetta",
)
server = app.server

config_plots = dict(locale="de")
current_layout = html.Div(
    [
        html.Div(id="current-time", children="Lädt...", style={"fontSize": "1rem"}),
        dbc.Spinner(dashboard_html(), color="info"),
        dcc.Interval(id="minute-interval", interval=60 * 1000),
    ]
)

date_form = dbc.Form(
    [
        dbc.Label("Zeitraum für Wetterdaten angeben:"),
        dbc.Row(
            [
                dbc.Col(
                    width=3,
                    children=[
                        dbc.Label("Von"),
                        dbc.Input(
                            id="date-from",
                            type="date",
                            value=date.today() - timedelta(days=8),
                            min=EARLIEST_DATE,
                            max=date.today(),
                            required=True,
                        ),
                    ],
                ),
                dbc.Col(
                    width=3,
                    children=[
                        dbc.Label("Bis"),
                        dbc.Input(
                            id="date-to",
                            type="date",
                            value=date.today(),
                            min=EARLIEST_DATE,
                            max=date.today(),
                            required=True,
                        ),
                    ],
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Interval:"),
                        dbc.RadioItems(
                            options=[
                                {"label": "Täglich", "value": "daily"},
                                {"label": "Stündlich", "value": "hourly"},
                            ],
                            value="daily",
                            id="check-period",
                        ),
                    ],
                    width=6,
                )
            ]
        ),
    ]
)
historical_layout = dbc.Container(
    [
        date_form,
        dbc.Spinner(
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="rain-graph", config=config_plots), width=12),
                    dbc.Col(
                        dcc.Graph(id="outdoor-temp-graph", config=config_plots),
                        width=12,
                    ),
                ]
            ),
            color="info",
        ),
        html.P(
            [
                html.Span(id="picked-date-from"),
                html.Span(id="picked-date-to"),
            ], hidden=True # hidden. only used to render changed dates before redering graphs
        ),
    ],
    fluid=True,
)

app.layout = dbc.Container(
    fluid=True,
    style={"fontSize": "1.5rem"},
    children=[
        html.H1(children="Wetta Wilsum"),
        dbc.Tabs(
            children=[
                dbc.Tab(label="Aktuelle Daten", children=current_layout),
                dbc.Tab(label="Historische Daten", children=historical_layout),
            ]
        ),
    ],
)


def draw_temp_graph(df, time_label):
    fig = go.Figure(layout=go.Layout(margin={"l": 0, "r": 0, "t": 20, "b": 20}))
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
            textposition="bottom center",
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
            textposition="top center",
        )
    )
    fig.update_layout(hovermode="x")
    fig.update_yaxes(title_text="Temperatur (°C)")
    return fig


def draw_rain_graph(df, time_label):
    fig = go.Figure(layout=go.Layout(margin={"l": 0, "r": 0, "t": 20, "b": 20}))
    fig.add_bar(
        x=df[time_label],
        y=df["rain_mm"],
        textposition="auto",
        texttemplate="%{y:.2f}mm",
    )
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
    Output("date-from", "max"),
    Output("date-to", "max"),
    [Input("minute-interval", "n_intervals")],
)
def update_date_picker_max(_):
    return date.today(), date.today()


def get_trigger_source():
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    return trigger


@app.callback(
    Output("picked-date-from", "children"),
    Output("picked-date-to", "children"),
    Output("date-from", "value"),
    Output("date-to", "value"),
    [
        Input("date-from", "value"),
        Input("date-to", "value"),
        Input("check-period", "value"),
    ],
)
def update_date_picker(date_from_str, date_to_str, check_period):
    date_from = date.fromisoformat(date_from_str)
    date_to = date.fromisoformat(date_to_str)
    trigger = get_trigger_source()
    if date_from > date_to:
        match trigger:
            case "date-from":
                date_to = date_from
            case "date-to":
                date_from = date_to
    if trigger == "check-period":
        match check_period:
            case "hourly":
                date_from = date.today() - timedelta(days=1)
                date_to = date.today()
            case "daily":
                date_from = date.today() - timedelta(days=8)
                date_to = date.today()
    return 2 * (date_from, date_to)


@app.callback(
    Output("outdoor-temp-graph", "figure"),
    Output("rain-graph", "figure"),
    [
        Input("picked-date-from", "children"),
        Input("picked-date-to", "children"),
        State("check-period", "value"),
    ],
)
def update_historical(date_from_str, date_to_str, check_period):
    date_from = date.fromisoformat(date_from_str)
    date_to = date.fromisoformat(date_to_str)

    match check_period:
        case "hourly":
            time_label, df = "timestamp_tz", get_hourly_values(date_from, date_to)
        case "daily":
            time_label, df = "date_tz", get_daily_values(date_from, date_to)
        case _:
            raise Exception("unknown time interval...")

    return draw_temp_graph(df, time_label), draw_rain_graph(df, time_label)


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
