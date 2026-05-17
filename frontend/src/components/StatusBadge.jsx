const LABELS = {
  ok: "Operationnel",
  degraded: "Degrade",
  error: "Critique"
};

export default function StatusBadge({ status = "unknown", children }) {
  const normalized = String(status || "unknown").toLowerCase();
  const label = children || LABELS[normalized] || "Inconnu";

  return <span className={`status-badge status-badge--${normalized}`}>{label}</span>;
}
