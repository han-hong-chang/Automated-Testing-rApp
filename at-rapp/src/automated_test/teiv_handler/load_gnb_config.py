import os
import json

def generate_payload_from_gnb_config(input_path: str, output_path: str):
    """
    Read gNB config JSON from input_path, generate payload structure,
    and write the output JSON to output_path.
    """

    # Load gNB configuration from input JSON file
    with open(input_path, "r", encoding="utf-8") as f:
        gNB_Config = json.load(f)

    # Initialize the 'entities' list with one dictionary containing all top-level components
    entities = [{
        "o-ran-smo-teiv-oam:ManagedElement": [
            {
                "id": "VIAVI-Rictest",
                "attributes": {
                    "status": "Assigned"
                }
            }
        ],
        "o-ran-smo-teiv-ran:ODUFunction": [],
        "o-ran-smo-teiv-ran:NRCellDU": [],
        "o-ran-smo-teiv-ran:NRSectorCarrier": []
    }]

    # Initialize the 'relationships' dictionary
    relationships = {
        "o-ran-smo-teiv-rel-oam-ran:MANAGEDELEMENT_MANAGES_ODUFUNCTION": [],
        "o-ran-smo-teiv-ran:ODUFUNCTION_PROVIDES_NRSECTORCARRIER": [],
        "o-ran-smo-teiv-ran:ODUFUNCTION_PROVIDES_NRCELLDU": []
    }

    index = 1

    # Process each gNB configuration group
    for group in gNB_Config["gNB_Config"]:
        for entry in group:
            odu_list = entry["gNB-DU-Function"]
            cell_list = entry["NR-Cell-DU"]
            sector_list = entry["NR-Sector-Carrier"]

            # Assume all three lists are of equal length
            for i in range(len(odu_list)):
                odu = odu_list[i]
                cell = cell_list[i]
                sector = sector_list[i]

                # Add 'status' and convert attribute values to strings if necessary
                for attr in [odu, cell, sector]:
                    attr["attributes"]["status"] = "Assigned"
                    attr["attributes"] = {
                        k: str(v) if not isinstance(v, (list, dict)) else v
                        for k, v in attr["attributes"].items()
                    }

                # Append to entities under the correct keys
                entities[0]["o-ran-smo-teiv-ran:ODUFunction"].append(odu)
                entities[0]["o-ran-smo-teiv-ran:NRCellDU"].append(cell)
                entities[0]["o-ran-smo-teiv-ran:NRSectorCarrier"].append(sector)

                # Build relationship entries
                relationships["o-ran-smo-teiv-rel-oam-ran:MANAGEDELEMENT_MANAGES_ODUFUNCTION"].append({
                    "id": str(index),
                    "aSide": "VIAVI-Rictest",
                    "bSide": str(index),
                    "sourceIds": ["VIAVI-Rictest", str(index)]
                })
                relationships["o-ran-smo-teiv-ran:ODUFUNCTION_PROVIDES_NRCELLDU"].append({
                    "id": str(index),
                    "aSide": str(index),
                    "bSide": str(index),
                    "sourceIds": [str(index), str(index)]
                })
                relationships["o-ran-smo-teiv-ran:ODUFUNCTION_PROVIDES_NRSECTORCARRIER"].append({
                    "id": str(index),
                    "aSide": str(index),
                    "bSide": str(index),
                    "sourceIds": [str(index), str(index)]
                })

                index += 1

    # Compose final payload structure
    payload = {
        "entities": entities,
        "relationships": [relationships]
    }

    # Write the output payload to the specified output path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"✅ Payload successfully written to:\n➡ {output_path}")