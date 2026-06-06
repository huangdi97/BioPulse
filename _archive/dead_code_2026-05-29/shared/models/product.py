from dataclasses import dataclass, field


@dataclass
class Product:
    product_id: int = 0
    name: str = ""
    category: str = ""
    brand: str = ""
    model: str = ""
    spec: str = ""
    unit_price: float = 0.0
    keywords: list[str] = field(default_factory=list)
    tech_params: dict = field(default_factory=dict)
    cert_status: str = ""
