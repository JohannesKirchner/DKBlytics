"""
Bank integration endpoint — test CSV import functionality.
"""

from pathlib import Path
import pytest


@pytest.mark.order(40)
def test_csv_import_endpoint_exists(client):
    """Test that the CSV import endpoint is available."""
    # Test with missing file should return 422 (validation error)
    r = client.post("/api/bank/import_csv")
    assert r.status_code == 422  # FastAPI validation error for missing required fields
