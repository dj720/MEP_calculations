import unittest

from processing.heating_processing import (calculate_reheat_time,
                                                  calculate_coil_size,
                                                  calculate_primary_flowrate,
                                                  calculate_heat_transfer,
                                                  calculate_deltaT,
                                                  calculate_flow_rate)


class TestCalculateCalorifierCalculations(unittest.TestCase):
    def test_reheat_time_calculation(self):
        # Test with known values
        initial_temperature = 20
        final_temperature = 80
        vessel_volume = 1000
        coil_size = 10
        expected_reheat_time = 418  # Calculate expected value manually
        self.assertAlmostEqual(calculate_reheat_time(initial_temperature, final_temperature, vessel_volume, coil_size),
                               expected_reheat_time, delta=0.1)

        # Test with zero initial temperature
        initial_temperature = 0
        final_temperature = 100
        vessel_volume = 500
        coil_size = 5
        expected_reheat_time = 696.6666  # Calculate expected value manually
        self.assertAlmostEqual(calculate_reheat_time(initial_temperature, final_temperature, vessel_volume, coil_size),
                               expected_reheat_time, delta=0.1)

    def test_reheat_time_with_zero_coil_size(self):
        # Test with zero coil size
        initial_temperature = 20
        final_temperature = 80
        vessel_volume = 1000
        coil_size = 0
        # This should raise a ZeroDivisionError
        with self.assertRaises(ZeroDivisionError):
            calculate_reheat_time(initial_temperature, final_temperature, vessel_volume, coil_size)

    def test_coil_size_calculation(self):
        # Test with known values
        initial_temperature = 20
        final_temperature = 80
        vessel_volume = 1000
        reheat_time = 25
        expected_coil_size = 167.2  # Calculate expected value manually 167.2
        self.assertAlmostEqual(calculate_coil_size(initial_temperature, final_temperature, vessel_volume, reheat_time),
                               expected_coil_size, delta=0.1)

        # Test with zero initial temperature
        initial_temperature = 0
        final_temperature = 100
        vessel_volume = 500
        reheat_time = 20
        expected_coil_size = 174.166666  # Calculate expected value manually 174.16
        self.assertAlmostEqual(calculate_coil_size(initial_temperature, final_temperature, vessel_volume, reheat_time),
                               expected_coil_size, delta=0.1)

    def test_coil_size_with_zero_reheat_time(self):
        # Test with zero reheat time
        initial_temperature = 20
        final_temperature = 80
        vessel_volume = 1000
        reheat_time = 0
        # This should raise a ZeroDivisionError
        with self.assertRaises(ZeroDivisionError):
            calculate_coil_size(initial_temperature, final_temperature, vessel_volume, reheat_time)

    def test_flowrate_calculation(self):
        # Test with known values
        primary_flow_temp = 60
        primary_return_temp = 40
        coil_size = 50
        expected_flowrate = 0.598
        self.assertAlmostEqual(calculate_primary_flowrate(primary_flow_temp, primary_return_temp, coil_size),
                               expected_flowrate, delta=0.1)


class TestEVCalculations(unittest.TestCase):

    def test_calculate_CFP(self):
        from processing.building_services.heating import calculate_CFP  # Replace with actual import
        static_head = 5  # Example static head value
        expected_CFP = 0.35 + 5 * 0.1 + 1  # exclude_air + static_head*0.1 + gauge_to_absolute
        result = calculate_CFP(static_head)
        self.assertAlmostEqual(result, expected_CFP, delta=0.1)

    def text_calculate_max_system_pressure(self):
        from processing.building_services.heating import calculate_max_system_pressure
        lowest_WP = 3  # Lowest working pressure
        SV_margin = 0.5  # Safety valve margin
        result = calculate_max_system_pressure(lowest_WP, SV_margin)
        expected_max_system_pressure_abs = lowest_WP - SV_margin + 1  # lowest_WP - SV_margin + gauge_to_absolute
        self.assertAlmostEqual(result, expected_max_system_pressure_abs, delta=0.1)

    def test_calculate_acceptance_factor(self):
        from processing.building_services.heating import calculate_acceptance_factor  # Replace with actual import
        CFP = 1.5  # Cold fill pressure
        max_system_pressure_barabs = 1
        expected_vessel_acceptance = (max_system_pressure_barabs - CFP) / max_system_pressure_barabs
        result = calculate_acceptance_factor(CFP, max_system_pressure_barabs)
        self.assertAlmostEqual(result, expected_vessel_acceptance, delta=0.1)

    def test_calculate_EV_size(self):
        from processing.building_services.heating import calculate_EV_size  # Replace with actual import
        system_volume = 100  # Example system volume
        expansion_factor = 1.2  # Example expansion factor
        vessel_acceptance = 0.3  # Example vessel acceptance
        safety_factor = 1.1  # Safety factor in the function
        expected_EV_size = system_volume * (expansion_factor / vessel_acceptance) * safety_factor
        result = calculate_EV_size(system_volume, expansion_factor, vessel_acceptance)
        self.assertAlmostEqual(result, expected_EV_size, delta=0.1)


# Function Definitions for Testing
def get_heating_conversion_factors():
    to_joules = {
        'BTU': 1055.06,
        'calories': 4.184,
        'joules': 1,
        'kWh': 3.6e6
    }
    return to_joules


def convert_heating_units(from_unit, to_unit, amount):
    to_joules = get_heating_conversion_factors()
    amount_in_joules = amount * to_joules[from_unit]
    result = amount_in_joules / to_joules[to_unit]
    result_rounded = round(result, 3)
    return result_rounded


# Unit Test Class
class TestHeatingConversion(unittest.TestCase):

    def test_get_heating_conversion_factors(self):
        factors = get_heating_conversion_factors()
        self.assertEqual(factors['BTU'], 1055.06)
        self.assertEqual(factors['calories'], 4.184)
        self.assertEqual(factors['joules'], 1)
        self.assertEqual(factors['kWh'], 3.6e6)

    def test_convert_heating_units_same_unit(self):
        # Test conversion when from_unit and to_unit are the same
        self.assertEqual(convert_heating_units('joules', 'joules', 100), 100)
        self.assertEqual(convert_heating_units('BTU', 'BTU', 50), 50)

    def test_convert_heating_units_joules_to_kWh(self):
        # Convert from joules to kWh
        result = convert_heating_units('joules', 'kWh', 3600000)
        self.assertAlmostEqual(result, 1.0, places=3)

    def test_convert_heating_units_kWh_to_BTU(self):
        # Convert from kWh to BTU
        result = convert_heating_units('kWh', 'BTU', 1)
        expected_result = 3.6e6 / 1055.06
        self.assertAlmostEqual(result, expected_result, places=3)

    def test_convert_heating_units_calories_to_BTU(self):
        # Convert from calories to BTU
        result = convert_heating_units('calories', 'BTU', 100)
        expected_result = (100 * 4.184) / 1055.06
        self.assertAlmostEqual(result, expected_result, places=3)


# Unit Test Class
class TestThermalCalculations(unittest.TestCase):

    def test_calculate_heat_transfer(self):
        # Known inputs and expected output
        flow_rate = 2.0  # m³/s
        cp_metric = 4.18  # kJ/kg°C (specific heat capacity of water)
        delta_t = 10.0  # °C
        density = 1000  # kg/m³ (density of water)

        # Expected heat transfer in kW
        expected_heat_transfer = flow_rate * density * cp_metric * delta_t / 1000
        self.assertAlmostEqual(calculate_heat_transfer(flow_rate, cp_metric, delta_t, density),
                               expected_heat_transfer, places=2)

    def test_calculate_deltaT(self):
        # Known inputs and expected output
        heat_transfer = 83.6  # kW
        flow_rate = 2.0  # m³/s
        cp_metric = 4.18  # kJ/kg°C (specific heat capacity of water)
        density = 1000  # kg/m³ (density of water)

        # Calculate expected delta T
        mass_flow_rate = flow_rate * density
        expected_delta_t = (heat_transfer * 1000) / (mass_flow_rate * cp_metric)  # °C
        self.assertAlmostEqual(calculate_deltaT(heat_transfer, flow_rate, cp_metric, density),
                               expected_delta_t, places=2)

    def test_calculate_flow_rate(self):
        # Known inputs and expected output
        delta_t = 10.0  # °C
        heat_transfer = 83.6  # kW
        cp_metric = 4.18  # kJ/kg°C (specific heat capacity of water)
        density = 1000  # kg/m³ (density of water)

        # Calculate expected flow rate
        expected_mass_flow_rate = heat_transfer / (cp_metric * delta_t / 1000)  # kg/s
        expected_flow_rate = expected_mass_flow_rate / density  # m³/s
        self.assertAlmostEqual(calculate_flow_rate(delta_t, heat_transfer, cp_metric, density),
                               expected_flow_rate, places=2)
