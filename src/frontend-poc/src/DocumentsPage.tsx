import { useEffect, useState } from "react";
import { api, type DocumentoItem, type DocumentoDetalle, type EjemploArchivos } from "./api";
import { styles, StatusBadge, Spinner } from "./styles";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedDoc, setSelectedDoc] = useState<DocumentoDetalle | null>(null);
  const [detalleLoading, setDetalleLoading] = useState(false);

  const [titulo, setTitulo] = useState("");
  const [contenido, setContenido] = useState("");
  const [ingestando, setIngestando] = useState(false);
  const [ingestaMsg, setIngestaMsg] = useState("");

  const [ejemplos, setEjemplos] = useState<EjemploArchivos | null>(null);
  const [rutaArchivo, setRutaArchivo] = useState("");

  const cargarDocs = async () => {
    setLoading(true); setError("");
    try { setDocs(await api.listarDocumentos()); }
    catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const cargarEjemplos = async () => {
    try { setEjemplos(await api.documentosEjemplo()); }
    catch { /* ignore */ }
  };

  useEffect(() => { cargarDocs(); cargarEjemplos(); }, []);

  const verDetalle = async (id: number) => {
    setDetalleLoading(true);
    try { setSelectedDoc(await api.obtenerDocumento(id)); }
    catch (e: any) { setError(e.message); }
    setDetalleLoading(false);
  };

  const eliminarDoc = async (id: number) => {
    if (!confirm(`Eliminar documento #${id}?`)) return;
    try {
      await api.eliminarDocumento(id);
      cargarDocs(); setSelectedDoc(null);
    } catch (e: any) { setError(e.message); }
  };

  const ingestarTexto = async () => {
    if (!titulo.trim() || !contenido.trim()) return;
    setIngestando(true); setIngestaMsg("");
    try {
      const res = await api.cargarContenido(titulo.trim(), contenido.trim());
      setIngestaMsg(res.resultado.mensaje);
      setTitulo(""); setContenido(""); cargarDocs();
    } catch (e: any) { setIngestaMsg(`Error: ${e.message}`); }
    setIngestando(false);
  };

  const ingestarArchivo = async (ruta?: string) => {
    const path = ruta || rutaArchivo;
    if (!path.trim()) return;
    setIngestando(true); setIngestaMsg("");
    try {
      const res = await api.ingestarArchivo(path.trim());
      setIngestaMsg(res.resultado.mensaje);
      setRutaArchivo(""); cargarDocs();
    } catch (e: any) { setIngestaMsg(`Error: ${e.message}`); }
    setIngestando(false);
  };

  return (
    <div>
      <div style={styles.card}>
        <h2 style={{ marginBottom: "1rem" }}>📥 Cargar documento</h2>
        <h3 style={{ fontSize: "0.95rem", color: "#555", marginBottom: "0.5rem" }}>
          Opcion 1: Pegar contenido
        </h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1rem" }}>
          <input style={styles.input} placeholder="Titulo del documento" value={titulo}
            onChange={e => setTitulo(e.target.value)} />
          <textarea style={styles.textarea} placeholder="Contenido (Markdown o texto plano)"
            value={contenido} onChange={e => setContenido(e.target.value)} />
          <button style={{ ...styles.button, ...styles.buttonPrimary }} onClick={ingestarTexto} disabled={ingestando}>
            {ingestando ? "⏳ Ingestando..." : "📤 Ingestar contenido"}
          </button>
        </div>

        <h3 style={{ fontSize: "0.95rem", color: "#555", marginBottom: "0.5rem" }}>
          Opcion 2: Ruta de archivo en servidor
        </h3>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
          <input style={styles.input} placeholder="C:/ruta/completa/al/archivo.pdf"
            value={rutaArchivo} onChange={e => setRutaArchivo(e.target.value)} />
          <button style={{ ...styles.button, ...styles.buttonPrimary }}
            onClick={() => ingestarArchivo()} disabled={ingestando}>
            📤
          </button>
        </div>

        {ejemplos && ejemplos.archivos.length > 0 && (
          <details>
            <summary style={{ cursor: "pointer", fontWeight: 600, color: "#0f3460", fontSize: "0.85rem" }}>
              📂 Archivos de ejemplo ({ejemplos.archivos.length})
            </summary>
            <div style={{ marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              {ejemplos.archivos.slice(0, 10).map((a, i) => (
                <div key={i} style={{ display: "flex", gap: "0.5rem", fontSize: "0.85rem", alignItems: "center" }}>
                  <span style={{ color: "#888" }}>📄</span>
                  <code style={{ flex: 1 }}>{a}</code>
                  <button style={{ ...styles.button, ...styles.buttonPrimary, ...styles.buttonSmall }}
                    onClick={() => ingestarArchivo(ejemplos.ruta_base + "\\" + a.replace("/", "\\"))}
                    disabled={ingestando}>
                    Ingestar
                  </button>
                </div>
              ))}
            </div>
          </details>
        )}

        {ingestaMsg && <div style={{ marginTop: "0.5rem", fontWeight: 600, color: "#155724" }}>{ingestaMsg}</div>}
      </div>

      <div style={styles.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2>📋 Documentos Indexados ({docs.length})</h2>
          <button style={{ ...styles.button, ...styles.buttonPrimary, ...styles.buttonSmall }} onClick={cargarDocs}>
            🔄
          </button>
        </div>
        {error && <div style={styles.error}>{error}</div>}
        {loading && <Spinner />}
        {docs.length === 0 && !loading && <div style={{ color: "#888" }}>No hay documentos indexados.</div>}
        <table style={styles.table}>
          <thead><tr>
            <th style={styles.th}>ID</th><th style={styles.th}>Titulo</th>
            <th style={styles.th}>Fuente</th><th style={styles.th}>Tipo</th>
            <th style={styles.th}>Frags</th><th style={styles.th}>Estado</th><th style={styles.th}>Accion</th>
          </tr></thead>
          <tbody>
            {docs.map(d => (
              <tr key={d.documento_id}>
                <td style={styles.td}>{d.documento_id}</td>
                <td style={styles.td}>{d.titulo}</td>
                <td style={styles.td}>{d.fuente}</td>
                <td style={styles.td}>{d.tipo_documento}</td>
                <td style={styles.td}>{d.cantidad_fragmentos}</td>
                <td style={styles.td}>
                  <StatusBadge ok={d.estado === "VIGENTE"} labelOk="Vigente" labelErr={d.estado} />
                </td>
                <td style={styles.td}>
                  <button style={{ border: "none", background: "none", cursor: "pointer", marginRight: "0.5rem" }}
                    onClick={() => verDetalle(d.documento_id)}>👁️</button>
                  <button style={{ border: "none", background: "none", cursor: "pointer", color: "#e94560" }}
                    onClick={() => eliminarDoc(d.documento_id)}>🗑️</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {detalleLoading && <Spinner />}
        {selectedDoc && (
          <div style={{ marginTop: "1rem", background: "#f8f9ff", padding: "1rem", borderRadius: "8px" }}>
            <h3 style={{ marginBottom: "0.5rem" }}>
              📄 {selectedDoc.titulo}
              <button style={{ ...styles.button, ...styles.buttonSmall, marginLeft: "1rem", background: "#ddd" }}
                onClick={() => setSelectedDoc(null)}>✕ Cerrar</button>
            </h3>
            <div style={{ fontSize: "0.85rem", color: "#555", marginBottom: "0.5rem" }}>
              ID: {selectedDoc.documento_id} | Fuente: {selectedDoc.fuente} | Tipo: {selectedDoc.tipo_documento}
              | Estado: {selectedDoc.estado} | Fragmentos: {selectedDoc.cantidad_fragmentos}
            </div>
            {selectedDoc.fragmentos.slice(0, 5).map(f => (
              <div key={f.id_fragmento} style={{ ...styles.fragmento, fontSize: "0.82rem" }}>
                <div style={{ fontWeight: 600, color: "#0f3460" }}>
                  #{f.numero_orden} ({f.cantidad_caracteres} chars)
                </div>
                <div>{f.contenido.substring(0, 600)}</div>
              </div>
            ))}
            {selectedDoc.fragmentos.length > 5 && (
              <div style={{ color: "#888", marginTop: "0.3rem" }}>
                ... y {selectedDoc.fragmentos.length - 5} fragmentos mas
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}