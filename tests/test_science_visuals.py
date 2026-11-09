"""Smoke tests for scientific scene classification and output helpers."""
import unittest
from science_visuals import classify, wrap

class ScienceVisualTests(unittest.TestCase):
    def test_protein(self):
        self.assertEqual(classify("Amino acids support muscle protein synthesis"), "protein")
    def test_energy(self):
        self.assertEqual(classify("Calorie deficit and fat loss"), "energy")
    def test_hydration(self):
        self.assertEqual(classify("Water and hydration improve performance"), "hydration")
    def test_fallback(self):
        self.assertEqual(classify("A useful habit"), "generic")

if __name__ == "__main__": unittest.main()
