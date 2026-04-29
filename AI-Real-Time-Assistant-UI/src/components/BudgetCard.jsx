function BudgetCard({ budget }) {
  if (!budget) return null;

  return (
    <article className="insight-card">
      <div className="card-header">
        <span className="icon-badge">₹</span>
        <div>
          <span className="soft-label">Budget</span>
          <h3>Cost estimate</h3>
        </div>
      </div>

      <div className="large-metric">₹{budget.total_estimated_cost || 0}</div>

      <div
        className={`status-chip ${
          budget.within_budget ? "success" : "warning"
        }`}
      >
        {budget.within_budget ? "Within budget" : "Above planned budget"}
      </div>

      <div className="metric-list">
        <div>
          <span>Accommodation</span>
          <strong>₹{budget.accommodation || 0}</strong>
        </div>
        <div>
          <span>Food</span>
          <strong>₹{budget.food || 0}</strong>
        </div>
        <div>
          <span>Transport</span>
          <strong>₹{budget.local_transport || 0}</strong>
        </div>
        <div>
          <span>Activities</span>
          <strong>₹{budget.activities || 0}</strong>
        </div>
        {budget.nightlife_extra !== undefined && (
          <div>
            <span>Nightlife buffer</span>
            <strong>₹{budget.nightlife_extra}</strong>
          </div>
        )}
      </div>

      {budget.budget_note && <p className="card-note">{budget.budget_note}</p>}
    </article>
  );
}

export default BudgetCard;
