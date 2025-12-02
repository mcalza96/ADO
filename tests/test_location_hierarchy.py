import sys
import os
import unittest
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from domain.disposal.services.location_service import LocationService
from repositories.site_repository import SiteRepository
from repositories.plot_repository import PlotRepository
from domain.shared.entities.location import Site, Plot

TEST_DB_PATH = "tests/test_biosolids.db"

class TestLocationHierarchy(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize test DB
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        DatabaseManager.initialize_db(db_path=TEST_DB_PATH)
        
    @classmethod
    def tearDownClass(cls):
        # Clean up
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        self.db_manager = DatabaseManager(db_path=TEST_DB_PATH)
        self.site_repo = SiteRepository(self.db_manager)
        self.plot_repo = PlotRepository(self.db_manager)
        self.service = LocationService(self.site_repo, self.plot_repo)

    def test_create_site_and_plots(self):
        # 1. Create Site
        site = Site(
            id=None,
            name="Fundo El Roble",
            owner_name="Agricola Roble Ltda",
            region="RM"
        )
        saved_site = self.service.create_site(site)
        self.assertIsNotNone(saved_site.id)
        print(f"DEBUG: Created Site ID: {saved_site.id}")
        
        # 2. Create Plots
        plot1 = Plot(
            id=None,
            site_id=saved_site.id,
            name="Lote Norte",
            area_acres=50.5,
            geometry_wkt="POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))"
        )
        saved_plot1 = self.service.create_plot(plot1)
        self.assertIsNotNone(saved_plot1.id)
        print(f"DEBUG: Created Plot 1 ID: {saved_plot1.id} for Site {saved_plot1.site_id}")
        
        plot2 = Plot(
            id=None,
            site_id=saved_site.id,
            name="Lote Sur",
            area_acres=30.0
        )
        saved_plot2 = self.service.create_plot(plot2)
        self.assertIsNotNone(saved_plot2.id)
        print(f"DEBUG: Created Plot 2 ID: {saved_plot2.id}")
        
        # 3. Verify Hierarchy Loading
        # Without plots
        fetched_site = self.service.get_site(saved_site.id, include_plots=False)
        self.assertEqual(len(fetched_site.plots), 0)
        
        # With plots
        fetched_site_full = self.service.get_site(saved_site.id, include_plots=True)
        print(f"DEBUG: Fetched site plots: {fetched_site_full.plots}")
        
        # Verify directly from repo to isolate service/repo issue
        direct_plots = self.plot_repo.get_by_site_id(saved_site.id)
        print(f"DEBUG: Direct plots from repo: {direct_plots}")
        
        self.assertEqual(len(fetched_site_full.plots), 2)
        plot_names = [p.name for p in fetched_site_full.plots]
        self.assertIn("Lote Norte", plot_names)
        self.assertIn("Lote Sur", plot_names)

    def test_validations(self):
        # Setup site
        site = self.service.create_site(Site(id=None, name="Fundo Validaciones"))
        
        # 1. Negative Area
        with self.assertRaises(ValueError) as cm:
            self.service.create_plot(Plot(
                id=None, site_id=site.id, name="Bad Area", area_acres=-5
            ))
        # Check for 'área' or just '0 acres' to be safe against encoding/accents
        self.assertTrue("área" in str(cm.exception).lower() or "area" in str(cm.exception).lower())
        
        # 2. Duplicate Name
        self.service.create_plot(Plot(
            id=None, site_id=site.id, name="Unique Name", area_acres=10
        ))
        with self.assertRaises(ValueError) as cm:
            self.service.create_plot(Plot(
                id=None, site_id=site.id, name="Unique Name", area_acres=20
            ))
        self.assertIn("ya existe", str(cm.exception).lower())
        
        # 3. Invalid WKT
        with self.assertRaises(ValueError) as cm:
            self.service.create_plot(Plot(
                id=None, site_id=site.id, name="Bad WKT", area_acres=10,
                geometry_wkt="CIRCLE(0 0, 10)" # Not POLYGON
            ))
        self.assertIn("wkt", str(cm.exception).lower())

if __name__ == '__main__':
    unittest.main()
