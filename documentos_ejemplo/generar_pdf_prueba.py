"""Genera un PDF de prueba con contenido institucional de la Universidad del Rosario."""
import os
import pymupdf

CONTENIDO = """
FACULTADES DE LA UNIVERSIDAD DEL ROSARIO

La Universidad del Rosario, fundada en 1653, es una de las universidades
mas antiguas y prestigiosas de Colombia.

FACULTAD DE CIENCIAS NATURALES
La Facultad de Ciencias Naturales ofrece programas en Biologia, Quimica,
y Ciencias Ambientales. Su enfoque esta en la investigacion cientifica y
la formacion integral de profesionales.

FACULTAD DE ECONOMIA
La Facultad de Economia ofrece programas en Economia, Administracion de
Empresas y Negocios Internacionales. Se destaca por su enfoque en el
desarrollo sostenible y la responsabilidad social empresarial.

FACULTAD DE MEDICINA
La Facultad de Medicina y Ciencias de la Salud es una de las mas reconocidas
del pais. Ofrece programas en Medicina, Enfermeria, y Ciencias de la Salud.
Cuenta con hospitales universitarios de alta complejidad.

FACULTAD DE JURISPRUDENCIA
La Facultad de Jurisprudencia es la facultad fundacional de la universidad.
Ofrece programas en Derecho y cuenta con una tradicion juridica de mas de
370 anos.

FACULTAD DE INGENIERIA
La Facultad de Ingenieria ofrece programas en Ingenieria Biomedica,
Ingenieria de Sistemas, e Ingenieria Industrial. Se enfoca en la innovacion
tecnologica y el emprendimiento.

ESCUELA DE CIENCIAS HUMANAS
La Escuela de Ciencias Humanas ofrece programas en Filosofia, Literatura,
Historia y Antropologia. Promueve el pensamiento critico y la investigacion
interdisciplinaria.

FACULTAD DE CREACION
La Facultad de Creacion ofrece programas en Artes Plasticas, Diseno y
Comunicacion Visual. Fomenta la expresion artistica y la innovacion creativa.
"""


def generar_pdf(ruta_salida: str) -> None:
    """Genera un PDF con el contenido institucional."""
    doc = pymupdf.open()
    page = doc.new_page()
    
    page.insert_text(
        pymupdf.Point(50, 80),
        "FACULTADES DE LA UNIVERSIDAD DEL ROSARIO",
        fontsize=18,
        fontname="helv",
    )
    
    y = 120
    for parrafo in CONTENIDO.strip().split("\n\n"):
        if not parrafo.strip():
            continue
        page.insert_text(
            pymupdf.Point(50, y),
            parrafo.strip(),
            fontsize=11,
            fontname="helv",
        )
        y += 50
        if y > 750:
            page = doc.new_page()
            y = 80
    
    doc.save(ruta_salida)
    doc.close()
    print(f"PDF creado exitosamente: {ruta_salida}")
    print(f"Tamano: {os.path.getsize(ruta_salida)} bytes")


if __name__ == "__main__":
    ruta = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "pdf/facultades_ur_prueba.pdf",
    )
    generar_pdf(ruta)