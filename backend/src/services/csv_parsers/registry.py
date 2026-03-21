"""Parser registry and discovery system."""

from __future__ import annotations

from typing import Dict, List, Union, BinaryIO, Optional

from .base import CSVParser, ParsedBankData
from .dkb_parser import DKBParser


class ParserRegistry:
    """Registry for managing CSV parsers."""
    
    def __init__(self):
        self._parsers: Dict[str, CSVParser] = {}
        self._register_built_in_parsers()
    
    def _register_built_in_parsers(self):
        """Register all built-in parsers."""
        dkb = DKBParser()
        self._parsers[dkb.name] = dkb
    
    def register(self, parser: CSVParser):
        """Register a new parser."""
        self._parsers[parser.name] = parser
    
    def get_parser(self, name: str) -> CSVParser:
        """Get parser by name."""
        if name not in self._parsers:
            available = ", ".join(self._parsers.keys())
            raise ValueError(f"Unknown parser '{name}'. Available: {available}")
        return self._parsers[name]
    
    def list_parsers(self) -> List[str]:
        """List all available parser names."""
        return list(self._parsers.keys())
    
    def auto_detect(self, file_content: str) -> Optional[CSVParser]:
        """Auto-detect which parser can handle the given content."""
        for parser in self._parsers.values():
            if parser.can_parse(file_content):
                return parser
        return None


# Global registry instance
_registry = ParserRegistry()


def get_parser(name: str) -> CSVParser:
    """Get a CSV parser by name."""
    return _registry.get_parser(name)


def list_parsers() -> List[str]:
    """List all available parser names."""
    return _registry.list_parsers()


def parse_csv_file(
    file: Union[BinaryIO, str], 
    parser_name: Optional[str] = None,
    holder_name: Optional[str] = None
) -> ParsedBankData:
    """Parse a CSV file using the specified or auto-detected parser.
    
    Args:
        file: File to parse (binary file or string content)
        parser_name: Specific parser to use, or None for auto-detection
        holder_name: Account holder name
        
    Returns:
        ParsedBankData containing accounts and transactions
        
    Raises:
        ValueError: If no suitable parser found or parsing fails
    """
    # Convert to string for auto-detection
    if hasattr(file, 'read'):
        content = file.read()
        if hasattr(file, 'seek'):
            file.seek(0)  # Reset for actual parsing
        if isinstance(content, bytes):
            content = content.decode('utf-8-sig')
    else:
        content = file
    
    # Get parser
    if parser_name:
        parser = get_parser(parser_name)
    else:
        parser = _registry.auto_detect(content)
        if not parser:
            raise ValueError("Could not auto-detect CSV format. Please specify parser explicitly.")
    
    # Parse the file
    return parser.parse(file, holder_name)