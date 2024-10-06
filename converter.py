import argparse
import logging
import os
import urllib.request
from typing import Tuple

import pandas as pd

OPENFLIGHTS_PLANES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/planes.dat"
OPENFLIGHTS_AIRLINES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"

APP_IN_THE_AIR_FIELDS = [
    "class",
    "seat",
    "pnr",
    "etkt",
    "what",
    "fare_class",
    "import_source",
    "airline_iata",
    "flight_number",
    "plane_iata",
    "from_iata",
    "to_iata",
    "dep_utc",
    "arr_utc",
    "dep_local",
    "arr_local",
    "booked",
]

OPENFLIGHTS_AIRLINES_FIELDS = [
    "full_name",
    "alias",
    "iata",
    "icao",
    "callsign",
    "country",
    "is_active",
]
OPENFLIGHTS_PLANE_FIELDS = ["full_name", "iata", "dafif"]

OPENFLIGHTS_AIRLINES_DATA_FILE = "airlines.dat"
OPENFLIGHTS_PLANES_DATA_FILE = "planes.dat"
EXTRA_PLANES_DATA_FILE = "extra_planes.dat"
EXTRA_AIRLINES_DATA_FILE = "extra_airlines.dat"


def format_timedelta(td: pd.Timedelta):
    hours = 24 * td.days + (td.seconds // (60 * 60))
    minutes = (td.seconds // 60) % 60

    return f"{hours:02}:{minutes:02}"


def download_openflights(data_dir: str) -> None:
    if not os.path.isdir(data_dir):
        raise ValueError(f"Data dir {data_dir} doesn't exist. Please create the directory first.")

    urllib.request.urlretrieve(OPENFLIGHTS_PLANES_URL, os.path.join(data_dir, OPENFLIGHTS_PLANES_DATA_FILE))
    urllib.request.urlretrieve(OPENFLIGHTS_AIRLINES_URL, os.path.join(data_dir, OPENFLIGHTS_AIRLINES_DATA_FILE))


def read_assets(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    openflights_airlines_path = os.path.join(data_dir, OPENFLIGHTS_AIRLINES_DATA_FILE)
    openflights_planes_path = os.path.join(data_dir, OPENFLIGHTS_PLANES_DATA_FILE)
    extra_airlines_path = os.path.join(data_dir, EXTRA_AIRLINES_DATA_FILE)
    extra_planes_path = os.path.join(data_dir, EXTRA_PLANES_DATA_FILE)

    airlines_df = pd.read_csv(openflights_airlines_path, index_col=0, header=None, names=OPENFLIGHTS_AIRLINES_FIELDS)
    planes_df = pd.read_csv(openflights_planes_path, header=None, names=OPENFLIGHTS_PLANE_FIELDS)

    airlines_df = airlines_df[airlines_df.is_active == "Y"]
    if os.path.isfile(extra_airlines_path):
        extra_airlines_df = pd.read_csv(extra_airlines_path, header=None, names=OPENFLIGHTS_AIRLINES_FIELDS)
        airlines_df = pd.concat([airlines_df, extra_airlines_df]).drop_duplicates(subset="iata", keep="last")

    if os.path.isfile(extra_planes_path):
        extra_planes_df = pd.read_csv(extra_planes_path, header=None, names=OPENFLIGHTS_PLANE_FIELDS)
        planes_df = pd.concat([planes_df, extra_planes_df]).drop_duplicates(subset="iata", keep="last")

    return airlines_df, planes_df


def read_flight_data(input: str) -> pd.DataFrame:
    flights = []
    is_flights_section = False

    with open(input, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0:
                continue

            if line.startswith("flights:"):
                is_flights_section = True
                continue

            if line.startswith("hotels:"):
                is_flights_section = False
                continue

            if not is_flights_section:
                continue

            arr = line.split(";")

            if len(arr) != len(APP_IN_THE_AIR_FIELDS):
                logging.warning(f"Unable to parse: {line}")
                continue

            flights.append(arr)

    return pd.DataFrame(flights, columns=APP_IN_THE_AIR_FIELDS).replace("None", None)


def convert(flights_df: pd.DataFrame, airlines_df: pd.DataFrame, planes_df: pd.DataFrame) -> pd.DataFrame:
    def plane_iata_to_name(iata_code: str):
        plane_info = planes_df[planes_df.iata == iata_code]
        if len(plane_info) == 1:
            return plane_info.iloc[0].full_name
        else:
            if iata_code != "None":
                logging.debug(f"Found {len(plane_info)} records for {iata_code} plane designator. Skipping")
            return None

    def airline_iata_to_name(iata_code: str):
        airline_info = airlines_df[(airlines_df.iata == iata_code) & (airlines_df.is_active == "Y")]
        if len(airline_info) == 1:
            return airline_info.iloc[0].full_name
        else:
            if iata_code != "None":
                logging.debug(f"Found {len(airline_info)} records for {iata_code} airline designator. Skipping")
            return None

    df = pd.DataFrame()

    df["Date"] = pd.to_datetime(flights_df.dep_local).dt.date
    df["Flight number"] = flights_df.airline_iata + flights_df.flight_number.astype(int).astype(str)
    df["From"] = flights_df.from_iata
    df["To"] = flights_df.to_iata
    df["Dep time"] = pd.to_datetime(flights_df.dep_local).dt.time
    df["Arr time"] = pd.to_datetime(flights_df.arr_local).dt.time
    df["Duration"] = (pd.to_datetime(flights_df.arr_utc) - pd.to_datetime(flights_df.dep_utc)).map(
        lambda x: format_timedelta(x)
    )
    df["Airline"] = flights_df["airline_iata"].apply(airline_iata_to_name)
    df["Aircraft"] = flights_df["plane_iata"].apply(plane_iata_to_name)
    df["Seat number"] = flights_df.seat

    return df


def remove_duplicates(flights_df: pd.DataFrame) -> pd.DataFrame:
    duplicates_found = flights_df[flights_df.duplicated(subset=['Date', 'From', 'To'], keep=False)]
    if not duplicates_found.empty:
        logging.warning(f"These are the duplicated/codeshare flights:\n"
                        f"{duplicates_found.sort_values(by='Date').to_string(index=False)}")
    else:
        logging.warning("No duplicates/codeshare have been found.")

    return  flights_df.drop_duplicates(subset=['Date', 'From', 'To'], ignore_index=True)


def main():
    parser = argparse.ArgumentParser(
        description='Command-line tool to convert "App in the Air" data export to MyFlighradar24 format'
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Folder to store downloaded assets and extra data",
    )
    parser.add_argument(
        "-s",
        "--skip-download",
        action="store_true",
        help="Skips downloading external assets. Assets must already be present in the data folder",
    )

    parser.add_argument(
        "--remove-duplicates",
        action="store_true",
        help="Remove duplicated/codeshare flights. These are the flights with the same route on the same date",
    )

    parser.add_argument("-i ", "--input", type=str, required=True, help="App in the Air export file path")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output csv path")

    args = parser.parse_args()

    if not args.skip_download:
        download_openflights(args.data_dir)

    airlines_df, planes_df = read_assets(args.data_dir)
    flights_df = read_flight_data(args.input)

    df = convert(flights_df, airlines_df, planes_df)
    if args.remove_duplicates:
        df = remove_duplicates(df)
    df.sort_values(by='Date').to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
