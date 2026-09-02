# Áreas y Facultades UR — Dataset de Prueba para Embeddings

> **DATASET DE PRUEBA — NO OFICIAL**
> 
> Este conjunto de datos es un artefacto de prueba para validar la generación de embeddings,
> persistencia vectorial y recuperación RAG. No representa información institucional oficial
> de la Universidad del Rosario. Las descripciones son resúmenes informativos para propósitos
> de prueba de similitud semántica.

---

## Registros del Dataset

### 1. Facultad de Ciencias Naturales y Matemáticas

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | facultad |
| Nombre | Facultad de Ciencias Naturales y Matemáticas |
| Texto para embedding | Universidad del Rosario - Facultad de Ciencias Naturales y Matematicas. Ofrece programas academicos en Biologia, Quimica, Matematicas, Fisica y Ciencias de la Tierra. Investigacion en biodiversidad, biotecnologia y ciencias exactas. Laboratorios especializados y grupos de investigacion reconocidos. |

### 2. Escuela de Ingeniería, Ciencia y Tecnología

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | escuela |
| Nombre | Escuela de Ingeniería, Ciencia y Tecnología |
| Texto para embedding | Universidad del Rosario - Escuela de Ingenieria, Ciencia y Tecnologia. Programas en Ingenieria de Sistemas, Ingenieria Industrial, Ingenieria Civil, Ciencia de Datos e Inteligencia Artificial. Formacion en transformacion digital, innovacion tecnologica y emprendimiento. |

### 3. Facultad de Jurisprudencia

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | facultad |
| Nombre | Facultad de Jurisprudencia |
| Texto para embedding | Universidad del Rosario - Facultad de Jurisprudencia. Pregrado en Derecho con mas de 370 anos de tradicion. Especializaciones en Derecho Penal, Laboral, Tributario, Constitucional y Comercial. Clinica juridica y consultorio legal. |

### 4. Facultad de Medicina y Ciencias de la Salud

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | facultad |
| Nombre | Facultad de Medicina y Ciencias de la Salud |
| Texto para embedding | Universidad del Rosario - Facultad de Medicina y Ciencias de la Salud. Programas en Medicina, Enfermeria, Fisioterapia, Terapia Ocupacional y Salud Publica. Hospital Universitario Mayor como escenario de practica. Investigacion clinica y biomedica. |

### 5. Facultad de Economía

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | facultad |
| Nombre | Facultad de Economía |
| Texto para embedding | Universidad del Rosario - Facultad de Economia. Programas en Economia, Administracion de Empresas, Finanzas y Negocios Internacionales. Centro de Estudios Economicos. Investigacion en desarrollo economico y politicas publicas. |

### 6. Escuela de Ciencias Humanas

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | escuela |
| Nombre | Escuela de Ciencias Humanas |
| Texto para embedding | Universidad del Rosario - Escuela de Ciencias Humanas. Programas en Antropologia, Sociologia, Filosofia, Historia, Literatura y Periodismo. Enfoque en ciencias sociales y humanidades. Grupos de investigacion en memoria historica y cultura. |

### 7. Facultad de Estudios Internacionales, Políticos y Urbanos

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | facultad |
| Nombre | Facultad de Estudios Internacionales, Políticos y Urbanos |
| Texto para embedding | Universidad del Rosario - Facultad de Estudios Internacionales, Politicos y Urbanos. Programas en Relaciones Internacionales, Ciencia Politica, Gobierno y Estudios Urbanos. Observatorio del Caribe Colombiano. Investigacion en politica global y desarrollo territorial. |

### 8. Instituto de Ciencias Básicas

| Campo | Valor |
|-------|-------|
| Dominio | urosario.edu.co |
| Tipo | instituto |
| Nombre | Instituto de Ciencias Básicas |
| Texto para embedding | Universidad del Rosario - Instituto de Ciencias Basicas. Programas de nivelacion y fundamentacion en Matematicas, Quimica, Fisica y Biologia. Cursos preuniversitarios y de apoyo academico. |

---

## Consultas de Prueba Sugeridas

1. "¿Qué facultad o escuela de la Universidad del Rosario está relacionada con estudios de tecnología, datos e inteligencia artificial?"
2. "¿Cuáles son los programas ofrecidos por la Facultad de Medicina y Ciencias de la Salud?"
3. "¿Dónde puedo estudiar Derecho en la Universidad del Rosario?"
4. "¿Qué opciones de estudio en economía y finanzas ofrece la Universidad del Rosario?"
5. "¿Existe algún programa en ciencia de datos en el portafolio académico?"

---

## Notas Técnicas

- La dimensión actual del deployment `ur-rag-embedding-3-large` es **3072** (el parámetro `dimensions` no es soportado).
- Los embeddings se generan con el modelo `text-embedding-3-large` versión base "1".
- Para persistencia se requiere crear la BD `rag_institucional`, habilitar `pgvector`, y ajustar la columna `embedding_3l` a `Vector(3072)`.
