import json
import math
from functools import reduce
import os
def load_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return None

def save_json(data, file_name):
    output_dir = "temp_json"
    os.makedirs(output_dir, exist_ok=True)  # 若目錄不存在則建立
    file_path = os.path.join(output_dir, file_name)
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to '{file_path}'.")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
def convert_latlon_to_xy(input_file, output_file):
    # Set the reference point's latitude and longitude
    lat0 = 25.0330  # Latitude of the reference point
    lon0 = 121.5654  # Longitude of the reference point

    # The distance per degree of latitude/longitude on Earth (in kilometers), converted to meters
    distance_per_degree = 111.32 * 1000  # Convert to meters

    def calculate_offset(lat, lon, lat0, lon0, distance_per_degree):
        # Calculate the horizontal (X-axis) offset
        X = (lon - lon0) * distance_per_degree
        # Calculate the vertical (Y-axis) offset
        Y = (lat - lat0) * distance_per_degree
        return X, Y

    # Load the input JSON file
    data = load_json(input_file)

    # Convert each cell's latitude and longitude to x, y coordinates
    converted_cells = []
    if data:
        for cell in data["cells"]:
            lat = cell["lat"]
            lon = cell["lon"]
            X, Y = calculate_offset(lat, lon, lat0, lon0, distance_per_degree)
            converted_cells.append({
                "name": cell["name"],
                "x": round(X),  # Round to nearest integer
                "y": round(Y)   # Round to nearest integer
            })

        # Prepare the new JSON structure
        output_data = {
            "cells": converted_cells
        }

        # Save the converted data to the output JSON file
        save_json(output_data, output_file)
    else:
        print("Failed to read the input JSON file.")

def load_and_ensure_xy_coordinates(input_file, output_file):
    data = load_json(input_file)
    
    # Check if the data contains lat, lon or x, y
    if "lat" in data["cells"][0] and "lon" in data["cells"][0]:
        print("Converting lat/lon to x/y...")
        convert_latlon_to_xy(input_file, output_file)
        data = load_json(output_file)  # Reload the data after conversion
    else:
        print("Using existing x/y coordinates.")
    
    # Regardless of whether it was converted or not, save the data to output
    save_json(data, output_file)
    
    return data

def check_s1_coordinates(data):
    if not data or "cells" not in data:
        print("Error: Invalid data format.")
        exit(1)
    
    for cell in data["cells"]:
        if cell.get("name") == "s1":
            x, y = cell.get("x", None), cell.get("y", None)
            if x != 0 or y != 0:
                print("Error: s1 must be at coordinates (0,0).")
                exit(1)
            return True
    
    print("Error: s1 not found in data.")
    exit(1)

def check_duplicate_coordinates(data):
    seen = set()
    cell_names = set()  # To track if cell names are duplicated
    
    for cell in data["cells"]:
        coord = (cell["x"], cell["y"])
        name = cell.get("name")
        
        if coord in seen:
            print(f"Error: Duplicate coordinates found at {coord}.")
            exit(1)
        seen.add(coord)
        
        # Check for duplicate names
        if name in cell_names:
            print(f"Error: Duplicate cell name found: {name}.")
            exit(1)
        cell_names.add(name)

def is_all_in_fourth_quadrant(data):
    if not data or "cells" not in data:
        return False
    return all(cell["x"] >= 0 and cell["y"] <= 0 for cell in data["cells"])

def process_coordinates(data):
    if not data or "cells" not in data:
        return None
    
    check_s1_coordinates(data)
    check_duplicate_coordinates(data)
    
    x_values = [cell["x"] for cell in data["cells"]]
    y_values = [cell["y"] for cell in data["cells"]]
    min_x = min(x_values, default=0)
    max_y = max(y_values, default=0)
    
    if is_all_in_fourth_quadrant(data):
        return data
    
    if min_x < 0:
        x_offset = abs(min_x)
        for cell in data["cells"]:
            cell["x"] += x_offset
    
    if max_y > 0:
        for cell in data["cells"]:
            cell["y"] -= max_y
    
    return data

def get_all_values_for_gcd(data):
    if not data or "cells" not in data:
        return []
    return [abs(cell["x"]) for cell in data["cells"]] + [abs(cell["y"]) for cell in data["cells"]]

def gcd_multiple(numbers):
    if not numbers:
        return 1  # Avoid errors from empty list
    return reduce(math.gcd, numbers)

def calculate_reference_distance(data):
    s1 = next((cell for cell in data["cells"] if cell["name"] == "s1"), None)
    s2 = next((cell for cell in data["cells"] if cell["name"] == "s2"), None)
    
    if not s1 or not s2:
        print("Error: s1 or s2 not found in data.")
        exit(1)
    
    distance = math.sqrt((s2["x"] - s1["x"]) ** 2 + (s2["y"] - s1["y"]) ** 2)
    rounded_distance = round(distance)  # Round the distance
    
    if rounded_distance < 100:
        print("Error: Reference distance must be >= 100 (RIC Test limitation).")
        exit(1)
    
    return rounded_distance

def scale_coordinates_by_gcd(data, gcd):
    # New function that scales coordinates by dividing by GCD and then scaling
    for cell in data["cells"]:
        cell["x"] = (cell["x"] // gcd) * 4  # Divide X by GCD and multiply by 4
        cell["y"] = (cell["y"] // gcd) * 2  # Divide Y by GCD and multiply by 2
    return data

def generate_xy_string(adjusted_coordinates):
    cells = adjusted_coordinates.get("cells", [])
    
    # Find the minimum and maximum Y values to ensure all Y-axis have corresponding rows
    min_y = min(cell["y"] for cell in cells)
    max_y = max(cell["y"] for cell in cells)
    
    # y_offset ensures there are no negative indices for Y-axis
    y_offset = -min_y if min_y < 0 else 0
    max_y_adjusted = max_y + y_offset
    
    # Initialize rows for the Y-axis
    lines = {y: "" for y in range(max_y_adjusted + 1)}
    
    # Place each cell into the corresponding Y-axis row
    for cell in sorted(cells, key=lambda c: (-c["y"], c["x"])):  # Sort by Y desc, then X asc
        y_value = cell["y"] + y_offset
        x_value = cell["x"]
        name = cell["name"]
        
        # Ensure the row is long enough and place the name at the correct position
        line = lines[y_value]
        if len(line) < x_value:
            line = line.ljust(x_value)
        
        # Insert the name
        line = line[:x_value] + name + line[x_value + len(name):]
        lines[y_value] = line
    
    # Convert to string and arrange the Y-axis from top to bottom
    # Removed the wrapping quotes, just output the final formatted string directly
    output_string = "\\n".join(lines[y] for y in range(max_y_adjusted, -1, -1))
    
    return output_string


def process_cell_xy_coordinates(input_file, output_file):
    """
    Processes the cell coordinates, ensuring all cells are within the fourth quadrant, 
    calculates the reference distance, scales the coordinates, and returns the 
    final processed data along with the reference distance and the output string.
    """
    converted_file = "converted_xy_coordinates.json"
    processed_file = "process_xy_coordinates_to_fourth_quadrant.json"
    scaled_file = "scaled_coordinates.json"
    # Step 1: Load and convert lat/lon if necessary
    data = load_and_ensure_xy_coordinates(input_file, converted_file)
    if not data:
        return None, None

    # Step 2: Shift coordinates to 4th quadrant
    processed_data = process_coordinates(data)
    if processed_data:
        save_json(processed_data, processed_file)

    # Step 3: Calculate reference distance (between s1 and s2)
    reference_distance = calculate_reference_distance(processed_data)

    # Step 4: Scale using real GCD
    all_values = get_all_values_for_gcd(processed_data)
    gcd_value = gcd_multiple(all_values)
    scaled_data = scale_coordinates_by_gcd(processed_data, gcd_value)
    save_json(scaled_data,scaled_file)

    # Step 5: Generate coordinate string
    output_string = generate_xy_string(scaled_data)

    return reference_distance, output_string

