export default function KpiCard({ label, value, note, tone = "blue" }) {
  return (
    <article className={`kpi-card kpi-card--${tone}`}>
      <p className="kpi-card__label">{label}</p>
      <p className="kpi-card__value">{value}</p>
      <p className="kpi-card__note">{note}</p>
    </article>
  );
}
