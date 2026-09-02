-- =============================================================================
-- MIGRACION 003b: COMMENTS ON rag.documentos
-- FASE F: Modelo de Datos Institucional RAG + LOG
-- Universidad del Rosario
-- =============================================================================

COMMENT ON TABLE rag.documentos IS
'Catalogo maestro de documentos institucionales que pueden participar en el RAG. Cada registro representa una fuente documental identificable y conserva informacion de clasificacion, periodo, origen, version, vigencia, trazabilidad y utilizacion. La fecha de carga representa el momento de incorporacion al RAG y no debe confundirse con la fecha del documento ni con la fecha de corte de la informacion.';

COMMENT ON COLUMN rag.documentos.id_documento IS 'Identificador interno unico del documento dentro del catalogo documental institucional. Es utilizado como referencia primaria por los fragmentos, clasificacion tematica, procesos de carga, consultas y eventos de auditoria.';

COMMENT ON COLUMN rag.documentos.id_serie_documental IS 'Identificador de la serie documental a la que pertenece el documento. Relaciona el documento con su familia logica (Balance General, Informe de Gestion, etc.).';

COMMENT ON COLUMN rag.documentos.id_periodo IS 'Identificador del periodo al que corresponde la informacion del documento. NULL si el documento no tiene un periodo asociado. No representa la fecha de carga.';

COMMENT ON COLUMN rag.documentos.titulo_documento IS 'Titulo del documento institucional. Visible para el agente en los resultados de retrieval y generacion. Debe ser descriptivo y unico dentro de la serie documental.';

COMMENT ON COLUMN rag.documentos.descripcion_documento IS 'Descripcion textual del contenido y proposito del documento. Proporciona contexto adicional al titulo.';

COMMENT ON COLUMN rag.documentos.tipo_documento IS 'Clasificacion del tipo documental segun la naturaleza del contenido. Ejemplos: facultad, reglamento, resolucion, acuerdo, circular, directriz, informe, manual, guia, formato, general.';

COMMENT ON COLUMN rag.documentos.nombre_archivo_original IS 'Nombre del archivo original del documento tal como fue cargado. Incluye la extension. Sirve para trazabilidad del origen fisico.';

COMMENT ON COLUMN rag.documentos.extension_archivo IS 'Extension del archivo original (pdf, docx, md, txt, etc.). Se almacena separadamente para facilitar busquedas por tipo de archivo.';

COMMENT ON COLUMN rag.documentos.mime_type IS 'Tipo MIME del archivo original. Ejemplo: application/pdf, text/markdown, text/plain.';

COMMENT ON COLUMN rag.documentos.ruta_origen IS 'Ruta de origen del archivo en el sistema de archivos o repositorio de origen. No es una URL accesible publicamente.';

COMMENT ON COLUMN rag.documentos.fuente_documento IS 'Origen institucional del documento. Puede ser una dependencia, URL institucional, sistema de origen o referencia externa.';

COMMENT ON COLUMN rag.documentos.usuario_cargador IS 'Nombre o identificador legible del usuario que realizo la carga del documento en el RAG.';

COMMENT ON COLUMN rag.documentos.identificador_usuario_cargador IS 'Identificador unico del usuario cargador en el sistema de autenticacion. Permite trazabilidad precisa de quien incorporo el documento.';

COMMENT ON COLUMN rag.documentos.fecha_documento IS 'Fecha correspondiente a la elaboracion, emision o formalizacion del documento fuente. No representa la fecha de incorporacion del documento al RAG.';

COMMENT ON COLUMN rag.documentos.fecha_corte IS 'Fecha hasta la cual el contenido o los datos del documento representan la realidad institucional. Puede ser diferente de la fecha de elaboracion y de la fecha de carga.';

COMMENT ON COLUMN rag.documentos.fecha_carga IS 'Fecha calendario en la que el documento fue incorporado al repositorio documental del RAG. Debe analizarse conjuntamente con hora_carga para reconstruir el momento de carga.';

COMMENT ON COLUMN rag.documentos.hora_carga IS 'Hora local correspondiente al proceso de incorporacion del documento. Se almacena mediante el tipo TIME y representa la hora en formato HH:MM:SS.';

COMMENT ON COLUMN rag.documentos.tamano_bytes IS 'Tamano del archivo original en bytes. Permite control de capacidad y deteccion de anomalias en el tamano de los documentos. NULL si no se pudo determinar.';

COMMENT ON COLUMN rag.documentos.hash_sha256 IS 'Valor SHA-256 calculado sobre el archivo documental utilizado para identificar duplicados, preservar trazabilidad y relacionar fisicamente un archivo con su registro documental.';

COMMENT ON COLUMN rag.documentos.version_documento IS 'Numero secuencial de version del documento dentro de una cadena documental. Permite distinguir diferentes ediciones del mismo documento sin sobrescribir su historial.';

COMMENT ON COLUMN rag.documentos.id_documento_anterior IS 'Referencia al documento que representa la version inmediatamente anterior. Permite reconstruir la evolucion documental y mantener trazabilidad entre versiones.';

COMMENT ON COLUMN rag.documentos.estado_vigencia IS 'Estado funcional del documento dentro del ciclo de vida institucional. Permite diferenciar informacion vigente, historica, reemplazada, archivada o retirada. El estado HISTORICO no implica eliminacion del documento.';

COMMENT ON COLUMN rag.documentos.es_documento_critico IS 'Indicador de criticidad institucional del documento. Un documento critico contiene informacion esencial para la operacion o toma de decisiones. No debe ser retirado del RAG sin aprobacion explicita.';

COMMENT ON COLUMN rag.documentos.participa_retrieval IS 'Indicador de si el documento debe ser incluido en las busquedas semanticas del RAG. FALSE permite excluir documentos del retrieval sin eliminarlos del catalogo.';