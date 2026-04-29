function RiskCard({ risk }) {
  if (!risk) return null;

  const level = risk.risk_level || "Unknown";

  const chipClass =
    level.toLowerCase() === "high"
      ? "danger"
      : level.toLowerCase() === "medium"
        ? "warning"
        : "success";

  return (
    <article className="insight-card">
      <div className="card-header">
        <span className="icon-badge">🛡️</span>
        <div>
          <span className="soft-label">Safety</span>
          <h3>Travel risk</h3>
        </div>
      </div>

      <div className={`status-chip ${chipClass}`}>{level}</div>

      <p className="card-note">{risk.reason || "No risk reason available."}</p>

      {risk.risk_factors?.length > 0 && (
        <ul className="compact-list">
          {risk.risk_factors.map((factor, index) => (
            <li key={index}>{factor}</li>
          ))}
        </ul>
      )}
    </article>
  );
}

export default RiskCard;
