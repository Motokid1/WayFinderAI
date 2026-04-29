function PlanOverview({ plan }) {
  const riskLevel = plan?.travel_risk?.risk_level || "Not checked";
  const totalCost = plan?.cost_breakdown?.total_estimated_cost;

  return (
    <section className="overview-card">
      <div>
        <span className="soft-label">Your itinerary</span>
        <h1>{plan.destination} trip plan</h1>
        <p>{plan.final_summary}</p>
      </div>

      <div className="overview-stats">
        <div>
          <span>Duration</span>
          <strong>{plan.days} days</strong>
        </div>
        <div>
          <span>Budget</span>
          <strong>₹{plan.budget}</strong>
        </div>
        <div>
          <span>Estimate</span>
          <strong>{totalCost ? `₹${totalCost}` : "Unavailable"}</strong>
        </div>
        <div>
          <span>Risk</span>
          <strong>{riskLevel}</strong>
        </div>
      </div>
    </section>
  );
}

export default PlanOverview;
