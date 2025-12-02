import sys
from unittest.mock import MagicMock

# Mock streamlit before importing container
st_mock = MagicMock()
def pass_through(func):
    return func
st_mock.cache_resource = pass_through
sys.modules['streamlit'] = st_mock

sys.modules['pandas'] = MagicMock()
sys.modules['plotly'] = MagicMock()
sys.modules['plotly.express'] = MagicMock()
sys.modules['fpdf'] = MagicMock()
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.pdfgen'] = MagicMock()
sys.modules['reportlab.pdfgen.canvas'] = MagicMock()

# Now we can import scripts
import scripts.seed_ui_demo
import tests.test_ui_logic
