import { useState } from "react";
import { styles } from "./styles";
import StatusPage from "./StatusPage";
import ChatPage from "./ChatPage";
import DocumentsPage from "./DocumentsPage";

const TABS = [
  { key: "chat", label: "💬 Chat RAG" },
  { key: "docs", label: "📋 Documentos" },
  { key: "status", label: "🔍 Estado" },
] as const;

type TabKey = typeof TABS[number]["key"];

export default function App() {
  const [tab, setTab] = useState<TabKey>("chat");

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div>
          <div style={styles.headerTitle}>🎓 RAG Institucional UR</div>
          <div style={styles.headerSubtitle}>
            Prueba de Concepto Local — FastAPI + PostgreSQL + Azure AI Foundry
          </div>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#a0a0b8" }}>FASE G</div>
      </header>

      <div style={styles.tabs}>
        {TABS.map(t => (
          <button
            key={t.key}
            style={{ ...styles.tab, ...(tab === t.key ? styles.tabActive : {}) }}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "chat" && <ChatPage />}
      {tab === "docs" && <DocumentsPage />}
      {tab === "status" && <StatusPage />}
    </div>
  );
}