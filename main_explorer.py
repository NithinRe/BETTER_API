# main_explorer.py

import time
import config # To get API_KEY, BASE_URL, USER_LOGIN, CURRENT_UTC_TIME
import api_client # To use the API functions

# --- Helper function to display analysis results ---
def display_analysis_summary(building_id, analysis_results):
    """
    Parses and displays a summary of the building analysis results.
    """
    print(f"\n--- Analysis Summary for Building ID: {building_id} ---")

    if not analysis_results or "generation_result" not in analysis_results:
        print("Analysis data is incomplete or unavailable.")
        if analysis_results and "error" in analysis_results:
             print(f"  Error: {analysis_results.get('message', 'Unknown error')}")
        return
        
    generation_result = analysis_results.get("generation_result")
    if generation_result != "COMPLETE":
        print(f"Analysis Status: {generation_result}")
        print(f"  Message: {analysis_results.get('generation_message', 'N/A')}")
        return

    print(f"  Analysis Generation Date: {analysis_results.get('generation_date', 'N/A')}")
    print(f"  Building Location: {analysis_results.get('building_location', 'N/A')}")
    print(f"  Building Space Type: {analysis_results.get('building_space_type', 'N/A')}")
    print(f"  Gross Floor Area: {analysis_results.get('building_gross_floor_area', 'N/A')} sqm")
    print(f"  Savings Target Used: {analysis_results.get('savings_target', 'N/A')}")
    print(f"  Min R-Squared Used: {analysis_results.get('min_model_r_squared', 'N/A')}")

    assessment = analysis_results.get("assessment", {})
    assessment_results_data = assessment.get("assessment_results", {})
    inverse_model = analysis_results.get("inverse_model", {})

    print("\n  Key Assessment Results:")
    ee_measures = assessment.get('ee_measures')
    if ee_measures: # Check if it's not None and not empty
        print(f"    Recommended EE Measures: {', '.join(ee_measures)}")
    else:
        print("    Recommended EE Measures: N/A or not provided")
        
    print(f"    Combined Energy Savings: {assessment_results_data.get('energy_savings_combined', 'N/A')} kWh ({assessment_results_data.get('energy_savings_pct_combined', 'N/A')}%)")
    print(f"    Combined Cost Savings: {assessment_results_data.get('cost_savings_combined', 'N/A')} Currency ({assessment_results_data.get('cost_savings_pct_combined', 'N/A')}%)")
    print(f"    Combined GHG Reductions: {assessment_results_data.get('ghg_savings_combined', 'N/A')} kg ({assessment_results_data.get('ghg_reductions_pct_combined', 'N/A')}%)")

    print("\n  Model Fit:")
    if "ELECTRICITY" in inverse_model and inverse_model["ELECTRICITY"]:
        print(f"    Electricity Model R-squared: {inverse_model['ELECTRICITY'].get('r2', 'N/A')}")
        print(f"    Electricity Model CVRMSE: {inverse_model['ELECTRICITY'].get('cvrmse', 'N/A')}")
    if "FOSSIL_FUEL" in inverse_model and inverse_model["FOSSIL_FUEL"]:
         print(f"    Fossil Fuel Model R-squared: {inverse_model['FOSSIL_FUEL'].get('r2', 'N/A')}")
         print(f"    Fossil Fuel Model CVRMSE: {inverse_model['FOSSIL_FUEL'].get('cvrmse', 'N/A')}")
    print("----------------------------------------------------")

# --- Main Interactive Logic ---
def main():
    print("Welcome to the BETTER API Explorer!")
    print(f"Current User: {config.USER_LOGIN}")
    print(f"Current Time (UTC): {config.CURRENT_UTC_TIME}")

    api_key = config.API_KEY
    base_url = config.BASE_URL

    if api_key == "YOUR_ACTUAL_API_KEY_HERE" or base_url == "YOUR_ACTUAL_BETTER_API_BASE_URL_HERE":
        print("\nWARNING: Please update API_KEY and BASE_URL in config.py before running.")
        return

    building_ids_input = input("Enter Building ID(s) to analyze (comma-separated, e.g., 101,102): ")
    try:
        building_ids_to_analyze = [int(bid.strip()) for bid in building_ids_input.split(',')]
    except ValueError:
        print("Invalid Building ID format. Please enter comma-separated numbers.")
        return

    if not building_ids_to_analyze:
        print("No building IDs provided. Exiting.")
        return

    print("\nAnalysis Parameters:")
    SAVINGS_TARGET_OPTIONS = ["NOMINAL", "CONSERVATIVE", "AGGRESSIVE"]
    print("Available Savings Targets:")
    for idx, target in enumerate(SAVINGS_TARGET_OPTIONS):
        print(f"  {idx+1}. {target}")
    
    target_choice_idx = -1
    while not (0 <= target_choice_idx < len(SAVINGS_TARGET_OPTIONS)):
        try:
            raw_choice = input(f"Choose a savings target number (1-{len(SAVINGS_TARGET_OPTIONS)}): ")
            target_choice_idx = int(raw_choice) - 1
            if not (0 <= target_choice_idx < len(SAVINGS_TARGET_OPTIONS)):
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    savings_target_param = SAVINGS_TARGET_OPTIONS[target_choice_idx]
    
    min_r_squared_param = -1.0
    while not (0.0 <= min_r_squared_param <= 1.0):
        try:
            min_r_squared_param = float(input("Enter minimum R-squared for model validation (0.0 to 1.0, e.g., 0.6): "))
            if not (0.0 <= min_r_squared_param <= 1.0):
                print("Value must be between 0.0 and 1.0.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    for building_id in building_ids_to_analyze:
        print(f"\nProcessing Building ID: {building_id}")
        print(f"  Using Savings Target: '{savings_target_param}', Min R-Squared: {min_r_squared_param}")

        print(f"  Triggering analysis for building {building_id}...")
        analysis_trigger_response = api_client.run_building_analysis(
            building_id, savings_target_param, min_r_squared_param, api_key, base_url
        )

        if not analysis_trigger_response or "id" not in analysis_trigger_response:
            print(f"  Failed to trigger analysis for building {building_id}. Response: {analysis_trigger_response}")
            continue
        
        building_analytics_id = analysis_trigger_response["id"]
        print(f"  Analysis triggered. Analytics ID: {building_analytics_id}, Initial Status: {analysis_trigger_response.get('generation_result')}")

        if analysis_trigger_response.get('generation_result') == "FAILED":
            print(f"  Initial analysis trigger failed. Message: {analysis_trigger_response.get('generation_message', 'N/A')}")
            display_analysis_summary(building_id, analysis_trigger_response) # Display the failure message
            continue # Move to next building if initial trigger fails

        final_analysis_results = api_client.poll_for_building_analysis_completion(
            building_id, building_analytics_id, api_key, base_url
        )
        
        display_analysis_summary(building_id, final_analysis_results)

    print("\n--- BETTER API Explorer Session Ended ---")

if __name__ == "__main__":
    main()