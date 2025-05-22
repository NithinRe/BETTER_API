# data_generator.py

import datetime
import random
import config  # To get API_KEY, BASE_URL, USER_LOGIN, CURRENT_UTC_TIME
import api_client # To use the API functions

# --- Helper function to generate sample utility bills ---
def generate_sample_bills(year, fuel_types, completeness="full", building_floor_area_sqm=1000):
    """
    Generates a list of sample utility bill objects.
    """
    bills = []
    months_to_generate = list(range(1, 13))
    if completeness == "missing":
        num_missing = random.randint(2, 4)
        for _ in range(num_missing):
            if months_to_generate: # ensure list is not empty
                months_to_generate.pop(random.randrange(len(months_to_generate)))

    for fuel in fuel_types:
        for month in months_to_generate:
            start_date = datetime.date(year, month, 1)
            if month == 12:
                end_date = datetime.date(year, month, 31)
            else:
                end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

            if fuel == "ELECTRIC_GRID":
                consumption = random.randint(50, 150) * (building_floor_area_sqm / 100.0)
                unit = "KWH"
                cost = consumption * random.uniform(0.08, 0.25)
            elif fuel == "NATURAL_GAS":
                consumption = random.randint(2, 10) * (building_floor_area_sqm / 100.0)
                unit = "THERMS"
                cost = consumption * random.uniform(0.80, 3.00)
            else:
                continue

            bills.append({
                "fuel_type": fuel,
                "bill_start_date": start_date.strftime("%Y-%m-%d"),
                "bill_end_date": end_date.strftime("%Y-%m-%d"),
                "consumption": round(consumption, 2),
                "unit": unit,
                "cost": round(cost, 2)
            })
    return bills

# --- Main Interactive Logic ---
def main():
    print("Welcome to the BETTER API Data Generator Wizard!")
    print(f"Current User: {config.USER_LOGIN}")
    print(f"Current Time (UTC): {config.CURRENT_UTC_TIME}")

    api_key = config.API_KEY
    base_url = config.BASE_URL

    if api_key == "YOUR_ACTUAL_API_KEY_HERE" or base_url == "YOUR_ACTUAL_BETTER_API_BASE_URL_HERE":
        print("\nWARNING: Please update API_KEY and BASE_URL in config.py before running.")
        return

    portfolio_id = None
    create_new_portfolio_choice = input("Do you want to create a new portfolio? (y/n): ").lower()
    if create_new_portfolio_choice == 'y':
        portfolio_name = input("Enter a name for the new portfolio: ")
        print(f"Creating portfolio '{portfolio_name}'...")
        portfolio_response = api_client.create_portfolio(portfolio_name, api_key, base_url)
        
        if portfolio_response and "id" in portfolio_response:
            portfolio_id = portfolio_response["id"]
            print(f"Portfolio '{portfolio_name}' created successfully with ID: {portfolio_id}")
        else:
            print(f"Failed to create portfolio. Response: {portfolio_response}")
            return
    else:
        try:
            portfolio_id_input = input("Enter the ID of an existing portfolio to use: ")
            portfolio_id = int(portfolio_id_input)
        except ValueError:
            print("Invalid portfolio ID format. Must be an integer.")
            return
    
    if not portfolio_id:
        print("No portfolio selected or created. Exiting.")
        return

    print(f"\nUsing Portfolio ID: {portfolio_id}")

    try:
        num_buildings = int(input("How many buildings do you want to add to this portfolio?: "))
        if num_buildings <= 0:
            print("Number of buildings must be positive. Exiting.")
            return
    except ValueError:
        print("Invalid number of buildings. Must be an integer.")
        return

    VALID_SPACE_TYPES = [
        "OFFICE", "HOTEL", "K12", "MULTIFAMILY_HOUSING", "WORSHIP_FACILITY", 
        "HOSPITAL", "MUSEUM", "BANK_BRANCH", "COURTHOUSE", "DATA_CENTER", 
        "DISTRIBUTION_CENTER", "FASTFOOD_RESTAURANT", "FINANCIAL_OFFICE", 
        "FIRE_STATION", "NON_REFRIGERATED_WAREHOUSE", "POLICE_STATION", 
        "REFRIGERATED_WAREHOUSE", "RETAIL_STORE", "SELF_STORAGE_FACILITY", 
        "SENIOR_CARE_COMMUNITY", "SUPERMARKET_GROCERY", "RESTAURANT", 
        "PUBLIC_LIBRARY", "OTHER"
    ]
    created_building_ids = []

    for i in range(num_buildings):
        print(f"\n--- Adding Building {i+1}/{num_buildings} ---")
        building_name = input(f"Enter name for Building {i+1} (e.g., 'Main Office Complex {i+1}'): ")
        
        print("Available Space Types:")
        for idx, space_type in enumerate(VALID_SPACE_TYPES):
            print(f"  {idx+1}. {space_type}")
        
        space_type_choice_idx = -1
        while not (0 <= space_type_choice_idx < len(VALID_SPACE_TYPES)):
            try:
                raw_choice = input(f"Choose a space type number (1-{len(VALID_SPACE_TYPES)}): ")
                space_type_choice_idx = int(raw_choice) - 1
                if not (0 <= space_type_choice_idx < len(VALID_SPACE_TYPES)):
                    print("Invalid choice. Please select a number from the list.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        building_space_type = VALID_SPACE_TYPES[space_type_choice_idx]

        try:
            building_floor_area = float(input("Enter gross floor area (in square meters, e.g., 5000): "))
            if building_floor_area <=0:
                 print("Floor area must be positive.")
                 continue # Skip to next building
        except ValueError:
            print("Invalid floor area. Must be a number.")
            continue # Skip to next building

        building_location = input("Enter building location (e.g., 'San Francisco, CA'): ")

        building_utility_bills = []
        generate_bills_choice = input("Generate sample utility bills for this building? (y/n): ").lower()
        if generate_bills_choice == 'y':
            try:
                bill_year = int(input("Enter year for utility bills (YYYY, e.g., 2023): "))
            except ValueError:
                print("Invalid year. Using default 2023.")
                bill_year = 2023
            
            fuel_choices = []
            if input("Include Electricity (ELECTRIC_GRID) bills? (y/n): ").lower() == 'y':
                fuel_choices.append("ELECTRIC_GRID")
            if input("Include Natural Gas (NATURAL_GAS) bills? (y/n): ").lower() == 'y':
                fuel_choices.append("NATURAL_GAS")
            
            bill_completeness_choice = input("Generate 'full' 12 months of data, or with 'missing' months? (full/missing): ").lower()
            bill_completeness = "missing" if bill_completeness_choice == "missing" else "full"
            
            building_utility_bills = generate_sample_bills(bill_year, fuel_choices, bill_completeness, building_floor_area)
            print(f"Generated {len(building_utility_bills)} bill records.")

        building_payload = {
            "portfolio": portfolio_id,
            "name": building_name,
            "space_type": building_space_type,
            "floor_area": building_floor_area,
            "location": building_location,
            "utility_bills": building_utility_bills
        }

        print(f"Creating building '{building_name}'...")
        building_response = api_client.create_building(building_payload, api_key, base_url)

        if building_response and "id" in building_response:
            building_id = building_response["id"]
            created_building_ids.append(building_id)
            print(f"Building '{building_name}' created successfully with ID: {building_id} and associated with portfolio {portfolio_id}.")
        else:
            print(f"Failed to create building '{building_name}'. Response: {building_response}")

    print("\n--- Data Generation Summary ---")
    print(f"Portfolio ID used/created: {portfolio_id}")
    if created_building_ids:
        print(f"Building IDs created in this session: {', '.join(map(str, created_building_ids))}")
        print("You can use these IDs in main_explorer.py.")
    else:
        print("No new buildings were created in this session.")
    
    print("\nData generator wizard finished.")

if __name__ == "__main__":
    main()