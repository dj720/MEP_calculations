import streamlit as st
import math
import pandas as pd

from common import setup_page
from processing.public_health_processing import (load_excel_data,
                                                        convert_df_to_excel,
                                                        select_stack_option,
                                                        appliance_du)

# WSP header
setup_page('Public health', 'david.naylor@wsp.com')

tool_selection = st.selectbox('Select your tool', ('Gradients', 'Stack sizing BS 12056', 'Pipe volume'), index=None)

if tool_selection is None:
    st.markdown('''
            Welcome to the public health homepage
            - Here you will find a range of calculator tools that can help you in your day to day work.
            - They are designed to be accessible and simple to use so you can quickly check what you need to with less hassle.
            - Some calculations include a bit of guidance, and pop-up warnings, but please don't assume the calculation is perfect if none are present. 
            ''')

if tool_selection == 'Gradients':
    fall_mm = st.number_input('Fall mm', min_value=0.0, value=10.0, step=10.0)
    run_mm = st.number_input('Run length mm', min_value=1, value=1000, step=10)

    gradient = run_mm / fall_mm
    angle_degrees = math.degrees(math.atan(fall_mm / run_mm))
    percentage = (fall_mm / run_mm) * 100

    st.success(f'''
               Results 
               - Gradient is 1 in {gradient:.1f}
               - Angle is {angle_degrees:.2f}
               - Percentage is {percentage:.1f} %
               ''')

if tool_selection == 'Pipe volume':
    # Initialize session state for pipe entries if not already
    if 'pipe_entries' not in st.session_state:
        st.session_state['pipe_entries'] = []

    # Load data from excel file into df
    pipe_data = 'data/Pipe dimension data.xlsx'
    xls_pipes = pd.ExcelFile(pipe_data)
    df_pipes = xls_pipes.parse('Formatted data')

    # give the option to reload an excel file into the doc 
    existing_file = st.checkbox('Reload existing excel file')
    if existing_file:
        # File upload section to load an existing Excel file
        uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"], key='uploaded_file')
        if uploaded_file is not None:
            # Update the session state with all column values
            st.session_state['pipe_entries'] = load_excel_data(uploaded_file)
            st.toast('Excel data loaded successfully!')

    # Show the form to add pipes
    st.subheader('Add new entry')

    pipe_material = st.selectbox('Pipe material', df_pipes['Material'].unique())
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
        int_diameter_mm = st.number_input('Manually set pipe diameter (mm)', min_value=1, value=20)

    length_m = st.number_input(f'Pipe length (m)', min_value=1, key=f'length_{len(st.session_state["pipe_entries"])}')
    m3_per_meter = math.pi * (int_diameter_mm / 2000) ** 2
    pipe_volume_m3 = m3_per_meter * length_m

    # Add the diameter and length to session state
    if st.button('Add pipe'):
        st.session_state['pipe_entries'].append(
            (pipe_material, nom_diameter_mm, int_diameter_mm, length_m, pipe_volume_m3))
        st.toast(f'Added {pipe_material}, {nom_diameter_mm} mm, {length_m:.2f} m')
        st.rerun()

    # Display the list of pipes that have been added in a table (from both manual input and uploaded file)
    if len(st.session_state['pipe_entries']) > 0:
        st.subheader("Pipe Details")

        # Create a DataFrame from session state data
        pipe_data = []
        for pipe_material, nom_diameter_mm, int_diameter_mm, length_m, pipe_volume_m3 in st.session_state[
            'pipe_entries']:
            pipe_data.append([pipe_material, nom_diameter_mm, int_diameter_mm, length_m, round(pipe_volume_m3, 2)])

        df = pd.DataFrame(pipe_data,
                          columns=["Material", "Nominal diameter (mm)", "Internal diameter (mm)", "Length (m)",
                                   "Pipe volume (m³)"])

        # Calculate total length and total volume
        total_length = df["Length (m)"].sum()
        total_volume = df["Pipe volume (m³)"].sum()

        # Append a totals row to the DataFrame
        df.loc['Total'] = ['', '', '', total_length, total_volume]

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

if tool_selection == 'Stack sizing BS 12056':
    # Streamlit app interface
    st.subheader("Discharge Units Calculation")

    # Create table-like columns for Appliance, DU, Number, and Total
    col1, col2, col3, col4 = st.columns([3, 3, 2, 3], vertical_alignment='top')

    # Set headers for the columns
    col1.write("**Appliance**")
    col2.write("**DU l/s**")
    col3.write("**Quantity**")
    col4.write("**Total DU l/s**")

    # Create inputs for appliance quantities and calculate totals
    appliance_quantities = {}
    appliance_totals = {}
    total_du = 0

    wc_present = False

    # Loop through each appliance and create a row in the table
    for appliance, du in appliance_du.items():
        with col1:
            st.write(appliance)  # Adjust the width as needed
            st.write('')
        with col2:
            st.write(f"{du}")  # Adjust the width as needed
            st.write('')
        with col3:
            # Smaller input box for better alignment
            quantity = st.number_input(f"{appliance}", min_value=0, value=0, step=1, key=appliance,
                                       label_visibility="collapsed")
            appliance_quantities[appliance] = quantity
            # Check if the appliance is a WC and if any quantity is added
            if "WC" in appliance and quantity > 0:
                wc_present = True  # Set wc_present to True if any WC quantity is greater than 0

        with col4:
            # Calculate and display total DU for each appliance
            total_appliance_du = du * quantity
            appliance_totals[appliance] = total_appliance_du
            total_du += total_appliance_du
            st.write(f"{total_appliance_du:.2f}")  # Adjust the width as needed
            st.write('')

            # Additional input for other DU values
    additional_du = st.number_input("Enter any additional DU's", min_value=0.0, value=0.0, step=0.1)
    total_du += additional_du

    # Display the final total DU including additional input
    st.success(f"Total DU: {total_du:.2f} l/s")

    frequency_of_use = {
        'Intermittent use, e.g. house, flat, offices': 0.5,
        'Frequent use, e.g. hotel, school, hospital': 0.7,
        'Congested use, e.g. public use': 1.0,
        'Special use, e.g. laboratory': 1.2
    }

    # Create a dropdown menu with the keys of the frequency_of_use dictionary
    selected_frequency = st.selectbox('Type of use', list(frequency_of_use.keys()))

    # Get the corresponding value from the dictionary
    frequency_factor_K = frequency_of_use[selected_frequency]

    st.write(f'Frequency factor (K) is {frequency_factor_K}')

    total_wastewater_flowrate = total_du ** 0.5 * frequency_factor_K

    if st.checkbox('Any additional water discharge?'):
        pumped_waste = st.number_input("Pumped waste discharge l/s", min_value=0.0, value=0.0, step=0.1)
        continuous_discharge = st.number_input("Any continuous discharge l/s", min_value=0.0, value=0.0, step=0.1,
                                               help='e.g. AC units')
        total_wastewater_flowrate += pumped_waste + continuous_discharge

    vent_method = st.radio('Venting method', ['Primary', 'Secondary'], horizontal=True)

    stack_option = select_stack_option(total_wastewater_flowrate, wc_present, vent_method)

    st.success(f'''
               Results
               - Total waste water flow rate is: {total_wastewater_flowrate:.2f} l/s
               - Venting recommendation is {stack_option}''')
