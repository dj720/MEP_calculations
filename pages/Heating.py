import streamlit as st
from common import setup_page
import pandas as pd
from pyfluids import Fluid, FluidsList, Input

from processing.heating_processing import (create_resultsheet,
                                                  calculate_coil_size,
                                                  calculate_reheat_time,
                                                  calculate_primary_flowrate,
                                                  calculate_acceptance_factor,
                                                  calculate_CFP,
                                                  calculate_expansion_factor,
                                                  calculate_EV_size,
                                                  calculate_max_system_pressure,
                                                  calculate_heat_transfer,
                                                  calculate_deltaT,
                                                  calculate_flow_rate,
                                                  get_heating_conversion_factors)


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

def export_results(initial_temperature, 
                   final_temperature, 
                   coil_size, 
                   vessel_volume, 
                   reheat_time, 
                   calculation_type,
                   include_primary, 
                   primary_flow_temp, 
                   primary_return_temp, 
                   primary_flowrate):
    
    st.header("Export results")
    engineers_notes = st.text_area('Engineers notes', 
                                   placeholder='Enter any notes to explain design decisions',
                                   max_chars=1000)
    
    pdf_filename = st.text_input("File reference", 
                                 placeholder='Project XYZ - DHWS Calculation', 
                                 max_chars=100)

    # Default filename if not provided
    if pdf_filename == '':
        pdf_filename = 'Project XYZ - DHWS Calculation'
    # Ensure file extension is .pdf
    if not pdf_filename.endswith(".pdf"):
        pdf_filename += ".pdf"

    # downloading section
    with st.spinner('Working on it...'):
        if st.button("Generate PDF"):
            pdf_output = create_resultsheet(initial_temperature, final_temperature, coil_size, vessel_volume,
                                            reheat_time, calculation_type, engineers_notes, include_primary,
                                            primary_flow_temp, primary_return_temp, primary_flowrate)
            # Display the download button
            st.download_button(label="Download PDF", data=pdf_output, file_name=pdf_filename, mime="application/pdf")
            st.success("PDF Generated Successfully! To run another calculation refresh this page")

def convert_heating_units():
    # Fetch conversion factors
    to_joules = get_heating_conversion_factors()

    # Inputs
    from_unit = st.selectbox("From", list(to_joules.keys()))
    to_unit = st.selectbox("To", list(to_joules.keys()))
    amount = st.number_input(f"Enter the amount of {from_unit}", value=1.0, min_value=0.0, step=1.0)

    # Convert to the base unit (joules) and then to the target unit
    amount_in_joules = amount * to_joules[from_unit]
    result = amount_in_joules / to_joules[to_unit]

    # Round result to 3 significant figures
    result_rounded = round(result, 3)

    # Result
    st.success(f"{amount} {from_unit} = {result_rounded} {to_unit}")

def check_temperature_validity(initial_temp, final_temp):
    if final_temp <= initial_temp:
        st.warning('Your result is negative... take a look at input temperatures.', icon="🌡️")
        return False
    return True

def check_primary_temperarure(primary_flow_temp):
    if primary_flow_temp < 60:
        st.warning(
            'Flow temperature is lower than 60°C, another source of heat is required to perform pasturisation on the calorifier.',
            icon="🦠")
        return False
    return True

def display_result(calculation_type, result_value, unit, primary_flowrate=None):
    result_message = f"- {calculation_type} is {result_value:.2f} {unit}"
    if primary_flowrate is not None:
        result_message += f"\n- Primary flow rate is {primary_flowrate:.2g} kg/s"
    st.success(f"Result\n{result_message}")

def display_results_logic(calculation_type, include_primary, reheat_time, primary_flowrate, coil_size):
    if calculation_type == "Re-heat time":
        st.form_submit_button('Update', on_click=display_result(
            "Re-heat time", reheat_time, "minutes", primary_flowrate if include_primary else None
        ))
    elif calculation_type == "Coil size":
        st.form_submit_button('Update', on_click=display_result(
            "Coil size", coil_size, "kW", primary_flowrate if include_primary else None
        ))


def display_working(include_primary, calculation_type, vessel_volume, final_temperature, initial_temperature, coil_size,
                    reheat_time, primary_flow_temp, primary_return_temp, primary_flowrate):
    st.markdown("\n")
    st.subheader('Vessel calculations')
    st.markdown("For a full derivation and guidance refer to 'Working' tab")
    # render populated equations
    if calculation_type == "Re-heat time":
        st.markdown("- Using the provided values:")
        st.latex(
            r"\text{time} = \frac{" + f"{vessel_volume} \\cdot 4.18 \\cdot ({final_temperature} - {initial_temperature})" + r"}{" + f"60 \\cdot {coil_size}" + r"}" '\space min')
        st.markdown("- Solving the equation:")
        st.latex(
            r"\text{time} = \frac{" + f"{vessel_volume * 4.18 * (final_temperature - initial_temperature):.0f}" + r"}{" + f"{60 * coil_size}" + r"}" '\space min')
        st.markdown("- Result:")
        st.latex(r"\text{time} \approx " + f"{reheat_time:.2g}" '\space min')
        st.markdown("\n")

    elif calculation_type == "Coil size":
        st.markdown("- Using the provided values:")
        st.latex(
            "\\text{Coil size} = \\frac{" + f"{vessel_volume} \\cdot 4.18 \\cdot ({final_temperature} - {initial_temperature})" + r"}{" + f"60 \\cdot {reheat_time}" + r"}" + '\space kW')
        st.markdown("- Solving the equation:")
        st.latex(
            r"\text{Coil size} = \frac{" + f"{vessel_volume * 4.18 * (final_temperature - initial_temperature):.0f}" + r"}{" + f"{60 * reheat_time}" + r"}" + '\space kW')
        st.markdown("- Result:")
        st.latex(r"\text{Coil size} \approx " + f"{coil_size:.2g} \space kW")
        st.markdown("\n")

    if include_primary:
        st.divider()
        st.subheader("Primary circuit calculations")
        st.markdown("Once the coil size is known, the primary side calculations can be undertaken")
        st.latex(r"\Delta T_{pri} =" + f"{(primary_flow_temp - primary_return_temp):}" + '\space K')
        st.markdown("The mass primary circuit mass flow rate is therefore")
        st.latex(
            r"\dot{m}_{pri} = \frac{" + f"{coil_size}" + r"}{" + f"{4.18 * (primary_flow_temp - primary_return_temp):}" + r"}" r"\space kg/s")
        st.latex(r"\therefore \space \dot{m}_{pri} \approx " + f"{primary_flowrate:.2g}" r"\space kg/s")


def display_workingtab(calculation_type, include_primary):
    # calculation derivation
    st.subheader("Assumptions")
    st.markdown("- The vessel contains only water")
    if include_primary:
        st.markdown("- The primary circuit also contains only water")

    st.divider()

    st.subheader("Equation derviation")
    st.markdown("- The calculation is based on the formula")
    st.latex(r"Q = mC_p(T_{final} - T_{initial})")
    st.markdown("- A summary of variables")
    col1, col2 = st.columns(2)
    with col1:
        st.latex(r"Q = Heat\space transfer\space (kJ)")
        st.latex(r"\dot{Q}_{coil} = Coil \space rating\space (kW\space or\space kJ/s )")
        st.latex(r"t = time \space (s)")
        st.latex(r"m = Mass\space of\space water \space(kg\space or \space litres)")
    with col2:
        st.latex(r"C_p = Specific\space heat\space capacity\space (kJ/kgK)")
        st.latex(r"T_{initial} = Cold \space fill \space temperature \space (K)")
        st.latex(r"T_{final} = Required \space final \space temperature \space (K)")
        st.latex(r"C_p = Specific\space heat\space capacity\space (4.18 \space kJ/kgK)")

    # futher derivations
    st.markdown("- A summary of equations")
    col3, col4 = st.columns(2)
    with col3:
        st.latex(r"Q = \dot{Q}_{coil} \cdot t")
    with col4:
        st.latex(r"\Delta T_{ves} = Vessel \space temperature\space change\space (K) = T_{final} - T_{initial}")

    # add final calc dependent on type
    st.markdown("- The final rearranged equation")
    if calculation_type == "re-heat time":
        latex_expression = r"\therefore \space t\space (min) = \frac{{mC_p \Delta T_{ves}}}{{60\space \dot{Q}_{coil}}}"
    else:
        latex_expression = r"\therefore \space Coil\space rating \space (\dot{Q}_{coil})= \frac{{mC_p\Delta T_{ves}}}{{60\space t\space (min)}}"
    st.latex(latex_expression)

    # add primary coil size/flowrate calc if it is selected to be included
    if include_primary:
        st.divider()
        st.subheader("Primary circuit calculations")
        st.markdown(
            "Using the same base formula as stated above, once the coil size is known, the primary side calculations can be undertaken")
        st.latex(r"\Delta T_{pri} = Primary \space temperature \space change\space (K) = T_{flow} - T_{return}")
        st.latex(r"\dot{m}_{pri} = Primary \space mass \space flowrate \space (kg/s)")
        #st.latex(r"\dot{Q}_{coil} = Heat\space transfer\space (KJ) = Coil \space rating\space (KW\space or\space KJ/s ) \cdot time \space (s)")
        st.markdown("The primary circuit mass flow rate is therefore")
        st.latex(r"\therefore \space \dot{m}_{pri} = \frac{\dot{Q}_{coil}}{C_p\Delta T_{pri}}")

    # guidance notes
    st.divider()
    st.subheader("Guidance")
    st.markdown("""
                    - Traditionally vessel re-heat times are designed to a designated time to complete such as 30 or 60 minutes, although each vessel and coil should be designed based on the particular requirements of the project i.e. building type, and occupational usage patterns.
                    - Refer to the Institute of Plumbing guide and CIBSE guide G for further information on sizing for the application.
                    - Calorifiers require the ability to run pasturisation cycle above 60°C. Either via LTHW supply or electric immersion for supplies less then 60°C.
                    - No margin of safety is applied to the calculations.
                    """)


def append_values_expansion(max_temperature, static_head, SV_margin, EV_size, vessel_acceptance):
    # appending values function
    st.session_state.EV_results.append({
        "Maximum temperature (°C)": max_temperature,
        "Static head (m)": static_head,
        "Safety valve margin (bar g)": SV_margin,
        "Expansion vessel volume (litres)": EV_size,
        'Acceptance factor': vessel_acceptance
    })


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


def EV_results(df):
    # only show results for ACH & VRF calculations
    with st.expander('Results'):
        st.subheader('Results')
        if st.session_state.EV_results:
            # Display and allow editing of the DataFrame using st.data_editor
            edited_df = st.data_editor(df, num_rows="dynamic")

            # Update the session state with the edited DataFrame
            st.session_state.EV_results = edited_df.to_dict('records')

            if st.button('clear all results'):
                st.session_state.EV_results = []
                st.rerun()
        else:
            st.markdown('Enter some values to view results')


# WSP header
setup_page('Heating', 'david.naylor@wsp.com')

tool_selection = st.selectbox('Select your tool',
                              ('Calorifier re-heat',
                               'Expansion vessels BS7074',
                               'Unit converter',
                               'Heat transfer',
                               'CIBSE pipe sizing',
                               'Pyfluids'
                               ), index=None)

if tool_selection is None:
    st.markdown('''
            Welcome to the heating homepage
            - Here you will find a range of calculator tools that can help you in your day to day work.
            - They are designed to be accessible and simple to use so you can quickly check what you need to with less hassle.
            - Some calculations include a bit of guidance, and pop-up warnings, but please don't assume the calculation is perfect if none are present. 
            ''')

if tool_selection == 'Calorifier re-heat':
    with st.expander('How to use'):
        st.markdown('''
                    This is a basic app to help you do quick checks for calorifier reheat calculations.  
                    - Select a calculation type below to either work to a time to reheat or coil size.
                    - Toggle the primary flow rate on to include your primary heat source.
                    - Export the results with any comments to create a pdf to store in your calculations folder. 
                    - A summary of the calculation method and some guidance is avaibale in the 'Working' tab.
                    ''')
    # allow toggling of equation type
    calculation_type = st.radio("Calculation selection", ["Re-heat time", "Coil size"], horizontal=True)

    # create tabs for inputs and working
    tab_input, tab_working = st.tabs(["Inputs", "Working"])

    with tab_input:
        # include the primary side calculation?
        include_primary = st.checkbox('Include primary flow rate calculation?')
        # input form
        with st.form("form_inputs", border=False):
            st.subheader('Vessel')
            # common input values across both calculations
            initial_temperature = st.slider("Initial temperature", min_value=0.0, max_value=100.0, value=15.0, step=1.0,
                                            format="%.0f °C",
                                            help='typically for mains water fill this would be around 15 or 20°C')
            final_temperature = st.slider("Final temperature", min_value=0.0, max_value=100.0, value=60.0, step=1.0,
                                          format="%.0f °C")
            vessel_volume = st.number_input("Volume, litres", min_value=0.0, max_value=10000.0, value=500.0, step=10.0,
                                            format="%.0f")

            # differentiate the 2 equations and their inputs and submit buttons
            if calculation_type == "Re-heat time":
                coil_size = st.number_input("Coil size, kW", min_value=0.0, max_value=1000.0, value=50.0, step=1.0,
                                            format="%.1f")
                st.markdown("\n")
                reheat_time = calculate_reheat_time(initial_temperature, final_temperature, vessel_volume, coil_size)
                check_temperature_validity(initial_temperature, final_temperature)

            elif calculation_type == 'Coil size':
                reheat_time = st.number_input("Required re-heat time, min", min_value=0.0, max_value=120.0, value=60.0,
                                              step=1.0,
                                              help='typically this would be around 30 - 60 minutes, but will depend on the system requirements - refer to working tab for more info')
                st.markdown("\n")
                coil_size = calculate_coil_size(initial_temperature, final_temperature, vessel_volume, reheat_time)
                check_temperature_validity(initial_temperature, final_temperature)

            # Primary side calcs if included
            if include_primary:
                st.subheader('Primary circuit')
                primary_flow_temp = st.slider('Flow temperature', min_value=0.0, max_value=100.0, value=60.0, step=1.0,
                                              format="%.0f °C")
                check_primary_temperarure(primary_flow_temp)
                primary_return_temp = st.slider('Return temperature', min_value=0.0, max_value=100.0, value=40.0,
                                                step=1.0, format="%.0f °C")
                # pass inputs to function
                primary_flowrate = calculate_primary_flowrate(primary_flow_temp, primary_return_temp, coil_size)
                check_temperature_validity(primary_return_temp, primary_flow_temp)
            else:
                # set the primary values to zero so the pdf generate function doesnt get sad
                primary_flow_temp, primary_return_temp, primary_flowrate = 0, 0, 0

            # function to display the results dependent on the calculation
            display_results_logic(calculation_type, include_primary, reheat_time, primary_flowrate, coil_size)

        # populated calculation expander
        with st.expander("See working"):
            display_working(include_primary, calculation_type, vessel_volume, final_temperature, initial_temperature,
                            coil_size, reheat_time, primary_flow_temp, primary_return_temp, primary_flowrate)

        # export results
        with st.expander('Export results'):
            export_results(initial_temperature, final_temperature, coil_size, vessel_volume, reheat_time,
                           calculation_type, include_primary, primary_flow_temp, primary_return_temp, primary_flowrate)

    with tab_working:
        # all latex expressions and guidance 
        display_workingtab(calculation_type, include_primary)

if tool_selection == 'Expansion vessels BS7074':

    if 'EV_results' not in st.session_state:
        st.session_state['EV_results'] = []

    with st.expander('How to use'):
        st.markdown('''
                    This is a basic app to help you do quick checks for expansion vessel size calculations based on the BS7074 calculation method.
                    - If you don't know the system volume, toggle the option to calculate based on system capacity.
                    - A summary of the calculation method and some guidance is avaibale in the 'Working' tab.
                    ''')

    # create tabs for inputs and working
    tab1, tab2 = st.tabs(["Input", "Workings"])

    with tab1:
        # input form
        calculate_from_kw = st.radio(label='Calculate system volume from system output kW rating?',
                                     options=['Yes', 'No, system volume is known'])
        specify_acceptance = st.checkbox(label='Fill and spill type calculation',
                                         help='By selecting this you will be able to specify the vessel usage efficiency (aka acceptance factor) which is controlled by the ''fill and spill'' unit.')

        with st.form("form_inputs_EV", border=False):
            # inputs area 
            Lowest_WP = st.slider("Lowest working pressure", min_value=0.0, max_value=10.0, value=3.0, step=0.5,
                                  format="%.1f bar g",
                                  help='Typically the system component with the lowest allowable operating pressure, but can also be other components dependent on location in the system. Existing systems should generally not be taken beyond 3 bar')
            SV_margin = st.slider("Safety valve margin", min_value=0.0, max_value=2.0, value=0.5, step=0.1,
                                  format="%.1f bar g",
                                  help='Typically around 0.5 bar to protect equipment in the system against over pressure.')

            # can now calculate max working pressure
            max_temperature = st.slider("Maximum system temperature", min_value=0.0, max_value=100.0, value=80.0,
                                        step=1.0, format="%.0f °C",
                                        help='Maximum temperature the system can expect to achieve.')
            if max_temperature > 80:
                st.warning(
                    'Maximum system is greater than 80°C, check expansion vessel temperature limits and specify intermediate vessel as necessary.')

            if calculate_from_kw == 'Yes':
                litres_per_kw = st.slider('kW to system volume', min_value=0.0, max_value=15.0, value=12.0, step=1.0,
                                          format="%.0f l per kW",
                                          help='Typical values are in the range of 12 litres per kw')
                system_kw = st.number_input('System output in kw', min_value=0.0, value=300.0, step=20.0)
                system_volume = system_kw * litres_per_kw
            else:
                system_volume = st.slider("System volume", min_value=0.0, max_value=100.0, value=50000.0, step=100.0,
                                          format="%.0f litres")  # build feature to allow calculation based on kw

            static_head = st.slider("Static head", min_value=0.0, max_value=100.0, value=10.0, step=1.0,
                                    format="%.0f m",
                                    help='Difference in height to the highest point in the system.')

            # send inputs to functions 
            cold_fill_pressure = calculate_CFP(static_head)
            max_system_pressure = calculate_max_system_pressure(Lowest_WP, SV_margin)

            if specify_acceptance:
                vessel_acceptance = st.number_input('Vessel acceptance', min_value=0.1, max_value=1.0,
                                                    help='This is the percentage of the vessel which can be utilised.')
            else:
                vessel_acceptance = calculate_acceptance_factor(cold_fill_pressure, max_system_pressure)

            expansion_factor = calculate_expansion_factor(max_temperature)

            #st.write(system_volume, expansion_factor, vessel_acceptance)

            EV_size = calculate_EV_size(system_volume, expansion_factor, vessel_acceptance)

            if cold_fill_pressure > max_system_pressure:
                st.warning(
                    '''Cold fill pressure is greater then the maximum system pressure, so your values will be negative.''')

            if st.form_submit_button(label='Submit values'):
                st.success(f"""
                        Results
                        - Cold fill pressure {cold_fill_pressure:.2f} bar g
                        - Vessel acceptance {100 * vessel_acceptance:.2f} %
                        - Water expansion factor at {max_temperature:.1f}°C is {expansion_factor:.4f} 
                        - EV size {EV_size:.0f} litres
                        """)
                append_values_expansion(max_temperature, static_head, SV_margin, EV_size, vessel_acceptance)

        # create and display df with results in 
        df = pd.DataFrame(st.session_state.EV_results)
        EV_results(df)

    with tab2:
        # calculation derivation
        st.subheader("Assumptions")
        st.markdown("""
                    - The vessel contains only water
                    - A 10% safety factor is applied to the vessel size
                    """)
        st.divider()

        st.subheader("Equation derviation")
        st.markdown('coming soon...')

if tool_selection == 'Unit converter':
    convert_heating_units()

if tool_selection == 'Heat transfer':

    # Function to get fluid properties (for Water or Air)
    def get_medium_properties(transfer_medium, medium_temperature, pressure):

        fluid = Fluid(getattr(FluidsList, transfer_medium))

        # Update the fluid's state with the given temperature and pressure
        fluid.update(Input.pressure(pressure), Input.temperature(medium_temperature))

        # Return key properties
        properties = {
            'Specific Heat (kJ/kg·K)': fluid.specific_heat / 1000,
            'Density (kg/m³)': fluid.density,
        }

        st.markdown(f'''
                This calculation assumes the heat transfer medium is {str(transfer_medium).lower()} with:
                - Specific heat capacity of {properties['Specific Heat (kJ/kg·K)']:.2f} kJ/kgK
                - Density of {properties['Density (kg/m³)']:.2f} kg/m³
                    '''
                    )

        return properties


    # Calculation set up
    transfer_medium = st.selectbox('Transfer medium is...', ['Water', 'Air'])

    calculation_mode = st.radio("Calculate the...",
                                ["Rate of heat transfer (kW)", "Temperature difference (ΔT)", "Flow rate (l/s)"],
                                horizontal=True)

    # Inputs fields
    medium_temperature = st.slider('Medium temperature (°C)', min_value=1, max_value=100, value=20)
    pressure = st.number_input('Pressure (Pa)', min_value=0, value=101325)

    # Run function to get properties
    properties = get_medium_properties(transfer_medium, medium_temperature, pressure)

    if calculation_mode == "Rate of heat transfer (kW)":
        flow_rate = st.number_input("Enter flow rate (l/s):", value=1.0, min_value=0.0, step=0.1)
        delta_t = st.number_input("Enter temperature difference (°C):", value=6.0, min_value=0.0, step=0.1)
        heat_transfer = calculate_heat_transfer(flow_rate, properties['Specific Heat (kJ/kg·K)'], delta_t,
                                                properties['Density (kg/m³)'])
        st.success(f"Heat transfer: {heat_transfer:.2f} kW")

    elif calculation_mode == 'Temperature difference (ΔT)':
        flow_rate = st.number_input("Enter flow rate (l/s):", value=1.0, min_value=0.0, step=0.1)
        heat_transfer = st.number_input("Enter heat transfer (kW):", value=1.0, min_value=0.0, step=0.1)
        delta_t = calculate_deltaT(heat_transfer, flow_rate, properties['Specific Heat (kJ/kg·K)'],
                                   properties['Density (kg/m³)'])
        st.success(f"Temperature difference (ΔT): {delta_t:.2f} °C")

    elif calculation_mode == 'Flow rate (l/s)':
        heat_transfer = st.number_input("Enter heat transfer (kW):", value=1.0, min_value=0.0, step=0.1)
        delta_t = st.number_input("Enter temperature difference (°C):", value=6.0, min_value=0.0, step=0.1)
        flow_rate = calculate_flow_rate(delta_t, heat_transfer, properties['Specific Heat (kJ/kg·K)'],
                                        properties['Density (kg/m³)'])
        st.success(f"Mass flow rate: {flow_rate:.2f} l/s")

if tool_selection == 'Pyfluids':
    # Create a list of all available fluids from FluidsList
    fluids = [fluid for fluid in FluidsList]

    # Select fluid from dropdown (selectbox)
    fluid_selection = st.selectbox("Select a fluid", fluids)

    # Pressure input in Pascals (default to 101325 Pa)
    pressure = st.number_input('Pressure (Pa)', min_value=0, value=101325)

    # Temperature input (in Celsius) with a slider
    temperature = st.slider('Temperature (°C)', min_value=1, max_value=100, value=50)

    # Create the fluid instance based on the selected fluid
    fluid = Fluid(fluid_selection)

    # Update the fluid's state based on the input pressure and temperature
    fluid.update(Input.pressure(pressure), Input.temperature(temperature))

    # Display specific heat in kJ/kg·K
    st.markdown(f"**Specific Heat (kJ/kg·K)**: {fluid.specific_heat / 1000:.3f}")

    # Optionally, you can display other properties as well
    st.markdown(f"**Density (kg/m³)**: {fluid.density:.2f}")
    st.markdown(f"**Enthalpy (J/kg)**: {fluid.enthalpy:.2f}")
    st.markdown(f"**Entropy (J/kg·K)**: {fluid.entropy:.5f}")

