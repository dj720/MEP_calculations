import math
import matplotlib.pyplot as plt
from pyfluids import Fluid, FluidsList, Input
import numpy as np
from bokeh.plotting import figure
import psychrolib


def calculate_ach_volume(room_volume, volume_flow_rate):
    # Calculate the Air Changes Per Hour (ACH)
    ach = volume_flow_rate * 3600 / room_volume
    return ach


def calculate_volume_flow_rate(room_volume, air_changes_per_hour):
    # Calculate the required volume flow rate
    volume_flow_rate = room_volume * air_changes_per_hour / 3600
    return volume_flow_rate


def calculate_occupation_flow_rate(occupation, air_per_person):
    # Calculate the required volume flow rate based on room occupation
    occupation_flow_rate = occupation * air_per_person / 1000
    return occupation_flow_rate


### ACH AND VFR CALCULATIONS

def calculate_room_volume(floor_area, ceiling_height):
    room_volume = floor_area * ceiling_height
    return room_volume


############################### UNIT CONVERSION APP ##############################

# Conversion factors from one unit to another
conversion_factors = {
    'm³/h': {
        'm³/h': 1,
        'CFM': 0.588577,
        'l/s': 0.277778,
        'm³/s': 0.000278,
        'ft³/h': 35.3147
    },
    'CFM': {
        'm³/h': 1.699,
        'CFM': 1,
        'l/s': 0.471947,
        'm³/s': 0.000471947,
        'ft³/h': 60
    },
    'l/s': {
        'm³/h': 3.6,
        'CFM': 2.11888,
        'l/s': 1,
        'm³/s': 0.001,
        'ft³/h': 127.133
    },
    'm³/s': {
        'm³/h': 3600,
        'CFM': 2118.88,
        'l/s': 1000,
        'm³/s': 1,
        'ft³/h': 127133
    },
    'ft³/h': {
        'm³/h': 0.0283168,
        'CFM': 0.0166667,
        'l/s': 0.007867,
        'm³/s': 0.000007867,
        'ft³/h': 1
    }
}


def convert_airflow_rate(value, from_unit, to_unit):
    """
    Convert the airflow rate from one unit to another.
    
    Parameters:
    value (float): The airflow rate value to convert.
    from_unit (str): The unit of the input value.
    to_unit (str): The unit to convert to.
    
    Returns:
    float: The converted airflow rate value.
    """
    return value * conversion_factors[from_unit][to_unit]


######################################## DUCT TAB ##########################################

# Air calcs

def calculate_aspect_ratio(width_mm, height_mm):
    aspect_ratio = width_mm / height_mm
    if aspect_ratio < 1:
        aspect_ratio = 1 / aspect_ratio

    return aspect_ratio


def get_air_properties(air_temperature, pressure):
    fluid = Fluid(FluidsList.Air)

    # Update the fluid's state with the given temperature and pressure
    fluid.update(Input.pressure(pressure), Input.temperature(air_temperature))

    # Return key properties
    properties = {
        'Specific Heat (kJ/kg·K)': fluid.specific_heat / 1000,
        'Density (kg/m³)': fluid.density,
    }

    return properties


# Duct calcs

def calculate_duct_velocity(duct_area, air_volume):
    return air_volume / duct_area


def calculate_rect_duct_area(height_mm, width_mm):
    # includes conversion mm to m
    # Convert dimensions from millimeters to meters
    height_m = height_mm / 1000
    width_m = width_mm / 1000

    # Calculate the duct area
    duct_area_sqm = height_m * width_m

    # Calculate the equivalent diameter (hydraulic diameter) convert to mm
    eq_diameter_mm = math.sqrt(height_m * width_m / math.pi) * 2000
    return duct_area_sqm, eq_diameter_mm


def calculate_round_duct_area(diameter_mm):
    # includes conversion mm to m
    return math.pi * (diameter_mm / 2000) ** 2


def find_min_diameter(air_volume, max_duct_velocity):
    required_area = air_volume / max_duct_velocity
    diameter_mm = math.ceil(math.sqrt((4 * required_area) / math.pi) * 1000)  # Convert m to mm and round up
    return diameter_mm


def find_min_rect_size(air_volume, max_duct_velocity, max_dim_mm):
    required_area = air_volume / max_duct_velocity

    if max_dim_mm:  # If max width is specified
        max_dim_m = max_dim_mm / 1000  # Convert to meters
        height_m = required_area / max_dim_m
        height_mm = height_m * 1000  # Convert to mm and round up
        return max_dim_mm, height_mm

    else:  # No max width specified, return square size
        size_mm = math.ceil(math.sqrt(required_area) * 1000)  # Convert m to mm and round up
        return size_mm, size_mm


def calculate_pressure_loss(diameter_mm, air_density, air_velocity):
    """
    Calculate the pressure loss per meter in a duct.
    
    Parameters:
    friction_factor (float): The Darcy-Weisbach friction factor (dimensionless).
    duct_length (float): The length of the duct in meters (m).
    hydraulic_diameter (float): The hydraulic diameter of the duct in meters (m).
    air_density (float): The density of air in kilograms per cubic meter (kg/m³).
    air_velocity (float): The velocity of air in meters per second (m/s).
    
    Returns:
    float: The pressure loss in Pascals per meter (Pa/m).
    """
    diameter_m = diameter_mm / 1000  # convert to m
    friction_factor = 0.02  # Typical Darcy-Weisbach friction factor for ductwork
    pressure_loss = friction_factor * (air_density * air_velocity ** 2) / (2 * diameter_m)
    return pressure_loss


def plot_duct_cross_section(width_mm=None, height_mm=None, diameter_mm=None):
    """
    Function to plot the cross-sectional profile of a duct, either rectangular or round.
    
    Parameters:
    width_mm (float, optional): Width of the rectangular duct in millimeters.
    height_mm (float, optional): Height of the rectangular duct in millimeters.
    diameter_mm (float, optional): Diameter of the round duct in millimeters.
    """

    # Create a new figure and axis for the plot
    fig, ax = plt.subplots(figsize=(3, 3))

    fig.patch.set_alpha(0)  # Make the figure background transparent
    ax.set_facecolor('none')  # Make the axes background transparent

    # If diameter is passed, plot a round duct
    if diameter_mm:
        diameter_m = diameter_mm / 1000

        # Plot a circle representing the round duct cross-section
        circle = plt.Circle((0, 0), diameter_m / 2, linewidth=2, edgecolor='gray', facecolor='lightgray')
        ax.add_patch(circle)
        ax.set_title(f'Round Duct Cross-Section: {diameter_mm:.0f}mm Diameter', color='white')
        # Add dimension text (diameter)
        ax.text(0, -diameter_m / 2 - 0.05, f"Ø {diameter_mm:.0f} mm", ha='center', va='top', fontsize=12, color='white')

        # Set limits and aspect ratio
        ax.set_xlim(-diameter_m / 2 - 0.1, diameter_m / 2 + 0.1)
        ax.set_ylim(-diameter_m / 2 - 0.1, diameter_m / 2 + 0.1)

    # If width and height are passed, plot a rectangular duct
    elif width_mm and height_mm:
        width_m = width_mm / 1000
        height_m = height_mm / 1000

        # Plot a rectangle representing the rectangular duct cross-section
        rect = plt.Rectangle((-width_m / 2, -height_m / 2), width_m, height_m, linewidth=2, edgecolor='gray',
                             facecolor='lightgray')
        ax.add_patch(rect)
        ax.set_title(f'Rectangular Duct Cross-Section: {width_mm:.0f}mm x {height_mm:.0f}mm', color='white')
        # Add dimension text (width and height, swapped labels)
        ax.text(0, -height_m / 2 - 0.05, f"{width_mm:.0f} mm", ha='center', va='top', fontsize=12,
                color='white')  # Width label
        ax.text(width_m / 2 + 0.05, 0, f"{height_mm:.0f} mm", ha='left', va='center', fontsize=12, rotation=90,
                color='white')  # Height label

        # Set limits and aspect ratio
        ax.set_xlim(-width_m / 2 - 0.1, width_m / 2 + 0.1)
        ax.set_ylim(-height_m / 2 - 0.1, height_m / 2 + 0.1)

    # If neither diameter nor width/height are provided, raise an error
    else:
        print("Either diameter or both width and height must be provided.")
        return

    # Remove axes, ticks, and labels
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal', 'box')
    ax.axis('off')

    return fig


def plot_psychrometric(pressure, t_range, rh_range, twb_range, y_max):
    # Temperature and humidity ranges
    t_array = np.arange(t_range[0], t_range[1], 0.1)
    rh_array = np.arange(rh_range[0] / 100, (rh_range[1] + 0.1) / 100, 0.1)
    twb_array = np.arange(twb_range[0], twb_range[1] + 5, 5)

    # Create Bokeh figure
    p = figure(width=800, height=600, x_range=(t_range[0], t_range[1]), y_range=(0, y_max),
               title='Psychrometric Chart')
    p.xaxis.axis_label = "Dry-bulb Temperature [°C]"
    p.yaxis.axis_label = "Humidity Ratio [$kg_{water}/kg_{dry air}$]"

    # Set unit system to SI
    psychrolib.SetUnitSystem(psychrolib.SI)

    # Plot constant relative humidity lines
    for rh in rh_array:
        hr_array = []
        for t in t_array:
            hr = psychrolib.GetHumRatioFromRelHum(t, rh, pressure)
            hr_array.append(hr)
        p.line(t_array, hr_array, line_color="black", legend_label='Relative humidity')

    # Plot constant wet-bulb temperature lines
    for twb in twb_array:
        hr_array = []
        t_plot_array = []
        for t in t_array:
            if twb <= t:
                hr = psychrolib.GetHumRatioFromTWetBulb(t, twb, pressure)
                hr_array.append(hr)
                t_plot_array.append(t)
        p.line(t_plot_array, hr_array, line_color="red", legend_label='Wet-bulb temperature')

    return p


