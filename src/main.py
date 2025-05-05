import json
import os
import time
import pandas as pd
import requests
import logging


from automated_test.ric_test_config_generator.generate_cell_config import (
    load_cell_config,
    generate_cell_profiles,
    calculate_total_number_of_cells
)
from automated_test.ric_test_config_generator.generate_ue_config import (
    load_ue_config,
    generate_ue_profiles
)
from automated_test.ric_test_config_generator.generate_rictest_config import update_rictest_config
from automated_test.ric_test_config_generator.convert_cell_coordinates import process_cell_xy_coordinates
from automated_test.ric_test_controller.rictest_controller import (
    start_rictest_simulation,
    stop_rictest_simulation
)
from interoperability_test.o1_interface_test import (
    get_test_interfaces,
    test_o1_netconf_connection,
    test_o1_ves_connection
)
from automated_test.rApp_validation_framework.evaluate_rapp_performance import (
    parse_pass_criteria,
    read_db_config,
    compare_two_runs,
    connect_to_influxdb,
    fetch_and_calculate_avg
)
from automated_test.test_spec_handler.query_test_spec import query_test_spec
from automated_test.test_spec_handler.parse_test_spec import parse_test_spec
from automated_test.test_spec_handler.listen_test_spec import listen_test_spec_from_tme
def main():
    # Wait for the test specification notification first
    print("Waiting for new test specification...")
    test_spec_notification = listen_test_spec_from_tme()
    
    if test_spec_notification:  # Only proceed if test_spec_notification is not None
        print("Querying test specification...")
        time.sleep(10)
        test_spec = query_test_spec()
        print("Input test spec from test-management-exposure:")
        print(json.dumps(test_spec, indent=4)) 
        parse_test_spec()
        time.sleep(10)
        # Load cell configuration from file
        cell_data = load_cell_config()
        print("Input Cell Configuration:")
        print(json.dumps(cell_data, indent=4))  # Pretty-print the data
        time.sleep(10)
        # Load UE configuration from file
        ue_data = load_ue_config()
        print("Input UE Configuration:")
        print(json.dumps(ue_data, indent=4))  # Pretty-print the data
        time.sleep(10)
        pass_criteria = parse_pass_criteria()
        time.sleep(10)
        # Step 2: Generate cell profiles and coordinates
        # Generate cell profiles and positions based on the loaded cell configuration
        cell_profiles, positions = generate_cell_profiles(cell_data)
        # Generate UE profiles based on the loaded UE configuration
        ue_profiles = generate_ue_profiles(ue_data)

        # Step 3: Output cell profiles and coordinates to JSON files
        # Write the generated cell profiles to a JSON file (in RIC Test format)
        with open(os.path.join("automated_test", "ric_test_config_generator", "temp_json", "output_cell_config.json"), "w") as posfile:
            json.dump(cell_profiles, posfile, indent=4)
            
        with open(os.path.join("automated_test","ric_test_config_generator", "temp_json", "cell_positions.json"), "w") as posfile:
            json.dump({"cells": positions}, posfile, indent=4)
            
        with open(os.path.join("automated_test", "ric_test_config_generator", "temp_json", "output_ue_config.json"), "w") as posfile:
            json.dump(ue_profiles, posfile, indent=4)
        # Step 4: Calculate the total number of cells
        # Calculate the total number of cells based on the configuration data
        total_number_of_cells = calculate_total_number_of_cells(cell_data)

        # Set the output file path for storing the converted XY coordinates
        output_file = os.path.join("automated_test","ric_test_config_generator","temp_json", "converted_xy_coordinates.json")
        
        # Process the cell positions and convert them to relative coordinates
        # This step moves all XY positions to a relative position and generates output coordinates
        print("For cell deployment setting...")  
        reference_distance, output_string = process_cell_xy_coordinates(
            os.path.join("automated_test","ric_test_config_generator","temp_json", "cell_positions.json"), 
            output_file
        )

        # Print the reference distance and the output string for clarity
        print(f"Reference Distance: {reference_distance}")
        print(f"Output String: {output_string}")

        time.sleep(10)
        # Step 5: Update the RIC Test configuration file
        # Use the generated cell and UE profiles along with the total number of cells to update the RIC Test configuration
        update_rictest_config(
            cell_profiles, 
            ue_profiles, 
            total_number_of_cells, 
            'RIC_Test_v2.4.conf', 
            reference_distance, 
            output_string
        )
        print("Start first RIC Test simulation...")  
        # Start first RIC Test simulation
        simulation_response = start_rictest_simulation(config_filename="updated_RIC_Test_v2.4.conf", config_dir="config")
        
        if simulation_response:
            print(f"Simulation started, HTTP Status Code: {simulation_response}")
        else:
            print("Simulation failed to start.")
        time.sleep(10)
        need_test= get_test_interfaces()
        time.sleep(90)
        if not need_test:
            print("Skipping NETCONF and VES tests.")
            return

        # Step 2: Test NETCONF connection
        netconf_success = test_o1_netconf_connection()
        netconf_result = "Pass" if netconf_success else "Failed"

        # Step 3: Test VES connection
        target_source_id = "VIAVI-RIC-Test"
        ves_success = test_o1_ves_connection(target_source_id)
        ves_result = "Pass" if ves_success else "Failed"
        time.sleep(10)

        # Final output for both tests
        print(f"O1 Netconf: {netconf_result}")
        print(f"O1 VES: {ves_result}")
        
        # Stop the first simulation and fetch data
        stop_result = stop_rictest_simulation()
        print(stop_result)
        time.sleep(10)    
        # Fetch and calculate first run data
        db_config = read_db_config()


        if db_config:
            print("✅ Successfully loaded DB configuration.")
            client = connect_to_influxdb(db_config)
            
            if client:
                print("⏳ Fetching first simulation data...")
                fields = [target['targetName'] for target in pass_criteria]
                first_run_data = fetch_and_calculate_avg(client, db_config, fields, "-90m")

                # Now, start the second simulation (with rApp)
                simulation_response = start_rictest_simulation(config_filename="updated_RIC_Test_v2.4.conf", config_dir="config")
                
                if simulation_response:
                    print(f"Second simulation started, HTTP Status Code: {simulation_response}")
                else:
                    print("Second simulation failed to start.")
                
                print("⏳ Waiting for the second simulation (with rApp) to run for two minutes...")
                time.sleep(60)

                # Stop the second simulation and fetch data
                stop_result = stop_rictest_simulation()
                print(stop_result)

                # Fetch and calculate second run data
                second_run_data = fetch_and_calculate_avg(client, db_config, fields, "-90m")          # Compare the two runs
                compare_two_runs(first_run_data, second_run_data, pass_criteria)
            else:
                print("❌ Failed to connect to InfluxDB.")
        else:
            print("❌ Failed to load DB configuration.")
    else:
        print("❌ No test specification notification received. Exiting.")

if __name__ == "__main__":
    main()