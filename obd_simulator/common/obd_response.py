"""
OBD Response handling compatible with python-OBD.
"""

from dataclasses import dataclass
from typing import Any, Optional
import pint

# Create a unit registry for handling physical quantities
ureg = pint.UnitRegistry()
Quantity = ureg.Quantity

@dataclass
class OBDResponse:
    """OBD Response class compatible with python-OBD"""
    command: Any
    value: Optional[Quantity] = None
    message: Optional[str] = None
    
    def is_null(self) -> bool:
        """Check if the response has no value"""
        return self.value is None
    
    def __str__(self) -> str:
        if self.is_null():
            return "None"
        return f"{self.value}"