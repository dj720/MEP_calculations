import unittest
from processing.public_health_processing import select_stack_option


# Unit test class
class TestSelectStackOption(unittest.TestCase):
    def test_primary_no_wc(self):
        # Test with primary method and no WC present
        result = select_stack_option(total_wastewater_flowrate=2.5, wc_present=False, vent_method='Primary')
        self.assertEqual(result, "primary 75mm")

    def test_primary_with_wc_skip_75mm(self):
        # Test with primary method and WC present (should skip 75mm)
        result = select_stack_option(total_wastewater_flowrate=2.5, wc_present=True, vent_method='Primary')
        self.assertEqual(result, "primary 100mm")

    def test_primary_above_all_primary_limits(self):
        # Test with primary method and flow rate above all limits
        result = select_stack_option(total_wastewater_flowrate=15.0, wc_present=True, vent_method='Primary')
        self.assertEqual(result, "there is no suitable stack option as the flow rate exceeds maximum limits, consider multiple stacks.")

    def test_secondary_no_wc(self):
        # Test with secondary method and no WC present
        result = select_stack_option(total_wastewater_flowrate=3.0, wc_present=False, vent_method='Secondary')
        self.assertEqual(result, "primary 75mm with 50mm secondary vent")

    def test_secondary_with_wc_skip_75mm_secondary(self):
        # Test with secondary method and WC present (should skip 75mm secondary option)
        result = select_stack_option(total_wastewater_flowrate=3.0, wc_present=True, vent_method='Secondary')
        self.assertEqual(result, "primary 100mm with 50mm secondary vent")

    def test_secondary_above_all_secondary_limits(self):
        # Test with secondary method and flow rate above all limits
        result = select_stack_option(total_wastewater_flowrate=20.0, wc_present=True, vent_method='Secondary')
        self.assertEqual(result, "there is no suitable stack option as the flow rate exceeds maximum limits, consider multiple stacks.")

    def test_flowrate_with_wc_primary(self):
        # Test a primary option where WC is present and a suitable larger size is found
        result = select_stack_option(total_wastewater_flowrate=5.0, wc_present=True, vent_method='Primary')
        self.assertEqual(result, "primary 100mm")

    def test_flowrate_with_wc_secondary(self):
        # Test a secondary option where WC is present and a suitable larger size is found
        result = select_stack_option(total_wastewater_flowrate=7.0, wc_present=True, vent_method='Secondary')
        self.assertEqual(result, "primary 100mm with 50mm secondary vent")
