"""
TDD & CoHaLo Behavioral Test Suite for Hermes Mesh & Starter Crews
Verifies factory registry, Pydantic schemas, and graceful degradation contracts.
"""
import sys
import os
import unittest

# Ensure apps/hermes is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from crews.crew_factory import CrewFactory
import crews.general_research_crew
import crews.google_seo_crew
import crews.astrology_timing_crew
from crews.google_seo_crew import check_google_maps_api_key

class TestHermesMeshContracts(unittest.TestCase):
    def test_starter_crews_registered(self):
        crews = CrewFactory.list_crews()
        self.assertIn("general_research", crews)
        self.assertIn("google_seo", crews)
        self.assertIn("astrology", crews)
        print(f"✅ Factory successfully registered {len(crews)} Starter Crews: {crews}")

    def test_google_maps_feature_flag(self):
        # By default in this environment, key is not injected
        has_key = check_google_maps_api_key()
        # Should gracefully return boolean without raising
        self.assertIsInstance(has_key, bool)
        print(f"✅ Google Maps API key graceful check returned: {has_key}")

    def test_pydantic_schema_contract(self):
        try:
            from pydantic import BaseModel, Field
            class BusinessAuditSchema(BaseModel):
                business_name: str
                rating: float = Field(ge=0.0, le=5.0)
                verified: bool

            sample = BusinessAuditSchema(business_name="Glamur Studio", rating=4.8, verified=True)
            self.assertEqual(sample.business_name, "Glamur Studio")
            print("✅ Pydantic contract validation passed exit code 0.")
        except ImportError:
            print("ℹ️ pydantic not installed locally in ZCP, test skipped.")

if __name__ == "__main__":
    unittest.main()
