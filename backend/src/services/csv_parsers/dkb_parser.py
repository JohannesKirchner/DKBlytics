"""DKB (Deutsche Kreditbank) CSV parser implementation."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import BinaryIO, Union, List, Optional

from .base import CSVParser, ParsedBankData
from ..bank_models import BankAccount, BankTransaction
from ...utils import ExternalServiceError


class DKBParser(CSVParser):
    """Parser for DKB CSV export files."""
    
    @property
    def name(self) -> str:
        return "dkb"
    
    @property  
    def bank_name(self) -> str:
        return "Deutsche Kreditbank (DKB)"
    
    def can_parse(self, file_content: str) -> bool:
        """Check if this looks like a DKB CSV file."""
        # DKB files start with account name and IBAN in quotes
        lines = file_content.strip().split('\n')
        if len(lines) < 5:
            return False
            
        # Look for DKB-specific patterns
        first_line = lines[0].strip()
        # Should be like: "Girokonto";"DEXXXXXXXX" or "Tagesgeld";"DEXXXXXXXX"
        if not (first_line.startswith('"') and ';"DE' in first_line):
            return False
            
        # Look for the expected column headers
        for line in lines[:10]:  # Check first 10 lines for headers
            if 'Buchungsdatum' in line and 'Zahlungsempfänger*in' in line and 'Betrag (€)' in line:
                return True
                
        return False
    
    def parse(self, file: Union[BinaryIO, str], holder_name: str = None) -> ParsedBankData:
        """Parse DKB CSV file.
        
        DKB CSV format:
        Line 1: "Account Name";"IBAN"
        Line 2: "Zeitraum:";"date range"  
        Line 3: "Kontostand vom date:";"amount €"
        Line 4: Empty
        Line 5: Column headers
        Line 6+: Transaction data
        """
        content = self._normalize_file_input(file)
        lines = content.strip().split('\n')
        
        if len(lines) < 6:
            raise ExternalServiceError("DKB CSV file too short - invalid format")
            
        # Parse account metadata from header
        account_name, iban = self._parse_account_header(lines[0])
        balance = self._parse_balance_line(lines[2])
        
        # Find and parse column headers
        header_line_idx = self._find_header_line(lines)
        if header_line_idx == -1:
            raise ExternalServiceError("Could not find transaction header line in CSV")
            
        headers = self._parse_csv_line(lines[header_line_idx])
        column_map = self._build_column_map(headers)
        
        # Parse transactions
        transactions = []
        for line_idx in range(header_line_idx + 1, len(lines)):
            line = lines[line_idx].strip()
            if not line:
                continue
                
            try:
                transaction = self._parse_transaction_line(line, column_map)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                # Log warning but continue with other transactions
                print(f"Warning: Could not parse transaction line {line_idx + 1}: {e}")
                continue
        
        if not transactions:
            raise ExternalServiceError("No valid transactions found in CSV file")
        
        # Create account object
        account = BankAccount(
            name=account_name,
            amount=balance,
            iban=iban,
            holder_name=holder_name or "Unknown"
        )
        
        return ParsedBankData(
            accounts=[account],
            transactions_per_account=[transactions]
        )
    
    def _parse_account_header(self, line: str) -> tuple[str, str]:
        """Parse first line: "Account Name";"IBAN" """
        parts = self._parse_csv_line(line)
        if len(parts) < 2:
            raise ExternalServiceError("Invalid account header line")
            
        account_name = parts[0].strip()
        iban = parts[1].strip()
        
        if not account_name or not iban:
            raise ExternalServiceError("Missing account name or IBAN in header")
            
        return account_name, iban
    
    def _parse_balance_line(self, line: str) -> Decimal:
        """Parse balance line: "Kontostand vom date:";"amount €" """
        parts = self._parse_csv_line(line)
        if len(parts) < 2:
            raise ExternalServiceError("Invalid balance line")
            
        balance_str = parts[1].strip()
        # Remove € symbol and convert German decimal format
        balance_str = balance_str.replace('€', '').replace('.', '').replace(',', '.').strip()
        
        try:
            return Decimal(balance_str)
        except (InvalidOperation, ValueError) as e:
            raise ExternalServiceError(f"Could not parse balance amount: {balance_str}") from e
    
    def _find_header_line(self, lines: List[str]) -> int:
        """Find the line containing transaction column headers."""
        for idx, line in enumerate(lines):
            if 'Buchungsdatum' in line and 'Betrag (€)' in line:
                return idx
        return -1
    
    def _build_column_map(self, headers: List[str]) -> dict[str, int]:
        """Map column names to indices."""
        column_map = {}
        
        # Required columns
        required_columns = {
            'date': 'Buchungsdatum',
            'peer': 'Zahlungsempfänger*in', 
            'purpose': 'Verwendungszweck',
            'amount': 'Betrag (€)',
        }
        
        # Optional columns
        optional_columns = {
            'reference': 'Kundenreferenz',
            'payer': 'Zahlungspflichtige*r'
        }
        
        # Map required columns
        for key, col_name in required_columns.items():
            try:
                column_map[key] = headers.index(col_name)
            except ValueError:
                raise ExternalServiceError(f"Missing required column: {col_name}")
        
        # Map optional columns
        for key, col_name in optional_columns.items():
            try:
                column_map[key] = headers.index(col_name)
            except ValueError:
                column_map[key] = None
                
        return column_map
    
    def _parse_transaction_line(self, line: str, column_map: dict[str, int]) -> Optional[BankTransaction]:
        """Parse a single transaction line."""
        parts = self._parse_csv_line(line)
        
        # Check if we have enough columns
        max_idx = max(idx for idx in column_map.values() if idx is not None)
        if len(parts) <= max_idx:
            return None
            
        try:
            # Extract transaction data
            date_str = parts[column_map['date']].strip()
            peer = parts[column_map['peer']].strip()
            purpose = parts[column_map['purpose']].strip()
            amount_str = parts[column_map['amount']].strip()
            
            # Optional fields
            reference = None
            if column_map.get('reference') is not None:
                reference = parts[column_map['reference']].strip() or None
            
            # Parse date (DD.MM.YY format)
            date_obj = self._parse_german_date(date_str)
            
            # Parse amount (German format: -1.234,56)
            amount = self._parse_german_amount(amount_str)
            
            # Combine purpose and peer for transaction text
            text = purpose if purpose else f"Transaction with {peer}"
            
            return BankTransaction(
                text=text,
                peer=peer,
                amount=amount,
                date=date_obj,
                customerreference=reference
            )
            
        except Exception as e:
            raise ExternalServiceError(f"Error parsing transaction: {e}")
    
    def _parse_csv_line(self, line: str) -> List[str]:
        """Parse a semicolon-delimited CSV line with proper quote handling."""
        # Use csv module to handle quoted fields properly
        reader = csv.reader([line], delimiter=';', quotechar='"')
        try:
            return next(reader)
        except StopIteration:
            return []
    
    def _parse_german_date(self, date_str: str) -> datetime:
        """Parse German date format DD.MM.YY or DD.MM.YYYY."""
        date_str = date_str.strip()
        
        # Try DD.MM.YYYY first
        for fmt in ['%d.%m.%y', '%d.%m.%Y']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        raise ExternalServiceError(f"Could not parse date: {date_str}")
    
    def _parse_german_amount(self, amount_str: str) -> Decimal:
        """Parse German amount format: -1.234,56"""
        amount_str = amount_str.strip()
        
        if not amount_str or amount_str == '0':
            return Decimal('0')
        
        # Remove thousands separators (dots) and convert decimal separator (comma to dot)
        # Handle negative amounts
        is_negative = amount_str.startswith('-')
        if is_negative:
            amount_str = amount_str[1:]
        
        # Convert German format to standard decimal format
        # Split by comma for decimal part
        if ',' in amount_str:
            integer_part, decimal_part = amount_str.rsplit(',', 1)
            # Remove dots from integer part (thousands separators)
            integer_part = integer_part.replace('.', '')
            amount_str = f"{integer_part}.{decimal_part}"
        else:
            # No decimal part, just remove dots
            amount_str = amount_str.replace('.', '')
        
        try:
            amount = Decimal(amount_str)
            return -amount if is_negative else amount
        except (InvalidOperation, ValueError) as e:
            raise ExternalServiceError(f"Could not parse amount: {amount_str}") from e