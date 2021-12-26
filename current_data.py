import dataclasses

import dash_bootstrap_components as dbc
from dash import html


@dataclasses.dataclass
class DashboardData:
    sql_column: str
    label: str
    category: str
    html_id: str = None
    unit: str = ""

    def __post_init__(self):
        if self.html_id is None:
            self.html_id = "current-" + self.sql_column

    def to_html(self):
        return html.Div(
            [
                dbc.CardBody(
                    self.label + ": ", style={"fontSize": "1rem", "padding": "0.3rem"}
                ),
                dbc.CardBody(
                    [
                        html.Span(id=self.html_id),
                        html.Span(self.unit, className="text-muted"),
                    ],
                    style={"fontSize": "3rem"},
                ),
            ]
        )

    def process_value(self, value):
        return value


def process_wind_direction(degree):
    directions = [
        "Nord",
        "Nord-Nordost",
        "Nordost",
        "Ost-Nordost",
        "Ost",
        "Ost-Südost",
        "Südost",
        "Süd-Südost",
        "Süd",
        "Süd-Südwest",
        "Südwest",
        "West-Südwest",
        "West",
        "West-Nordwest",
        "Nordwest",
        "Nord-Nordwest",
        "Nord",
    ]
    section = round(degree / (360 / (len(directions) - 1)))
    return directions[section]


class WindDirectionData(DashboardData):
    def process_value(self, value):
        return f"{process_wind_direction(value)} - {value}"


class TimeData(DashboardData):
    def process_value(self, value):
        return f"Zeitpunkt der Daten: {value}"


CURRENT_DATA_CATEGORIES = [
    "Temperatur",
    "Luftfeuchtigkeit",
    "Sonne",
    "Niederschlag",
    "Wind",
    "Luftdruck",
]
CURRENT_DATA_COLUMNS = [
    DashboardData(
        "ROUND(temp_outdoor_c,1)", "Draußen", "Temperatur", "current-temp-outdoor", "°C"
    ),
    DashboardData(
        "ROUND(temp_indoor_c,1)", "Drinnen", "Temperatur", "current-temp-indoor", "°C"
    ),
    DashboardData("humidity_outdoor", "Draußen", "Luftfeuchtigkeit", unit="%"),
    DashboardData("humidity_indoor", "Drinnen", "Luftfeuchtigkeit", unit="%"),
    DashboardData(
        "ROUND((barometer * 33.8639),2)",
        "Relativ",
        "Luftdruck",
        "current-pressure-relative",
        unit="hPA",
    ),
    DashboardData(
        "ROUND((pressure * 33.8639),2)",
        "Absolut",
        "Luftdruck",
        "current-pressure-absolut",
        unit="hPA",
    ),
    WindDirectionData("wind_direction", "Richtung", "Wind", unit="°"),
    DashboardData(
        "ROUND(wind_speed_kmh,1)",
        "Geschwindigkeit",
        "Wind",
        "current-wind-speed",
        unit="km/h",
    ),
    DashboardData(
        "ROUND(wind_gust_kmh,1)", "Böe", "Wind", "current-wind-gust", unit="km/h"
    ),
    DashboardData(
        "ROUND(rain_event_mm,2)",
        "Letzes Ereignis",
        "Niederschlag",
        "rain-event",
        unit="mm",
    ),
    DashboardData(
        "ROUND(rain_hourly_mm,2)",
        "Diese Stunde",
        "Niederschlag",
        "rain-hour",
        unit="mm",
    ),
    DashboardData(
        "ROUND(rain_daily_mm,2)", "Dieser Tag", "Niederschlag", "rain-day", unit="mm"
    ),
    DashboardData(
        "ROUND(rain_weekly_mm,2)", "Diese Woche", "Niederschlag", "rain-week", unit="mm"
    ),
    DashboardData(
        "ROUND(rain_monthly_mm,2)",
        "Dieser Monat",
        "Niederschlag",
        "rain-month",
        unit="mm",
    ),
    DashboardData("radiation", "Sonnenstrahlung", "Sonne", unit="kLux"),
    DashboardData("uv", "UV-Index", "Sonne"),
    TimeData(
        "CONVERT_TZ(`timestamp`, 'GMT', 'Europe/Berlin') AS `timestamp`",
        "Zeit",
        "Meta",
        "current-time",
    ),
]


def dashboard_html():
    html_parts = []
    for category in CURRENT_DATA_CATEGORIES:
        html_parts.append(
            dbc.Col(
                dbc.Spinner(
                    dbc.Card(
                        children=[
                            dbc.CardHeader(category),
                            *[
                                c.to_html()
                                for c in CURRENT_DATA_COLUMNS
                                if c.category == category
                            ],
                        ],
                        class_name="text-white bg-dark",
                    ),
                    color="info",
                ),
                width=4,
            )
        )

    return dbc.Row(html_parts, class_name="gy-2 gx-2")
