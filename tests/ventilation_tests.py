import unittest
import math

from processing.ventilation_processing import (calculate_ach_volume,
                                                      calculate_occupation_flow_rate,
                                                      calculate_volume_flow_rate,
                                                      convert_airflow_rate,
                                                      calculate_duct_velocity,
                                                      calculate_rect_duct_area,
                                                      calculate_round_duct_area,
                                                      find_min_diameter,
                                                      find_min_rect_size,
                                                      calculate_pressure_loss)


class TestAirChangeCalculations(unittest.TestCase):

    def test_calculate_ach_volume(self):
        room_volume = 150  # in meters cubed
        volume_flow_rate = 0.5  # in cubic meters per second
        expected_ach = 12  # Calculated as (0.5 * 3600) / (150)
        result = calculate_ach_volume(room_volume, volume_flow_rate)
        self.assertEqual(result, expected_ach)

    def test_calculate_volume_flow_rate(self):
        room_volume = 150  # in meters cubed
        air_changes_per_hour = 12
        expected_volume_flow_rate = 0.5  # Calculated as (150 * 12) / 3600
        result = calculate_volume_flow_rate(room_volume, air_changes_per_hour)
        self.assertAlmostEqual(result, expected_volume_flow_rate, places=2)

    def test_calculate_occupation_flow_rate(self):
        occupation = 10  # number of people
        air_per_person = 20  # in liters per second per person
        expected_occupation_flow_rate = 0.2  # Calculated as (10 * 20) / 1000
        result = calculate_occupation_flow_rate(occupation, air_per_person)
        self.assertAlmostEqual(result, expected_occupation_flow_rate, places=2)

    def test_convert_airflow_rate(self):
        value = 100  # Example value in the original unit
        from_unit = 'm³/h'
        to_unit = 'CFM'
        expected_value = 58.8577  # Conversion using the conversion factor
        result = convert_airflow_rate(value, from_unit, to_unit)
        self.assertAlmostEqual(result, expected_value, places=4)

        # Test conversion in reverse
        from_unit = 'CFM'
        to_unit = 'm³/h'
        expected_value = 169.9
        result = convert_airflow_rate(100, from_unit, to_unit)
        self.assertAlmostEqual(result, expected_value, places=1)


# Unit Test Class
class TestDuctCalculations(unittest.TestCase):

    def test_calculate_duct_velocity(self):
        duct_area = 0.25  # in square meters
        air_volume = 1.0  # in cubic meters per second
        expected_velocity = 4.0
        self.assertAlmostEqual(calculate_duct_velocity(duct_area, air_volume), expected_velocity, places=2)

    def test_calculate_rect_duct_area(self):
        height_mm = 500
        width_mm = 400
        duct_area_sqm, eq_diameter_mm = calculate_rect_duct_area(height_mm, width_mm)
        expected_area = (height_mm / 1000) * (width_mm / 1000)
        expected_diameter = math.sqrt((height_mm / 1000) * (width_mm / 1000) / math.pi) * 2000
        self.assertAlmostEqual(duct_area_sqm, expected_area, places=4)
        self.assertAlmostEqual(eq_diameter_mm, expected_diameter, places=2)

    def test_calculate_round_duct_area(self):
        diameter_mm = 300
        expected_area = math.pi * (diameter_mm / 2000) ** 2
        self.assertAlmostEqual(calculate_round_duct_area(diameter_mm), expected_area, places=4)

    def test_find_min_diameter(self):
        air_volume = 2.0  # cubic meters per second
        max_duct_velocity = 4.0  # meters per second
        required_area = air_volume / max_duct_velocity
        expected_diameter = math.ceil(math.sqrt((4 * required_area) / math.pi) * 1000)
        self.assertEqual(find_min_diameter(air_volume, max_duct_velocity), expected_diameter)

    def test_find_min_rect_size_with_max_dim(self):
        air_volume = 2.0  # cubic meters per second
        max_duct_velocity = 4.0  # meters per second
        max_dim_mm = 800  # limit for the larger dimension in mm
        required_area = air_volume / max_duct_velocity
        max_dim_m = max_dim_mm / 1000
        height_m = required_area / max_dim_m
        expected_height_mm = height_m * 1000
        self.assertAlmostEqual(find_min_rect_size(air_volume, max_duct_velocity, max_dim_mm),
                               (max_dim_mm, expected_height_mm), places=2)

    def test_find_min_rect_size_square(self):
        air_volume = 2.0  # cubic meters per second
        max_duct_velocity = 4.0  # meters per second
        required_area = air_volume / max_duct_velocity
        expected_size_mm = math.ceil(math.sqrt(required_area) * 1000)
        self.assertEqual(find_min_rect_size(air_volume, max_duct_velocity, None),
                         (expected_size_mm, expected_size_mm))

    def test_calculate_pressure_loss(self):
        diameter_mm = 300  # duct diameter in mm
        air_density = 1.2  # density in kg/m³
        air_velocity = 5.0  # velocity in m/s
        diameter_m = diameter_mm / 1000
        friction_factor = 0.02
        expected_pressure_loss = friction_factor * (air_density * air_velocity ** 2) / (2 * diameter_m)
        self.assertAlmostEqual(calculate_pressure_loss(diameter_mm, air_density, air_velocity),
                               expected_pressure_loss, places=4)
