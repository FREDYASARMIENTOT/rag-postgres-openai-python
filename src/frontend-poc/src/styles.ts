import React from "react";

export const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: "1000px", margin: "0 auto", padding: "1.5rem",
    fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
    color: "#1a1a2e", minHeight: "100vh",
  },
  header: {
    background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
    color: "#e94560", padding: "1rem 1.5rem", borderRadius: "12px",
    marginBottom: "1.5rem", display: "flex", alignItems: "center",
    justifyContent: "space-between", flexWrap: "wrap" as const, gap: "0.5rem",
  },
  headerTitle: { fontSize: "1.3rem", fontWeight: 700, color: "#fff" },
  headerSubtitle: { fontSize: "0.8rem", color: "#a0a0b8" },
  tabs: { display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" as const },
  tab: {
    padding: "0.6rem 1.2rem", border: "none", borderRadius: "8px",
    background: "#e8e8ee", color: "#555", cursor: "pointer",
    fontWeight: 600, fontSize: "0.9rem", transition: "all 0.2s",
  },
  tabActive: { background: "#1a1a2e", color: "#fff" },
  card: {
    background: "#fff", borderRadius: "12px", padding: "1.5rem",
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)", marginBottom: "1rem",
    border: "1px solid #eee",
  },
  input: {
    width: "100%", padding: "0.8rem 1rem", border: "2px solid #ddd",
    borderRadius: "8px", fontSize: "1rem", outline: "none",
    transition: "border-color 0.2s", fontFamily: "inherit",
  },
  textarea: {
    width: "100%", minHeight: "100px", padding: "0.8rem 1rem",
    border: "2px solid #ddd", borderRadius: "8px", fontSize: "0.95rem",
    outline: "none", fontFamily: "inherit", resize: "vertical" as const,
  },
  button: {
    padding: "0.7rem 1.5rem", border: "none", borderRadius: "8px",
    fontWeight: 600, cursor: "pointer", fontSize: "0.95rem",
    transition: "all 0.2s",
  },
  buttonPrimary: { background: "#1a1a2e", color: "#fff" },
  buttonDanger: { background: "#e94560", color: "#fff" },
  buttonSmall: { padding: "0.4rem 0.8rem", fontSize: "0.8rem" },
  respuesta: {
    background: "#f8f9ff", padding: "1rem", borderRadius: "8px",
    whiteSpace: "pre-wrap" as const, lineHeight: 1.6, marginTop: "0.5rem",
  },
  fragmento: {
    background: "#fff", border: "1px solid #e0e0e8", borderRadius: "8px",
    padding: "0.8rem", marginTop: "0.5rem", fontSize: "0.85rem",
  },
  error: { color: "#e94560", fontWeight: 600, marginTop: "0.5rem" },
  badge: {
    display: "inline-block", padding: "0.2rem 0.6rem",
    borderRadius: "12px", fontSize: "0.75rem", fontWeight: 600,
  },
  badgeOk: { background: "#d4edda", color: "#155724" },
  badgeErr: { background: "#f8d7da", color: "#721c24" },
  table: { width: "100%", borderCollapse: "collapse" as const, fontSize: "0.9rem" },
  th: {
    textAlign: "left" as const, padding: "0.6rem 0.8rem",
    borderBottom: "2px solid #ddd", fontWeight: 600, color: "#555",
  },
  td: { padding: "0.6rem 0.8rem", borderBottom: "1px solid #eee" },
  grid2: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem" },
};

export const spinnerStyle = document.createElement("style");
spinnerStyle.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
document.head.appendChild(spinnerStyle);

export function StatusBadge({ ok, labelOk, labelErr }: { ok: boolean; labelOk: string; labelErr: string }) {
  return React.createElement("span", {
    style: { ...styles.badge, ...(ok ? styles.badgeOk : styles.badgeErr) },
  }, ok ? labelOk : labelErr);
}

export function Spinner() {
  return React.createElement("div", {
    style: {
      display: "inline-block", width: "20px", height: "20px",
      border: "3px solid #ddd", borderTopColor: "#1a1a2e",
      borderRadius: "50%", animation: "spin 0.8s linear infinite",
      marginRight: "0.5rem", verticalAlign: "middle",
    },
  });
}