"""
Tests unitarios para fragmentador_documentos.py.

Valida:
    1. Fragmentación por encabezados Markdown.
    2. Límite de tamaño máximo.
    3. Contenido vacío.
    4. Documentos sin encabezados.
"""

from __future__ import annotations

import pytest

from fastapi_app.fragmentador_documentos import FragmentadorDocumentos, FragmentoResultado


class TestFragmentadorConfiguracion:
    """Pruebas de configuración del fragmentador."""

    def test_tamano_maximo_default(self):
        """El tamaño máximo por defecto debe ser 1000."""
        f = FragmentadorDocumentos()
        assert f.tamano_maximo == 1000

    def test_tamano_maximo_personalizado(self):
        """Debe aceptar tamaño máximo personalizado."""
        f = FragmentadorDocumentos(tamano_maximo=500)
        assert f.tamano_maximo == 500

    def test_tamano_maximo_muy_pequeno_lanza_error(self):
        """Tamaño máximo < 100 debe lanzar ValueError."""
        with pytest.raises(ValueError, match="muy peque"):
            FragmentadorDocumentos(tamano_maximo=50)

    def test_solapamiento_negativo_lanza_error(self):
        """Solapamiento negativo debe lanzar ValueError."""
        with pytest.raises(ValueError):
            FragmentadorDocumentos(solapamiento=-1)

    def test_solapamiento_mayor_que_tamano_lanza_error(self):
        """Solapamiento >= tamano_maximo debe lanzar ValueError."""
        with pytest.raises(ValueError):
            FragmentadorDocumentos(tamano_maximo=200, solapamiento=200)


class TestFragmentacionMarkdown:
    """Pruebas de fragmentación de documentos Markdown."""

    def test_documento_con_encabezados_se_fragmenta(self):
        """Documento con ## debe fragmentarse por sección."""
        md = "## Facultad de Medicina\n\nTexto de medicina.\n\n## Facultad de Derecho\n\nTexto de derecho."
        f = FragmentadorDocumentos(tamano_maximo=2000)
        fragmentos = f.fragmentar(md)
        assert len(fragmentos) == 2
        assert "Medicina" in fragmentos[0].contenido
        assert "Derecho" in fragmentos[1].contenido

    def test_cada_fragmento_tiene_orden_unico(self):
        """Cada fragmento debe tener un orden incremental."""
        md = "## A\n\nContenido A\n\n## B\n\nContenido B\n\n## C\n\nContenido C"
        f = FragmentadorDocumentos(tamano_maximo=2000)
        fragmentos = f.fragmentar(md)
        ordenes = [fr.orden for fr in fragmentos]
        assert ordenes == [0, 1, 2]

    def test_fragmentos_tienen_contenido_no_vacio(self):
        """Cada fragmento debe tener contenido no vacío."""
        md = "## Test\n\nContenido válido.\n\n## Test2\n\nMás contenido."
        f = FragmentadorDocumentos(tamano_maximo=2000)
        fragmentos = f.fragmentar(md)
        for fr in fragmentos:
            assert len(fr.contenido.strip()) > 0

    def test_contenido_vacio_lanza_error(self):
        """Contenido vacío debe lanzar ValueError."""
        f = FragmentadorDocumentos()
        with pytest.raises(ValueError, match="vacío"):
            f.fragmentar("")

    def test_contenido_solo_espacios_lanza_error(self):
        """Contenido solo con espacios debe lanzar ValueError."""
        f = FragmentadorDocumentos()
        with pytest.raises(ValueError, match="vacío"):
            f.fragmentar("   \n  \n  ")

    def test_documento_sin_encabezados_es_un_solo_fragmento(self):
        """Documento sin ## debe ser un solo fragmento si cabe en tamaño."""
        md = "Este es un documento sin encabezados Markdown."
        f = FragmentadorDocumentos(tamano_maximo=2000)
        fragmentos = f.fragmentar(md)
        assert len(fragmentos) == 1

    def test_seccion_grande_se_subdivide(self):
        """Sección que excede tamano_maximo debe subdividirse."""
        md = "## Facultad Grande\n\n" + ("Palabra repetida. " * 200) + "\n\n## Otra\n\nFin."
        f = FragmentadorDocumentos(tamano_maximo=500)
        fragmentos = f.fragmentar(md)
        assert len(fragmentos) > 1, "La sección grande debió subdividirse"

    def test_fragmento_resultado_tiene_metadatos(self):
        """Cada FragmentoResultado debe tener metadata con tipo_seccion."""
        md = "## Facultad de Medicina\n\nContenido médico."
        f = FragmentadorDocumentos(tamano_maximo=2000)
        fragmentos = f.fragmentar(md)
        for fr in fragmentos:
            assert "tipo_seccion" in fr.metadata


class TestFragmentoResultado:
    """Pruebas de la clase FragmentoResultado."""

    def test_creacion_fragmento_resultado(self):
        """Crear FragmentoResultado con valores básicos."""
        fr = FragmentoResultado(contenido="Test", orden=0)
        assert fr.contenido == "Test"
        assert fr.orden == 0

    def test_contenido_se_limpia_de_espacios(self):
        """El contenido debe limpiarse de espacios iniciales/finales."""
        fr = FragmentoResultado(contenido="  Test con espacios  ", orden=0)
        assert fr.contenido == "Test con espacios"

    def test_repr_incluye_orden_y_chars(self):
        """__repr__ debe mostrar orden y longitud."""
        fr = FragmentoResultado(contenido="Hola mundo", orden=3)
        repr_str = repr(fr)
        assert "orden=3" in repr_str
        assert "chars=" in repr_str