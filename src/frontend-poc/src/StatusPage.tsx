import { useEffect, useState } from "react";
import { api, type HealthStatus } from "./api";
import { styles, StatusBadge, Spinner } from "./styles";

export default function StatusPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const check = async () => {
    setLoading(true); setError("");
    try { setHealth(await api.health()); }
    catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  useEffect(() => { check(); }, []);

  return (
    <div style={styles.card}>
      <h2 style={{ marginBottom: "1rem" }}>🔍 Estado del RAG Institucional</h2>
      {loading && <div><Spinner /> Verificando...</div>}
      {error && <div style={styles.error}>{error}</div>}
      {health && (
        <div style={styles.grid2}>
          <div>Sessionmaker:</div>
          <div><StatusBadge ok={health.sessionmaker} labelOk="✅ OK" labelErr="❌ No disponible" /></div>
          <div>Proveedor Embeddings:</div>
          <div><StatusBadge ok={health.proveedor_embeddings} labelOk="✅ OK" labelErr="❌ No disponible" /></div>
          <div>Proveedor LLM (Luna):</div>
          <div><StatusBadge ok={health.proveedor_llm} labelOk="✅ OK" labelErr="❌ No disponible" /></div>
        </div>
      )}
      <button style={{ ...styles.button, ...styles.buttonPrimary, marginTop: "1rem" }} onClick={check}>
        🔄 Refrescar
      </button>
    </div>
  );
}