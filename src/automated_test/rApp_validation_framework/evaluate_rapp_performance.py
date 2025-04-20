import json
import os
import time
import pandas as pd
import logging
from influxdb import DataFrameClient
from configparser import ConfigParser
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from requests.exceptions import RequestException, ConnectionError
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def read_db_config():
    """ Read the db_config.ini file and return database parameters """
    cfg = ConfigParser()

    config_path = os.path.join(os.path.dirname(__file__), 'db_config.ini')

    if not os.path.exists(config_path):
        print(f"❌ db_config.ini not found. Please check the path: {config_path}")
        return {}

    cfg.read(config_path)
    
    config = {}
    for section in cfg.sections():
        if section == 'influxdb':
            config = {
                "host": cfg.get(section, "host"),
                "port": cfg.get(section, "port"),
                "user": cfg.get(section, "user"),
                "password": cfg.get(section, "password"),
                "measurement": cfg.get(section, "measurement"),
                "token": cfg.get(section, "token"),
                "org": cfg.get(section, "org"),
                "bucket": cfg.get(section, "bucket"),
                "address": cfg.get(section, "address"),
            }
    return config

def connect_to_influxdb(config):
    """ Connect to InfluxDB and return the client object """
    client = None
    try:
        client = influxdb_client.InfluxDBClient(url=config["address"], org=config["org"], token=config["token"])
        version = client.version()
        logger.info("Connected to Influx Database, InfluxDB version: {}".format(version))
        return client
    except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError):
        logger.error("Failed to establish a connection with InfluxDB. Please check your URL/hostname.")
        return None

def query_data(client, query, org):
    """ Execute a query and return the result """
    while True:
        try:
            query_api = client.query_api()
            result = query_api.query_data_frame(org=org, query=query)
            logger.info(f'Cell data: {result}')
            return result
        except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError) as e:
            logger.error(f'Failed to query InfluxDB: {e}. Retrying in 60 seconds...')
            time.sleep(60)

def read_data(client, org, bucket, start="-5m", stop=None, fields=None):
    """ Read data from InfluxDB """
    if fields:
        print("📊 Fields to be fetched:")
        print(fields)  # Show which fields will be fetched
    else:
        print("⚠️ No fields specified, fetching all fields.")

    query = f'from(bucket:"{bucket}")'

    if stop:
        query += f' |> range(start: {start}, stop: {stop}) '
    else:
        query += f' |> range(start: {start}) '

    query += ' |> filter(fn: (r) => r["_measurement"] == "CellReports")'

    if fields:
        field_conditions = ' or '.join([f'r["_field"] == "{field}"' for field in fields])
        query += f' |> filter(fn: (r) => {field_conditions}) '

    query += ' |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value") '

    return query_data(client, query, org)

def get_avg_value_from_data(df, field_name):
    """ Calculate the average value of the specified field """
    if df is None or df.empty:
        logger.warning(f"⚠️ No data received to calculate average for {field_name}.")
        return None

    if field_name not in df.columns:
        logger.warning(f"⚠️ '{field_name}' column not found in the data.")
        return None

    try:
        values = pd.to_numeric(df[field_name], errors='coerce')
        avg = values.mean()
        return avg
    except Exception as e:
        logger.error(f"❌ Failed to calculate average for {field_name}: {e}")
        return None

def fetch_and_calculate_avg(client, db_config, fields, start_time):
    """ Fetch data and calculate average values for specified fields """
    data = read_data(client, db_config["org"], db_config["bucket"], start=start_time, fields=fields)
    avg_results = {}

    for field in fields:
        avg = get_avg_value_from_data(data, field)
        if avg is not None:
            avg_results[field] = avg
    print("avg_results",avg_results)
    return avg_results

def compare_two_runs(first_run_data, second_run_data, expectation_targets):
    """ Compare the data of two test runs based on pre-calculated averages """
    print("📋 Test expectations overview:")
    for target in expectation_targets:
        print(f"🔸 Target name: {target.get('targetName')}")
        print(f"   Condition: {target.get('targetCondition')}")
        print(f"   Expected value range: {target.get('targetValueRange')} {target.get('targetUnit', '')}")
        print(f"   Scope: {target.get('targetScope')}")
        print("")

    for target in expectation_targets:
        field = target.get("targetName")
        condition = target.get("targetCondition")
        value_range = target.get("targetValueRange", [])
        unit = target.get("targetUnit", "")
        
        avg1 = first_run_data.get(field)
        avg2 = second_run_data.get(field)

        if avg1 is None or avg2 is None:
            print(f"⚠️ Skipping comparison for {field} due to missing data.")
            continue

        print(f"\n📊 Comparing field: {field}")
        print(f"   First simulation avg: {avg1}")
        print(f"   Second simulation avg: {avg2}")

        if condition == "IS_LESS_THAN_OR_EQUAL_TO" and value_range:
            threshold = avg1 * (float(value_range[0]) / 100)
            print(f"   Expectation: <= {float(value_range[0])}% of first run → {threshold:.2f} {unit}")
            if avg2 <= threshold:
                print(f"✅ Success: {field} decreased as expected.")
            else:
                print(f"❌ Failed: {field} did not decrease enough.")

        elif condition == "IS_GREATER_THAN_OR_EQUAL_TO" and value_range:
            threshold = avg1 * (float(value_range[0]) / 100)
            print(f"   Expectation: >= {float(value_range[0])}% of first run → {threshold:.2f} {unit}")
            if avg2 >= threshold:
                print(f"✅ Success: {field} increased as expected.")
            else:
                print(f"❌ Failed: {field} did not increase enough.")
        else:
            print("⚠️ Unsupported condition or missing value range.")

def parse_pass_criteria():
    """ Parse test-spec.json file and return expected test criteria """
    file_path = os.path.join(os.getcwd(), 'test-spec.json')
    
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        expectation_targets = data.get("testSpecifications", [])[0].get("expectationTargets", [])
        
        if expectation_targets:
            results = []
            for target in expectation_targets:
                result = {
                    "targetName": target.get("targetName"),
                    "targetCondition": target.get("targetCondition"),
                    "targetValueRange": target.get("targetValueRange"),
                    "targetUnit": target.get("targetUnit"),
                    "targetScope": target.get("targetScope")
                }
                results.append(result)
            
            return results
        else:
            print("❌ No expectation targets found.")
            return []

    except Exception as e:
        print(f"❌ Failed to read or parse the JSON file: {e}")
        return []



