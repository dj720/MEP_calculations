import pandas as pd
from io import BytesIO
import streamlit as st


# Function to convert DataFrame to Excel
def convert_df_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Pipe Data')
    writer._save()
    processed_data = output.getvalue()
    return processed_data


# Function to upload and load Excel data
def load_excel_data(uploaded_file):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(uploaded_file)

    # List of required columns
    required_columns = ['Material', 'Nominal diameter (mm)', 'Internal diameter (mm)', 'Length (m)', 'Pipe volume (m³)']

    # Check if all required columns exist in the uploaded file
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"The uploaded file is missing the following required columns: {', '.join(missing_columns)}")
        return

    # Drop rows with missing or NaN values in the required columns
    df = df.dropna(subset=required_columns)

    # Create a list of tuples with the cleaned data (for all required columns)
    pipe_entries = [
        (
            row['Material'],
            row['Nominal diameter (mm)'],
            row['Internal diameter (mm)'],
            row['Length (m)'],
            row['Pipe volume (m³)']
        )
        for _, row in df.iterrows()
    ]

    return pipe_entries


dict_primary_ventilated_stacks = {
    '75mm': 2.6,
    '100mm': 5.2,
    '150mm': 12.4
}

dict_secondary_ventilated_stacks = {
    '75mm with 50mm secondary vent': 3.4,
    '100mm with 50mm secondary vent': 7.3,
    '150mm with 75mm secondary vent': 18.3
}

# Define appliances with their DU (l/s) values
appliance_du = {
    "WC, 6L cistern (1.2 - 1.7 l/s)": 1.7,
    "Wash basin": 0.3,
    "Bath": 1.3,
    "Shower Tray (no plug)": 0.4,
    "Kitchen sink": 1.3,
    "Urinal (cistern flush) per person": 0.2,
    "Bidet": 0.3,
    "Dishwasher, domestic": 0.2,
    "Washing Machine < 6kg": 0.6,
    "Washing Machine < 12kg": 1.2
}


def select_stack_option(total_wastewater_flowrate, wc_present, vent_method):
    if vent_method == 'Primary':
        # First, check primary ventilated stack options
        for option, max_flow in dict_primary_ventilated_stacks.items():
            # Skip the '75mm' option if WC is present
            if wc_present and option == '75mm':
                continue
            # Return the first suitable option where the total flow rate is within the limit
            if total_wastewater_flowrate <= max_flow:
                return f"primary {option}"

    elif vent_method == 'Secondary':
        # If no primary stack option is suitable, check secondary ventilated stack options
        for option, max_flow in dict_secondary_ventilated_stacks.items():
            if wc_present and option == '75mm with 50mm secondary vent':
                continue
            if total_wastewater_flowrate <= max_flow:
                return f"primary {option}"

    # If no option is suitable, return a message indicating the flow rate is too high
    return "there is no suitable stack option as the flow rate exceeds maximum limits, consider multiple stacks."
