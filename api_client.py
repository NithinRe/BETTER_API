# api_client.py

import requests
import json
import time

# Note: API_KEY and BASE_URL will be passed to functions or imported from config
# For this structure, we'll assume they are passed as arguments.

# --- Helper Function to Make API Requests ---
def _make_request(method, endpoint, data=None, params=None, api_key=None, base_url=None):
    """
    A helper function to make requests to the BETTER API.
    """
    if not api_key or not base_url:
        return {"error": "API_KEY and BASE_URL must be provided."}

    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, params=params)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=data, params=params)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, params=params)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        if response.content:
            return response.json()
        return None # For DELETE or other responses with no content

    except requests.exceptions.HTTPError as http_err:
        error_content = None
        try:
            error_content = response.json()
        except json.JSONDecodeError:
            error_content = response.text
        return {"error": "HTTPError", "status_code": response.status_code, "message": str(http_err), "details": error_content}
    except requests.exceptions.RequestException as req_err:
        return {"error": "RequestException", "message": str(req_err)}
    except json.JSONDecodeError as json_err:
        return {"error": "JSONDecodeError", "message": str(json_err), "raw_response": response.text if 'response' in locals() else "N/A"}


# --- Portfolio Management ---
def create_portfolio(portfolio_name, api_key, base_url):
    """Creates a new portfolio."""
    endpoint = "/portfolios/"
    payload = {"name": portfolio_name}
    return _make_request("POST", endpoint, data=payload, api_key=api_key, base_url=base_url)

# --- Building Management ---
def create_building(building_payload, api_key, base_url):
    """
    Creates a new building.
    building_payload should include 'portfolio' (ID), 'name', 'space_type', 
    'floor_area', 'location', and optionally 'utility_bills'.
    """
    endpoint = "/buildings/"
    return _make_request("POST", endpoint, data=building_payload, api_key=api_key, base_url=base_url)

# --- Utility Bill Management ---
def list_utility_bills(building_id, api_key, base_url):
    """Lists all utility bills for a given building."""
    endpoint = f"/buildings/{building_id}/utility_bills/"
    return _make_request("GET", endpoint, api_key=api_key, base_url=base_url)

def get_utility_bill_details(building_id, bill_id, api_key, base_url):
    """Retrieves details for a specific utility bill."""
    endpoint = f"/buildings/{building_id}/utility_bills/{bill_id}/"
    return _make_request("GET", endpoint, api_key=api_key, base_url=base_url)

def add_new_bills_to_building(building_id, new_bills_payload, api_key, base_url):
    """
    Adds one or more new utility bills to an existing building.
    Assumes POST to /buildings/{building_id}/utility_bills/ with a list of bills.
    """
    endpoint = f"/buildings/{building_id}/utility_bills/"
    # new_bills_payload is expected to be a list of bill objects
    return _make_request("POST", endpoint, data=new_bills_payload, api_key=api_key, base_url=base_url)

def edit_utility_bill(building_id, bill_id, bill_update_payload, api_key, base_url):
    """Edits/updates fields of a specific utility bill (PATCH)."""
    endpoint = f"/buildings/{building_id}/utility_bills/{bill_id}/"
    return _make_request("PATCH", endpoint, data=bill_update_payload, api_key=api_key, base_url=base_url)

def delete_utility_bill(building_id, bill_id, api_key, base_url):
    """Deletes a specific utility bill."""
    endpoint = f"/buildings/{building_id}/utility_bills/{bill_id}/"
    return _make_request("DELETE", endpoint, api_key=api_key, base_url=base_url)


# --- Building Analytics Functions ---
def run_building_analysis(building_id, savings_target, min_r_squared, api_key, base_url):
    """
    Triggers a new analytics run for a specified building.
    Returns the initial response from the API, including the analytics ID and generation status.
    """
    endpoint = f"/buildings/{building_id}/analytics/"
    payload = {
        "savings_target": savings_target,
        "min_model_r_squared": min_r_squared,
        "benchmark_data_type": "DEFAULT" 
    }
    return _make_request("POST", endpoint, data=payload, api_key=api_key, base_url=base_url)

def get_building_analysis_details(building_id, building_analytics_id, api_key, base_url, html_format=False, units_ip=False):
    """
    Retrieves the details and status of a specific building analytics run.
    This is used for polling and getting final results.
    Can request HTML format and IP units.
    """
    endpoint = f"/buildings/{building_id}/analytics/{building_analytics_id}/"
    params = {}
    if html_format:
        params["format"] = "html"
        if units_ip:
            params["units"] = "IP"
    
    # If HTML format is requested, the response might not be JSON
    # _make_request currently tries to parse JSON. This might need adjustment if HTML is directly returned.
    # For now, assuming JSON response unless HTML format is specifically handled for its raw text.
    if html_format:
         # This part would need _make_request to be adapted or a new helper for raw content
        print(f"Note: HTML format requested for {endpoint}. Raw response handling might be needed if not JSON.")

    return _make_request("GET", endpoint, params=params, api_key=api_key, base_url=base_url)


def poll_for_building_analysis_completion(building_id, building_analytics_id, api_key, base_url, poll_interval_seconds=10, max_attempts=30):
    """
    Polls the building analytics detail endpoint until the analysis is COMPLETE or FAILED.
    Returns the final analytics data object.
    """
    print(f"Polling for completion of analytics ID: {building_analytics_id} for building ID: {building_id}...")
    for attempt in range(max_attempts):
        details = get_building_analysis_details(building_id, building_analytics_id, api_key, base_url)
        
        if details and "error" not in details:
            generation_result = details.get("generation_result")
            print(f"  Attempt {attempt + 1}/{max_attempts}: Status = {generation_result}")
            if generation_result == "COMPLETE":
                print("Analysis COMPLETE.")
                return details
            elif generation_result == "FAILED":
                print(f"Analysis FAILED. Message: {details.get('generation_message', 'No message provided.')}")
                return details
            elif generation_result == "IN_PROGRESS":
                time.sleep(poll_interval_seconds)
            else:
                print(f"Unexpected generation_result status: {generation_result}. Details: {details}")
                return details
        else:
            error_message = details.get('message', 'Unknown error') if details else 'Initial call failed, no details.'
            print(f"  Attempt {attempt + 1}/{max_attempts}: Error fetching analysis details: {error_message}")
            # If there's a persistent API error, might not be useful to keep polling
            # For simplicity, we continue polling, but in a real app, might break on certain errors.
            time.sleep(poll_interval_seconds)

    print(f"Polling timed out after {max_attempts} attempts.")
    # Return last fetched details, even on timeout, for inspection
    return details if 'details' in locals() else {"error": "Polling failed to get details."}
