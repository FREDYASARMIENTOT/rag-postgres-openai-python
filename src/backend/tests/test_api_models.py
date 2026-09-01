"""
Tests UNIT para los modelos de API (api_models.py).

Cobertura:
- UNIT 1: ChatRequestOverrides defaults.
- UNIT 2: Filter validation.
- UNIT 3: PriceFilter field constraints.
- UNIT 4: ItemPublic serialization.
"""

import pytest
from pydantic import ValidationError

from fastapi_app.api_models import (
    BrandFilter,
    ChatRequestOverrides,
    Filter,
    ItemPublic,
    ItemWithDistance,
    PriceFilter,
    RetrievalMode,
    SearchResults,
)


@pytest.mark.unit
class TestRetrievalMode:
    """Prueba los modos de búsqueda disponibles."""

    def test_valores(self):
        assert RetrievalMode.TEXT.value == "text"
        assert RetrievalMode.VECTORS.value == "vectors"
        assert RetrievalMode.HYBRID.value == "hybrid"


@pytest.mark.unit
class TestChatRequestOverrides:
    """Prueba los valores por defecto de overrides."""

    def test_defaults(self):
        overrides = ChatRequestOverrides()
        assert overrides.top == 3
        assert overrides.temperature == 0.3
        assert overrides.retrieval_mode == RetrievalMode.HYBRID
        assert overrides.use_advanced_flow is True
        assert overrides.prompt_template is None


@pytest.mark.unit
class TestFilterValidation:
    """Prueba la validación de filtros."""

    def test_filter_valido(self):
        f = Filter(column="price", comparison_operator=">", value=30.0)
        assert f.column == "price"
        assert f.comparison_operator == ">"
        assert f.value == 30.0

    def test_filter_str_value(self):
        f = Filter(column="brand", comparison_operator="=", value="AirStrider")
        assert f.value == "AirStrider"

    def test_filter_sin_campos(self):
        with pytest.raises(ValidationError):
            Filter()

    def test_price_filter_default_column(self):
        pf = PriceFilter(comparison_operator=">", value=30.0)
        assert pf.column == "price"
        assert pf.comparison_operator == ">"
        assert pf.value == 30.0

    def test_brand_filter_default_column(self):
        bf = BrandFilter(comparison_operator="=", value="AirStrider")
        assert bf.column == "brand"
        assert bf.comparison_operator == "="
        assert bf.value == "AirStrider"


@pytest.mark.unit
class TestItemPublic:
    """Prueba el modelo de respuesta pública de ítems."""

    def test_creacion_valida(self):
        item = ItemPublic(id=1, type="Boots", brand="AirStrider",
                          name="Test Boots", description="Test desc",
                          price=99.99)
        assert item.id == 1
        assert item.to_str_for_rag() == "Name:Test Boots Description:Test desc Price:99.99 Brand:AirStrider Type:Boots"

    def test_sin_id(self):
        with pytest.raises(ValidationError):
            ItemPublic(type="Boots", brand="X", name="Y",
                       description="Z", price=10.0)


@pytest.mark.unit
class TestSearchResults:
    """Prueba el modelo de resultados de búsqueda."""

    def test_creacion_valida(self):
        results = SearchResults(query="test", items=[], filters=[])
        assert results.query == "test"
        assert results.items == []
        assert results.filters == []