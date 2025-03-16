import streamlit as st
import pandas as pd
import psychrolib
import bokeh

from processing.ventilation_processing import (calculate_ach_volume,
                                                      calculate_volume_flow_rate,
                                                      calculate_occupation_flow_rate,
                                                      calculate_room_volume,
                                                      calculate_rect_duct_area,
                                                      plot_duct_cross_section,
                                                      calculate_duct_velocity,
                                                      calculate_pressure_loss,
                                                      find_min_rect_size,
                                                      calculate_aspect_ratio,
                                                      find_min_diameter,
                                                      calculate_round_duct_area,
                                                      conversion_factors,
                                                      convert_airflow_rate,
                                                      get_air_properties,
                                                      plot_psychrometric)
from common import setup_page


def get_room_volume(dimension_type):
    if dimension_type == 'volume':
        room_volume = st.number_input("Room volume (m³)", min_value=1.0, step=1.0, value=50.0)
        return room_volume, None, None

    ceiling_height = st.number_input("Ceiling height (m)", min_value=1.0, step=0.1, value=2.5)

    if dimension_type == 'area and height':
        floor_area = st.number_input("Floor area (m²)", min_value=1.0, step=1.0, value=50.0)

    elif dimension_type == 'dimensions and height':
        room_width = st.number_input("Room width (m)", min_value=1.0, step=1.0, value=5.0)
        room_depth = st.number_input("Room depth (m)", min_value=1.0, step=1.0, value=5.0)
        floor_area = room_width * room_depth

    else:
        floor_area = None

    # Ensure `floor_area` and `ceiling_height` are available
    if floor_area is not None and ceiling_height is not None:
        room_volume = calculate_room_volume(floor_area, ceiling_height)
        return room_volume, floor_area, ceiling_height
    else:
        st.error("Please provide valid inputs.")
        return None, None, None


def results(df):
    # only show results for ACH & VRF calculations
    with st.expander('Results'):
        st.subheader('Results')
        if st.session_state.ACH_results:
            # Display and allow editing of the DataFrame using st.data_editor
            edited_df = st.data_editor(df, num_rows="dynamic")

            # Update the session state with the edited DataFrame
            st.session_state.ACH_results = edited_df.to_dict('records')

            if st.button('clear all results'):
                st.session_state.ACH_results = []
                st.rerun()
        else:
            st.markdown('Enter some values to view results')

        # Equations
        st.subheader('Equations')
        st.latex(
            r"\text{Volume Flow Rate} = \frac{{\text{{Floor Area}} \times \text{{Ceiling Height}} \times \text{{ACH}}}}{{3600}}")
        st.latex(
            r"ACH = \frac{{\text{{Volume Flow Rate}} \times 3600}}{{\text{{Floor Area}} \times \text{{Ceiling Height}}}}")


### APPENDING VALUES FOR AIR CHANGES AND VOLUME FLOW CALCULATIONS

def append_values_volume(room_reference, room_volume, ach, volume_flow_rate):
    # appending values function
    st.session_state.ACH_results.append({
        "Room reference": room_reference,
        "Room volume (m³)": room_volume,
        "Air changes (/hour)": ach,
        "Volume flow rate (m³/s)": volume_flow_rate
    })


def append_values_area(room_reference, floor_area, ceiling_height, room_volume, ach, volume_flow_rate):
    # appending values function
    st.session_state.ACH_results.append({
        "Room reference": room_reference,
        "Floor area (m²)": floor_area,
        "Ceiling height (m)": ceiling_height,
        "Room volume (m³)": room_volume,
        "Air changes (/hour)": ach,
        "Volume flow rate (m³/s)": volume_flow_rate
    })


def display_rect_duct(air_volume, air_density):
    duct_calc_type = st.radio('Select the calculation type', ['Standard', 'Minimum duct size'], horizontal=True)

    if duct_calc_type == 'Standard':

        # inputs
        height_mm = st.number_input('Height mm', min_value=100, step=25, value=100)
        width_mm = st.number_input('Width mm', min_value=100, step=25, value=100)

        # run calcs
        duct_area_sqm, eq_diameter_mm = calculate_rect_duct_area(width_mm, height_mm)
        duct_velocity = calculate_duct_velocity(duct_area_sqm, air_volume)
        pressure_loss = calculate_pressure_loss(eq_diameter_mm, air_density, duct_velocity)

        # results
        st.success(f'''
                   Results
                    - Velocity is {duct_velocity:.2f} m/s
                    - Pressure loss is {pressure_loss:.2f} Pa/m
                    - Aspect ratio is {width_mm / height_mm:.1f}
                    ''')

    elif duct_calc_type == 'Minimum duct size':
        # for rectangular ducts allow max width selection
        use_max_width = st.checkbox('Fix one dimension')
        if use_max_width:
            max_dim_mm = st.number_input('Fixed dimension mm', min_value=100, step=25, value=200)
        else:
            max_dim_mm = None

        max_duct_velocity = st.number_input('Max duct velocity m/s', min_value=1.0, step=0.5, value=5.0, max_value=15.0,
                                            help='Velocities highter than 5 m/s can cause excessive noise and pressure loss in a system')

        # run calcs
        width_mm, height_mm = find_min_rect_size(air_volume, max_duct_velocity, max_dim_mm)
        area = width_mm * height_mm / (1000 * 1000)

        # run calcs
        duct_area, eq_diameter = calculate_rect_duct_area(width_mm, height_mm)
        duct_velocity = calculate_duct_velocity(duct_area, air_volume)
        pressure_loss = calculate_pressure_loss(eq_diameter, air_density, duct_velocity)
        aspect_ratio = calculate_aspect_ratio(width_mm, height_mm)

        if aspect_ratio >= 4:
            st.warning('Aspect ratio is greater than 4 to 1 in one axis, this is typically not ok.')

        # results
        st.success(f'''
                    Results
                    - Minimum size is {width_mm:.0f}mm x {height_mm:.0f}mm
                    - Pressure loss is {pressure_loss:.0f} Pa/m
                    - Aspect ratio is {aspect_ratio:.1f}
                    ''')

    else:
        raise Exception('Unhandled duct_calc_type: ' + duct_calc_type)

    with st.expander('Plot'):
        # Example usage in Streamlit
        fig = plot_duct_cross_section(width_mm, height_mm, None)
        # Show the plot
        st.pyplot(fig)


def display_round_duct(air_volume, air_density):
    """Handles the round duct shape calculations."""

    # Inputs
    diameter_mm = st.number_input('Diameter (mm)', min_value=100, step=25, value=100)
    max_duct_velocity = st.number_input(
        'Max Duct Velocity (m/s)', min_value=1.0, step=0.5, value=5.0,
        help='Velocities > 5 m/s can cause excessive noise and pressure loss.'
    )

    # Run calculations
    min_diameter = find_min_diameter(air_volume, max_duct_velocity)
    duct_area = calculate_round_duct_area(diameter_mm)
    duct_velocity = calculate_duct_velocity(duct_area, air_volume)
    pressure_loss = calculate_pressure_loss(diameter_mm, air_density, duct_velocity)

    # Results
    st.success(f'''
               Results
               - Velocity is {duct_velocity:.2f} m/s
               - Pressure drop is {pressure_loss:.2f} Pa/m
               - Min diameter for {max_duct_velocity} m/s is {min_diameter} mm
               ''')
    with st.expander('Plot'):
        # Example usage to plot a round duct:
        plot_duct_cross_section(None, None, diameter_mm)


# WSP header
setup_page('Ventilation', 'david.naylor@wsp.com')

# initialise session state for list of past entries
if 'ACH_results' not in st.session_state:
    st.session_state['ACH_results'] = []

tool_selection = st.selectbox('Select your tool', (
    'Volume flow rates', 'Unit converter', 'CIBSE duct sizing', 'Louvres', 'Psychrometirc chart'), index=None)

with st.expander('How to use'):
    st.markdown('''
                This is a basic app to help you do quick checks for ventilation calculations, it's not here to calculate your index leg.  
                - Select a calculation type below  
                - Some results are stored in the results dropdown, although they won't stay if you refresh the page.
                ''')

if tool_selection is None:
    st.markdown('''
            Welcome to the ventilation homepage
            - Here you will find a range of calculator tools that can help you in your day to day work.
            - They are designed to be accessible and simple to use so you can quickly check what you need to with less hassle.
            - Some calculations include a bit of guidance, and pop-up warnings, but please don't assume the calculation is perfect if none are present. 
            ''')

if tool_selection == 'Volume flow rates':
    # Calculation set up 
    calculation_type = st.radio('Select what you want to calculate',
                                ['ac/hr', 'volume flow rate', 'ac/hr vs occupancy'], horizontal=True)
    dimension_input_type = st.radio('Select input dimensions', ['volume', 'area and height', 'dimensions and height'],
                                    horizontal=True)

    # Inputs form 
    with st.form('ach and vfr inputs', border=False):

        # Common inputs across both calculations
        room_reference = st.text_input("Room reference")

        # Call the function to get the room volume based on the dimension input type
        room_volume, floor_area, ceiling_height = get_room_volume(dimension_input_type)

        if room_volume is not None:

            if calculation_type == 'ac/hr':
                # Specific inputs for air changes per hour (ACH)
                volume_flow_rate = st.number_input("Volume flow rate (m³/s)", min_value=0.01, step=0.01, value=0.1)

                # Form submit button
                if st.form_submit_button("Calculate ac/hr"):
                    ach = calculate_ach_volume(room_volume, volume_flow_rate)

                    if dimension_input_type == 'volume':
                        append_values_volume(room_reference, room_volume, ach, volume_flow_rate)
                    else:
                        append_values_area(room_reference, floor_area, ceiling_height, room_volume, ach,
                                           volume_flow_rate)

                    st.success(f"**Result:** Air changes per hour (ac/hr) = {ach:.2f}")

            elif calculation_type == 'volume flow rate':
                # Specific inputs for volume flow rate calculation
                air_changes_per_hour = st.number_input("ac/hr", min_value=1.0, step=1.0, value=6.0)

                # Form submit button
                if st.form_submit_button("Calculate volume flow rate"):
                    volume_flow_rate = calculate_volume_flow_rate(room_volume, air_changes_per_hour)
                    append_values_area(room_reference, floor_area, ceiling_height, room_volume, air_changes_per_hour,
                                       volume_flow_rate)

                    st.success(f"**Result:** Volume flow rate = {volume_flow_rate:.4f} m³/s")

            elif calculation_type == 'ac/hr vs occupancy':

                # Specific inputs
                occupation = st.number_input('number of people', min_value=1, step=1)
                air_per_person = st.slider('air volume l/person/s', min_value=1, max_value=20, step=1, value=10)
                air_changes_per_hour = st.number_input("ac/hr", min_value=1.0, step=1.0, value=6.0)

                if st.form_submit_button("calculate most onerous"):
                    occupation_flow_rate = calculate_occupation_flow_rate(occupation, air_per_person)
                    volume_flow_rate = calculate_volume_flow_rate(room_volume, air_changes_per_hour)
                    if occupation_flow_rate > volume_flow_rate:
                        st.success(
                            f'The most onerous requirement is occupation, this is equivalent to {occupation_flow_rate:.2f} m³/s')
                    else:
                        st.success(
                            f'The most onerous requirement is {air_changes_per_hour} air changes, this is equivalent to {volume_flow_rate:.2f} m³/s')

    if calculation_type != 'ac/hr vs occupancy':
        # create and display df with results in 
        df = pd.DataFrame(st.session_state.ACH_results)
        results(df)

if tool_selection == 'Unit converter':

    # Conversion factors from one unit to another. User input for the value and units
    input_value = st.number_input('enter the value', min_value=0.0, value=1.0, step=0.1)
    from_unit = st.selectbox('from', options=list(conversion_factors.keys()))
    to_unit = st.selectbox('to', options=list(conversion_factors.keys()))

    # Perform the conversion
    if st.button('convert'):
        converted_value = convert_airflow_rate(input_value, from_unit, to_unit)
        st.success(f'{input_value:.2f} {from_unit} is equal to {converted_value:.2f} {to_unit}')

if tool_selection == 'CIBSE duct sizing':
    # Air inputs
    st.subheader('Air')

    # Inputs
    air_volume = st.number_input('Air Volume Flow Rate (m³/s)', min_value=0.01, step=0.01, value=0.05)
    with st.expander('Advanced air properties'):
        air_temperature = st.number_input('Air Temperature (°C)', value=20)
        pressure = st.number_input('Pressure (Pa)', min_value=0, value=101325)

    # Run function to get properties
    properties = get_air_properties(air_temperature, pressure)
    st.markdown(f'''
            - Density is {properties['Density (kg/m³)']:.2f} kg/m³
                ''')

    st.subheader('Duct')
    duct_shape = st.radio('select the duct shape', ['Rectangular', 'Round'], horizontal=True)

    if duct_shape == 'Rectangular':
        display_rect_duct(air_volume, properties['Density (kg/m³)'])

    elif duct_shape == 'Round':
        display_round_duct(air_volume, properties['Density (kg/m³)'])

if tool_selection == 'Louvres':
    st.markdown('Calculate louvre size requirement and face velocity')

    # Input fields for dimensions
    width = st.number_input("Louvre width (mm)", min_value=0, step=10, value=300)
    height = st.number_input("Louvre height (mm)", min_value=0, step=10, value=200)

    # Calculate total louvre area
    total_area = width * height / (1000 * 1000)

    # Show the calculated total area
    st.write(f"**Total louvre area is** {total_area:.2f} m²")

    # Input fields for airflow rate and free area percentage
    airflow_rate = st.number_input("Airflow rate (m³/s)", min_value=0.0, step=0.01, value=0.5)
    free_area_percentage = st.slider("Free area %", min_value=0, max_value=100, value=50)

    # Calculate free area based on percentage
    free_area = (free_area_percentage / 100) * total_area

    # Calculate face velocity if inputs are valid
    if total_area > 0 and free_area > 0:
        face_velocity = airflow_rate / free_area
        st.success(f"The face velocity is: {face_velocity:.2f} m/s")
    else:
        st.warning("Width, height, and free area must be greater than zero to perform the calculation.")

if tool_selection == 'Psychrometirc chart':
    st.markdown("Plot a psychrometric chart, and add points for your calculations - this is a WIP, if you can't wait try [this](https://www.flycarpet.net/en/psyonline)")

    # Initialize session state for storing points
    if 'points' not in st.session_state:
        st.session_state['points'] = []

    with st.expander('Modify graph'):
        # User inputs to modify the limits of the graph
        pressure = st.number_input("Atmospheric Pressure (Pa)", value=101325, step=500)
        t_range = st.slider("Dry-bulb Temperature Range (°C)", -10, 60, (5, 45))
        rh_range = st.slider("Relative Humidity Range (%)", 0, 100, (0, 100), step=10)
        twb_range = st.slider("Wet-bulb Temperature Range (°C)", -10, t_range[1], (-10, 45), step=10)
        y_max = st.slider("Maximum Humidity Ratio ($kg_{water}/kg_{dry air}$)", 0.01, 0.1, 0.025)

    p = plot_psychrometric(pressure, t_range, rh_range, twb_range, y_max)

    with st.expander('Add a point'):
        # Inputs for adding a point
        db_temp = st.number_input("Dry-bulb Temperature for Point (°C)", value=25.0)
        wb_temp = st.number_input("Wet-bulb Temperature for Point (°C)", value=20.0)
        label = st.text_input("Label for Point", value=f"Point {len(st.session_state['points']) + 1}")
        # Button to add the point
        if st.button("Add Point"):
            if wb_temp <= db_temp:
                # Set unit system to SI
                psychrolib.SetUnitSystem(psychrolib.SI)
                hum_ratio_point = psychrolib.GetHumRatioFromTWetBulb(db_temp, wb_temp, pressure)
                # Append the point to session state
                st.session_state['points'].append((db_temp, hum_ratio_point, label))
                st.success(
                    f"Point added: {label} - DB Temp: {db_temp}°C, WB Temp: {wb_temp}°C, Humidity Ratio: {hum_ratio_point:.4f} kg_water/kg_dry_air")
            else:
                st.warning("Wet-bulb temperature cannot be higher than dry-bulb temperature.")

        # Button to clear all points
        if st.button("Clear All Points"):
            st.session_state['points'] = []
            st.success("All points cleared.")

        # Convert session state points to a pandas DataFrame for display
        if st.session_state['points']:
            points_df = pd.DataFrame(st.session_state['points'],
                                     columns=["Dry-bulb Temp (°C)", "Humidity Ratio", "Label"])

            # Display points using st.data_editor
            edited_points = st.data_editor(points_df, num_rows="dynamic", key="points_editor")

            # Update session state with any changes made in the data editor
            st.session_state['points'] = list(edited_points.itertuples(index=False, name=None))

            # Extract data for plotting
            db_temps, hum_ratios, labels = zip(*st.session_state['points'])
            p.circle(db_temps, hum_ratios, size=10, color="red", legend_label="Added points")

    # Display the plot by embedding html
    st.components.v1.html(bokeh.embed.file_html(p))

