"""Base classes and interfaces for CSV bank statement parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, List, Union

# Import existing bank data models
from ..bank_models import BankAccount, BankTransaction


@dataclass(frozen=True)
class ParsedBankData:
    """Container for parsed bank statement data."""
    
    accounts: List[BankAccount]
    transactions_per_account: List[List[BankTransaction]]
    
    def __post_init__(self):
        if len(self.accounts) != len(self.transactions_per_account):
            raise ValueError("Mismatched number of accounts and transaction lists")


class CSVParser(ABC):
    """Abstract base class for CSV bank statement parsers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this parser."""
        pass
    
    @property
    @abstractmethod
    def bank_name(self) -> str:
        """Human-readable bank name."""
        pass
    
    @abstractmethod
    def can_parse(self, file_content: str) -> bool:
        """Check if this parser can handle the given CSV content."""
        pass
    
    @abstractmethod
    def parse(self, file: Union[BinaryIO, str], holder_name: str = None) -> ParsedBankData:
        """Parse CSV file into bank data.
        
        Args:
            file: Binary file or string content to parse
            holder_name: Account holder name (optional, may be extracted from CSV)
            
        Returns:
            ParsedBankData containing accounts and their transactions
            
        Raises:
            ValueError: If CSV format is invalid or unsupported
        """
        pass
    
    def _normalize_file_input(self, file: Union[BinaryIO, str]) -> str:
        """Convert file input to string content."""
        if isinstance(file, str):
            return file
        elif hasattr(file, 'read'):
            if hasattr(file, 'seek'):
                file.seek(0)  # Reset file pointer
            content = file.read()
            if isinstance(content, bytes):
                return content.decode('utf-8-sig')  # Handle BOM
            return content
        else:
            raise ValueError("File input must be string or file-like object")