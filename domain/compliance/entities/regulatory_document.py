from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class RegulatoryDocument:
    """
    Documento regulatorio inmutable (Snapshot).
    Representa un certificado o guía que no debe cambiar aunque la carga original cambie.
    """
    id: Optional[int]
    doc_type: str  # 'CERTIFICADO_DISPOSICION', 'GUIA_DESPACHO'
    related_load_id: int
    
    snapshot_data: Dict[str, Any] = field(default_factory=dict) # JSON con datos congelados
    
    generated_at: Optional[datetime] = None
    pdf_url: Optional[str] = None
