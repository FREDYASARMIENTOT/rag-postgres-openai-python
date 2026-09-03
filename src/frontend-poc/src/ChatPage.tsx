import { useState } from "react";
import { api, type GeneracionResult, type ConsultaResult } from "./api";
import { styles, Spinner } from "./styles";

export default function ChatPage() {
  const [consulta, setConsulta] = useState("");
  const [modo, setModo] = useState<"simple" | "generacion">("generacion");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GeneracionResult | ConsultaResult | null>(null);
  const [error, setError] = useState("");
  const [historial, setHistorial] = useState<Array<{ consulta: string; tipo: string }>>([]);

  const handleSubmit = async () => {
    if (!consulta.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      if (modo === "generacion") {
        setResult(await api.consultarConGeneracion(consulta.trim()));
      } else {
        setResult(await api.consultar(consulta.trim(), 10));
      }
      setHistorial(prev => [{ consulta: consulta.trim(), tipo: modo }, ...prev].slice(0, 10));
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  const genResult = result && "respuesta" in result ? (result as GeneracionResult) : null;
  const simResult = result && "resultados" in result ? (result as ConsultaResult) : null;

  return (
    <div>
      <div style={styles.card}>
        <h2 style={{ marginBottom: "1rem" }}>💬 Consultar RAG Institucional</h2>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <button style={{ ...styles.tab, ...(modo === "generacion" ? styles.tabActive : {}) }}
            onClick={() => setModo("generacion")}>
            🤖 Generar respuesta
          </button>
          <button style={{ ...styles.tab, ...(modo === "simple" ? styles.tabActive : {}) }}
            onClick={() => setModo("simple")}>
            🔍 Solo búsqueda
          </button>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <input style={styles.input} placeholder='Ej: "Cuantas facultades tiene la Universidad del Rosario?"'
            value={consulta} onChange={e => setConsulta(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSubmit()} disabled={loading} />
          <button style={{ ...styles.button, ...styles.buttonPrimary, whiteSpace: "nowrap" }}
            onClick={handleSubmit} disabled={loading}>
            {loading ? "⏳" : "➡️"}
          </button>
        </div>
        {loading && <div style={{ marginTop: "1rem", display: "flex", alignItems: "center" }}>
          <Spinner /> Consultando...</div>}
        {error && <div style={styles.error}>{error}</div>}

        {genResult && (
          <div style={{ marginTop: "1rem" }}>
            <div style={{ fontWeight: 600, color: "#555", fontSize: "0.85rem" }}>
              Modelo: {genResult.modelo || "N/A"} | Deployment: {genResult.deployment || "N/A"} | Fragmentos: {genResult.fragmentos_count}
            </div>
            <div style={styles.respuesta}>{genResult.respuesta}</div>
            {genResult.fragmentos.length > 0 && (
              <details style={{ marginTop: "1rem" }}>
                <summary style={{ cursor: "pointer", fontWeight: 600, color: "#555" }}>
                  📄 Ver {genResult.fragmentos.length} fragmentos utilizados
                </summary>
                {genResult.fragmentos.map((f, i) => (
                  <div key={i} style={styles.fragmento}>
                    <div style={{ fontWeight: 600, fontSize: "0.8rem", color: "#0f3460" }}>
                      [{f.fuente}] {f.titulo} — Score: {f.score.toFixed(4)}
                    </div>
                    <div style={{ marginTop: "0.3rem" }}>{f.contenido.substring(0, 500)}</div>
                  </div>
                ))}
              </details>
            )}
          </div>
        )}

        {simResult && (
          <div style={{ marginTop: "1rem" }}>
            <div style={{ fontWeight: 600, color: "#555" }}>{simResult.total} resultados</div>
            {simResult.resultados.map((r, i) => (
              <div key={i} style={styles.fragmento}>
                <div style={{ fontWeight: 600, fontSize: "0.8rem", color: "#0f3460" }}>
                  [{r.fuente}] {r.titulo} — Score: {r.score.toFixed(4)}
                </div>
                <div style={{ marginTop: "0.3rem" }}>{r.contenido.substring(0, 400)}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {historial.length > 0 && (
        <div style={styles.card}>
          <h3 style={{ marginBottom: "0.5rem" }}>🕐 Historial</h3>
          {historial.map((h, i) => (
            <div key={i} style={{ padding: "0.3rem 0", borderBottom: "1px solid #f0f0f0", fontSize: "0.85rem" }}>
              <span style={{ color: "#888", marginRight: "0.5rem" }}>
                {h.tipo === "generacion" ? "🤖" : "🔍"}
              </span>
              {h.consulta.substring(0, 80)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}