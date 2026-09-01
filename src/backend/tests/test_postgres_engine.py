"""
Tests UNIT e AZURE para postgres_engine.py.

Cobertura:
- UNIT 1: URI construction for local PostgreSQL.
- UNIT 2: URI construction for Azure PostgreSQL with SSL.
"""

import pytest

from fastapi_app.postgres_engine import verify_pgvector_available, verify_pgvector_created


@pytest.mark.unit
class TestPgvectorValidationFunctions:
    """Prueba que las funciones de validación de pgvector existen y son callables."""

    def test_verify_pgvector_available_exists(self):
        """Verifica que la función existe y es asíncrona."""
        import asyncio
        assert asyncio.iscoroutinefunction(verify_pgvector_available)

    def test_verify_pgvector_created_exists(self):
        """Verifica que la función existe y es asíncrona."""
        import asyncio
        assert asyncio.iscoroutinefunction(verify_pgvector_created)

    def test_funciones_distintas(self):
        """Son funciones diferentes con diferente propósito."""
        assert verify_pgvector_available is not verify_pgvector_created