import streamlit as st
from common import setup_page
import pandas as pd
import math
from pyfluids import Fluid, FluidsList, Input

from processing.heating_processing import (get_glycol_water_properties,
                                                  calculate_reynolds_number,
                                                  calculate_darcy_friction_factor,
                                                  calculate_pressure_drop_per_meter,
                                                  convert_df_to_excel)

setup_page('Heating', 'david.naylor@wsp.com')

def load_excel_data(uploaded_file):
    """Function to upload and load Excel data into session state"""
    # Read the Excel file into a DataFrame
    df = pd.read_excel(uploaded_file)

    # List of required columns
    required_columns = ["Material", "Nominal diameter (mm)", "Internal diameter (mm)", "Velocity (m/s)",
                        "Pressure drop (Pa/m)"]

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
            row['Velocity (m/s)'],
            row["Pressure drop (Pa/m)"]
        )
        for _, row in df.iterrows()
    ]

    return pipe_entries

def check_existing_file():
    # give the option to reload an excel file into the doc
    existing_file = st.checkbox('Reload existing excel file')
    if existing_file:
        # File upload section to load an existing Excel file
        uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"], key='uploaded_file')
        if uploaded_file is not None:
            pipe_entries = load_excel_data(uploaded_file)

            # Update the session state with all column values
            st.session_state['pipe_entries'] = pipe_entries
            st.toast('Excel data loaded successfully!')

def add_pipe_entry(df_pipes):
    """Function to add a new pipe entry to session state"""
    st.subheader('Add new entry')

    # Inputs
    pipe_material = st.selectbox('Pipe material', df_pipes['Material'].unique())

    # Filter the row based on the selected material
    eq_roughness_row = df_pipes[df_pipes['Material'] == pipe_material]
    if not eq_roughness_row.empty:
        eq_roughness_mm = eq_roughness_row['Equivalent roughness'].values[0]  # m
        st.write(f"Equivalent roughness is {eq_roughness_mm} mm")
    else:
        st.warning("No roughness data found for the selected pipe material.")
        eq_roughness_mm = 0

    nominal_diameters = df_pipes[df_pipes['Material'] == pipe_material]['Nominal diameter '].unique()
    nom_diameter_mm = st.selectbox('Nominal diameter', nominal_diameters)
    int_diameter_row = df_pipes[
        (df_pipes['Material'] == pipe_material) & (df_pipes['Nominal diameter '] == nom_diameter_mm)]

    # Extract the internal diameter from the row
    if not int_diameter_row.empty:
        int_diameter_mm = int_diameter_row['Internal diameter'].values[0]  # Extract the value
        st.write(f"Internal diameter: {int_diameter_mm} mm")
    else:
        st.write("Internal diameter not found.")
        int_diameter_mm = 0

    flow_rate = st.number_input('Water flow rate (L/s)', min_value=0.1, value=0.5)  # Flow rate in liters per second

    # Temperature input (in Celsius) with a slider
    temperature = st.slider('Water temperature (°C)', min_value=1, max_value=100, value=50)
    pressure = 101325  # Atmospheric pressure in Pa

    use_glycol = st.checkbox('Include glycol?')
    if use_glycol:
        # Input for glycol percentage
        glycol_percentage = st.slider("Glycol percentage", min_value=0, max_value=60,
                                      value=30) / 100  # Convert to fraction

        # Get glycol-water mixture properties
        fluid_density, fluid_viscosity = get_glycol_water_properties(glycol_percentage, temperature, pressure)
    else:
        # Create the fluid instance based on the selected fluid using PyFluids
        fluid = Fluid(FluidsList.Water)
        # Update the fluid's state based on the input pressure and temperature
        fluid.update(Input.temperature(temperature), Input.pressure(pressure))
        fluid_density = fluid.density  # kg/m³
        fluid_viscosity = fluid.dynamic_viscosity  # Pa.s

    # Convert flow rate to m³/s and internal diameter to meters
    flow_rate_m3s = flow_rate / 1000  # L/s to m³/s
    
    int_diameter_m = int_diameter_mm / 1000  # mm to meters

    # Calculate pipe area and velocity
    pipe_area = math.pi * (int_diameter_m / 2) ** 2  # m2
    velocity = flow_rate_m3s / pipe_area  # m/s

    # Calculate Reynolds number using Fluids library
    reynolds_number = calculate_reynolds_number(velocity, int_diameter_m, fluid_density, fluid_viscosity)
    if reynolds_number <= 2000:
        st.warning('Reynolds number is less than 2000')
        friction_factor_value = 64 / reynolds_number
    else:
        friction_factor_value = calculate_darcy_friction_factor(reynolds_number, eq_roughness_mm, int_diameter_mm)

    pressure_drop_per_meter = calculate_pressure_drop_per_meter(friction_factor_value, fluid_density, velocity,
                                                                int_diameter_m)
    velocity_pressure = 0.5 * fluid_density * velocity ** 2

    st.success(f'''
                - Fluid velocity is {velocity:.2f} m/s
                - Pressure drop is {pressure_drop_per_meter:.2f} Pa/m
                - Velocity pressure is {velocity_pressure:.2f} Pa''')

    with st.expander('Advanced properties'):
        st.markdown(f'''
                - Reynolds number: {reynolds_number:.2f}
                - Darcy friction factor: {friction_factor_value:.4f}
                - Density: {fluid_density:.2f} kg/m³
                - Viscosity: {fluid_viscosity:.6f} Pa.s''')

    # Add the diameter and length to session state
    if st.button('Add pipe'):
        st.session_state['pipe_entries'].append(
            (pipe_material, nom_diameter_mm, int_diameter_mm, round(velocity, 3), round(pressure_drop_per_meter, 1)))
        st.toast(f'Added {pipe_material}, {nom_diameter_mm} mm, {velocity:.2f} m/s, {pressure_drop_per_meter:.2f} Pa/m')
        st.rerun()

# Initialize session state for pipe entries if not already
if 'pipe_entries' not in st.session_state:
    st.session_state['pipe_entries'] = []

# Load data from excel file into df
pipe_data = 'data/Pipe dimension data.xlsx'
xls_pipes = pd.ExcelFile(pipe_data)
df_pipes = xls_pipes.parse('Formatted data')

check_existing_file()

# Show the form to add pipes
add_pipe_entry(df_pipes)

# Display the list of pipes that have been added in a table (from both manual input and uploaded file)
if len(st.session_state['pipe_entries']) > 0:
    st.subheader("Pipe Details")

    # Create a DataFrame from session state data
    pipe_data = []
    for pipe_material, nom_diameter_mm, int_diameter_mm, velocity, pressure_drop_per_meter in st.session_state[
        'pipe_entries']:
        pipe_data.append([pipe_material, nom_diameter_mm, int_diameter_mm, velocity, pressure_drop_per_meter])

    df = pd.DataFrame(pipe_data,
                        columns=["Material", "Nominal diameter (mm)", "Internal diameter (mm)", "Velocity (m/s)",
                                "Pressure drop (Pa/m)"])

    # Calculate total length and total volume
    #total_length = df["Length (m)"].sum()
    #total_volume = df["Pipe volume (m³)"].sum()

    # Append a totals row to the DataFrame
    #df.loc['Total'] = ['', '', '', total_length, total_volume]

    # Display the table
    st.dataframe(df)

    # Download the Excel file
    st.download_button(
        label="Download as Excel",
        data=convert_df_to_excel(df),
        file_name="pipe_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Option to clear all entries
    if st.button('Clear all'):
        # Clear the list of pipe entries
        st.session_state['pipe_entries'] = []
        existing_file = False

        st.success('All entries and loaded files have been cleared.')
        st.rerun()  # Refresh the app to reflect changes
