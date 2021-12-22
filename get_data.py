from datetime import datetime, timedelta, date

import pandas as pd
from sqlalchemy import create_engine

from current_data import CURRENT_DATA_COLUMNS
from db_secrets import connection_data

EARLIEST_DATE = date(2021, 7, 23)


def init_connection():
    connection_string = (
        f"mysql+mysqlconnector://{connection_data['user']}:{connection_data['password']}"
        f"@{connection_data['host']}:{connection_data['port']}"
        f"/{connection_data['database']}?force_ipv6=true"
    )
    return create_engine(connection_string)


def date_filter_string(date_start: date, date_end: date, time_label="timestamp_tz"):
    return f"{time_label} >= '{date_start.isoformat()}' and {time_label} <= '{date_end.isoformat()}'"


def get_daily_values(date_start: date, date_end: date, db_connection=None):
    if db_connection is None:
        db_connection = init_connection()
    columns = [
        "date_tz",
        "temp_outdoor_c_avg",
        "temp_outdoor_c_min",
        "temp_outdoor_c_max",
        "rain_mm",
    ]
    query_string = f"SELECT {', '.join(columns)} FROM wetta.weather_data_daily"
    filter_string = date_filter_string(date_start, date_end, time_label="date_tz")
    data = pd.read_sql(
        f"{query_string} WHERE {filter_string}",
        db_connection,
        columns=columns,
        parse_dates=["date_tz"],
    )
    return data


def get_hourly_values(date_start: date, date_end: date, db_connection=None):
    if db_connection is None:
        db_connection = init_connection()
    columns = [
        "timestamp_tz",
        "temp_outdoor_c_avg",
        "temp_outdoor_c_min",
        "temp_outdoor_c_max",
        "rain_mm",
    ]
    query_string = f"SELECT {', '.join(columns)} FROM wetta.weather_data_hourly"
    filter_string = date_filter_string(date_start, date_end)
    data = pd.read_sql(
        f"{query_string} WHERE {filter_string}",
        db_connection,
        columns=columns,
        parse_dates=["timestamp_tz"],
    )
    return data


def get_current_data(db_connection=None):
    if db_connection is None:
        db_connection = init_connection()
    columns = [c.sql_column for c in CURRENT_DATA_COLUMNS]
    query_string = f"SELECT {', '.join(columns)} FROM wetta.weather_data"
    filter_string = "ORDER BY `timestamp` desc LIMIT 1"
    data = pd.read_sql(
        f"{query_string} {filter_string}",
        db_connection,
        columns=columns,
    )
    return data


if __name__ == "__main__":
    conn = init_connection()
    cols = ["temp_indoor_c", "temp_outdoor_c"]
    df = get_hourly_values(
        datetime.now() - timedelta(hours=10), datetime.now(), cols[0]
    )
    print(df)
