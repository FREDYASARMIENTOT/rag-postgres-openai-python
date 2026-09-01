"""
Tests del RAG Institucional Universidad del Rosario.

Clasificación de tests:

- UNIT: Prueban lógica interna sin dependencias externas.
  Se ejecutan sin conexión a Azure ni PostgreSQL.

- INTEGRATION: Prueban interacción con componentes reales
  pero controlados (ej: PostgreSQL testcontainer, mock de OpenAI).

- AZURE: Requieren conexión activa a Azure o PostgreSQL real.
  Se ejecutan solo cuando se cuenta con las credenciales adecuadas.

Para ejecutar solo tests unitarios:
    pytest -m unit -v

Para ejecutar todos los tests (excepto AZURE):
    pytest -v

Para ejecutar todos los tests incluyendo AZURE:
    pytest -v --run-azure
"""