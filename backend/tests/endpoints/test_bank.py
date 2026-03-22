"""
Bank integration endpoint — test CSV import functionality.
"""

from decimal import Decimal
from pathlib import Path
import io
import pytest

from src.services.csv_parsers import parse_csv_file


@pytest.mark.order(40)
def test_csv_import_endpoint_exists(client):
    """Test that the CSV import endpoint is available."""
    # Test with missing file should return 422 (validation error)
    r = client.post("/api/bank/import_csv")
    assert r.status_code == 422  # FastAPI validation error for missing required fields


@pytest.mark.order(41)
def test_dkb_csv_parsing():
    """Test that DKB CSV files are parsed correctly without database interaction."""
    # Mock DKB CSV content (anonymized, inline)
    with open(Path(__file__).parent / "../mock_data/bank/mock_dkb.csv") as f:
        parsed_data = parse_csv_file(f, "dkb", "TEST HOLDER")
    
    # Verify account data
    assert len(parsed_data.accounts) == 1
    account = parsed_data.accounts[0]
    assert account.holder_name == "TEST HOLDER"
    assert account.name == "Girokonto"
    assert account.amount == Decimal("-1234.56")  # Balance from header
    assert account.iban == "MOCK_IBAN_GIROKONTO"  # Mock IBAN from CSV header
    
    # Verify transaction data
    assert len(parsed_data.transactions_per_account) == 1
    transactions = parsed_data.transactions_per_account[0]
    assert len(transactions) == 5
    
    # Test first transaction (Gehalt/Rente)
    t1 = transactions[0]
    assert t1.text == "Gehalt Januar 2025"
    assert t1.peer == "MOCK COMPANY GMBH"
    assert t1.amount == Decimal("-2500.00")  # Income is negative in DKB format
    assert str(t1.date) == "2025-01-10"
    assert t1.customerreference is None
    
    # Test second transaction (Lastschrift with customer reference)
    t2 = transactions[1]
    assert t2.text == "Einkauf 07.01.25 MOCK CITY"
    assert t2.peer == "MOCK SUPERMARKET"
    assert t2.amount == Decimal("45.67")  # Expense is positive
    assert str(t2.date) == "2025-01-08"
    assert t2.customerreference == "MOCK-REF-123"
    
    # Test third transaction (Überweisung)
    t3 = transactions[2]
    assert t3.text == "Miete Wohnung Januar"
    assert t3.peer == "MAX MUSTERMANN"
    assert t3.amount == Decimal("800.00")
    assert str(t3.date) == "2025-01-05"
    
    # Verify all transactions are properly ordered (newest first, as they appear in CSV)
    dates = [t.date for t in transactions]
    assert dates == sorted(dates, reverse=True)
