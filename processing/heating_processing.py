from fpdf import FPDF
import getpass
import datetime
from datetime import datetime
import csv
import numpy as np
from fluids.friction import friction_factor
from fluids.core import Reynolds
import CoolProp.CoolProp as CP
from io import BytesIO
import pandas as pd


#### Calculations ####

def calculate_reheat_time(initial_temperature, final_temperature, vessel_volume, coil_size):
    delta_temperature = final_temperature - initial_temperature
    reheat_time = (vessel_volume * delta_temperature * 4.18) / (60 * coil_size)
    return reheat_time


def calculate_coil_size(initial_temperature, final_temperature, vessel_volume, reheat_time):
    delta_temperature = final_temperature - initial_temperature
    coil_size = (vessel_volume * delta_temperature * 4.18) / (60 * reheat_time)
    return coil_size


def calculate_primary_flowrate(primary_flow_temp, primary_return_temp, coil_size):
    primary_delta_temperature = primary_flow_temp - primary_return_temp
    primary_flowrate = coil_size / (4.18 * primary_delta_temperature)
    return primary_flowrate


#### PDF ####

def create_resultsheet(initial_temperature, final_temperature, coil_size, vessel_volume, reheat_time, calculation_type,
                       engineers_notes, include_primary, primary_flow_temp, primary_return_temp, primary_flowrate):
    def add_variables(pdf):
        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(200, 10, txt="1. Variables", ln=True, align='L')
        pdf.ln(5)
        pdf.set_font("Arial", size=12)

        # data for all calculations
        variables = {
            "> Initial Temperature (°C)": initial_temperature,
            "> Final Temperature (°C)": final_temperature,
            "> Coil Size (kW)": coil_size,
            "> Vessel Volume (litres)": vessel_volume,
            "> Reheat Time (min)": reheat_time
        }
        # add primary data if required
        if include_primary:
            # data if primary is included
            primary_data = {
                '> Primary Flow Temperature (°C)': primary_flow_temp,
                '> Primary Return Temperature (°C)': primary_return_temp,
                '> Primary Flow Rate (kg/s)': primary_flowrate
            }
            variables.update(primary_data)

        # print dictionary 
        for key, value in variables.items():
            pdf.cell(0, 10, txt=f"{key}: {value:.4g}", ln=True)
        pdf.ln(5)

        # Include engineers notes
        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(200, 10, txt="2. Engineers Notes", ln=True, align='L')
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        if engineers_notes == '':
            pdf.cell(200, 10, txt='N/A')
        else:
            pdf.multi_cell(0, 10, txt=engineers_notes)

    def add_calculations(pdf):
        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(200, 10, txt="3. Calculations", ln=True, align='L')
        pdf.ln(10)

        # Add relevant calculation based on selection
        if calculation_type == "Reheat Time":
            pdf.image("data/Building Services/calorifier-reheat/reheat_time_latex_exp1.png", x=55, y=50, w=100)
        else:
            pdf.image("data/Building Services/calorifier-reheat/reheat_rating_latex_exp1.png", x=55, y=50, w=100)
        if include_primary:
            pdf.image("data/Building Services/calorifier-reheat/primary_flowrate_latex_exp1.png", x=55, y=225, w=100)

    def add_schematic(pdf):
        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(200, 10, txt="4. Schematic", ln=True, align='L')
        pdf.ln(10)
        pdf.image('data/Building Services/calorifier-reheat/Calorifier_schematic.png', x=30, y=50, w=150)

    # Initialize PDF
    pdf = MyPDF()
    pdf.alias_nb_pages()  # This is required to get the total number of pages

    # Page 1 - variables and notes
    pdf.add_page()
    add_variables(pdf)

    # Page 2 - derivation
    pdf.add_page()
    add_calculations(pdf)

    # Page 3 - schematic
    pdf.add_page()
    add_schematic(pdf)

    # Write PDF to memory
    pdf_bytes = pdf.output(dest="S").encode(
        "latin-1")  #https://discuss.streamlit.io/t/creating-a-pdf-file-generator/7613/2

    return pdf_bytes


class MyPDF(FPDF):
    def header(self):
        # Rendering logo (this is the slow bit :( !!!!!):
        self.image('data/Building Services/calorifier-reheat/wsp_cmyk-01-reduced1.png', x=10, y=10, w=33)
        self.set_font("Arial", "B", 15)
        # Moving cursor to the right:
        self.cell(80)
        # Printing title:
        self.cell(30, 10, "Calorifier Calculation Sheet", border=0, ln=1, align="C")
        self.ln(2)
        self.line(x1=10, y1=30, y2=30, x2=200)
        self.ln(15)

    def footer(self):
        # Position cursor at 1.5 cm from bottom:
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        # Printing page number, date, user:
        self.cell(0, 10,
                  f"Page {self.page_no()}/{{nb}} | Generated by: {getpass.getuser()} | Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Tool developed by the Cambridge MEP team",
                  0, 0, 'C')


###################### Expansion #############################

def calculate_expansion_factor(max_temperature):
    # Read the data from the CSV file
    with open('data/Expansion_data.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)

    # Convert the data to lists for easier manipulation
    temperatures = [float(row['Temperature']) for row in data]
    expansion_factors = [float(row['Expansion Factor']) for row in data]

    # Check if the temperature is in the data
    if max_temperature in temperatures:
        index = temperatures.index(max_temperature)
        expansion_factor = expansion_factors[index]
        return expansion_factor
    else:
        # If the temperature is not in the data, interpolate the data of the two nearest points
        idx = np.searchsorted(temperatures, max_temperature)
        if idx == 0:
            # If temperature is below the lowest temperature in the data
            idx = 1
        elif idx == len(temperatures):
            # If temperature is above the highest temperature in the data
            idx = len(temperatures) - 1

        # Perform linear interpolation
        t1 = temperatures[idx - 1]
        t2 = temperatures[idx]
        f1 = expansion_factors[idx - 1]
        f2 = expansion_factors[idx]
        expansion_factor = f1 + ((f2 - f1) / (t2 - t1)) * (max_temperature - t1)
        return expansion_factor


def calculate_CFP(static_head):
    exclude_air = 0.35
    gauge_to_absolute = 1
    static_head_barg = static_head * 0.1
    cold_fill_pressure = exclude_air + static_head_barg + gauge_to_absolute
    return cold_fill_pressure


def calculate_max_system_pressure(lowest_WP, SV_margin):
    gauge_to_absolute = 1
    max_system_pressure_barabs = lowest_WP - SV_margin + gauge_to_absolute
    return max_system_pressure_barabs


def calculate_acceptance_factor(CFP, max_system_pressure_barabs):
    vessel_acceptance = (max_system_pressure_barabs - CFP) / max_system_pressure_barabs
    return vessel_acceptance


def calculate_EV_size(system_volume, expansion_factor, vessel_acceptance):
    safety_factor = 1.1
    EV_size = system_volume * (expansion_factor / vessel_acceptance) * safety_factor
    return EV_size


###################### Unit converter #############################

def get_heating_conversion_factors():
    # Store conversion factors relative to a base unit (e.g., joules)
    to_joules = {
        'BTU': 1055.06,
        'calories': 4.184,
        'joules': 1,
        'kWh': 3.6e6
    }
    return to_joules


###################### Heat flow #############################


def calculate_heat_transfer(flow_rate, cp_metric, delta_t, density):
    mass_flow_rate = flow_rate * density
    heat_transfer = mass_flow_rate * cp_metric * delta_t / 1000  # kW
    return heat_transfer


def calculate_deltaT(heat_transfer, flow_rate, cp_metric, density):
    mass_flow_rate = flow_rate * density
    delta_t = (heat_transfer * 1000) / (mass_flow_rate * cp_metric)  # °C
    return delta_t


def calculate_flow_rate(delta_t, heat_transfer, cp_metric, density):
    mass_flow_rate = heat_transfer / (cp_metric * delta_t / 1000)
    flow_rate = mass_flow_rate / density
    return flow_rate


###################### CIBSE pipe sizing #############################


def convert_df_to_excel(df):
    """Function to convert DataFrame to Excel"""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Pipe Data')
    writer._save()
    processed_data = output.getvalue()
    return processed_data


def calculate_reynolds_number(velocity, int_diameter, fluid_density, fluid_viscosity):
    """Calculate Reynolds number using the Fluids library"""
    return Reynolds(V=velocity, D=int_diameter, rho=fluid_density, mu=fluid_viscosity)


def calculate_darcy_friction_factor(reynolds_number, eq_roughness, int_diameter):  # int_diameter
    """Calculate Darcy friction factor using the Fluids library (Colebrook-White)"""
    return friction_factor(Re=reynolds_number, eD=eq_roughness / int_diameter)  #/int_diameter


def calculate_pressure_drop_per_meter(friction_factor, density, velocity, diameter):
    """Calculate pressure drop per meter using Darcy-Weisbach equation"""
    return (friction_factor * density * velocity ** 2) / (2 * diameter)


def get_glycol_water_properties(glycol_percentage, temperature, pressure=101325):
    """
    Returns the density and dynamic viscosity of a water-ethylene glycol mixture.
    glycol_percentage: Fraction of glycol (0 to 1).
    temperature: Temperature in Celsius.
    pressure: Pressure in Pascals.
    """
    # Convert glycol percentage to an integer percentage for the CoolProp identifier
    glycol_percentage_int = int(glycol_percentage * 100)

    # Define the fluid name in CoolProp for ethylene glycol-water mixture with the specified concentration
    fluid_name = f"INCOMP::MEG-{glycol_percentage_int}%"  # e.g., "INCOMP::MEG-30%"

    # Convert temperature to Kelvin
    temperature_K = temperature + 273.15

    # Calculate density and dynamic viscosity using CoolProp
    density = CP.PropsSI('D', 'T', temperature_K, 'P', pressure, fluid_name)  # Density in kg/m³
    viscosity = CP.PropsSI('V', 'T', temperature_K, 'P', pressure, fluid_name)  # Dynamic viscosity in Pa.s

    return density, viscosity
