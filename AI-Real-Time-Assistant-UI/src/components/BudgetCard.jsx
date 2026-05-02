import React from "react";

const formatCurrency = (value) => {
  const amount = Number(value || 0);

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
};

const getEstimateValue = (costBreakdown) => {
  if (!costBreakdown) return 0;

  if (costBreakdown.total_estimated_cost) {
    return costBreakdown.total_estimated_cost;
  }

  if (costBreakdown.total_estimate?.expected) {
    return costBreakdown.total_estimate.expected;
  }

  if (costBreakdown.total_estimate?.high) {
    return costBreakdown.total_estimate.high;
  }

  return 0;
};

const getCategoryTotals = (costBreakdown) => {
  const categoryTotals = costBreakdown?.category_totals || {};

  return {
    accommodation:
      categoryTotals.accommodation ||
      categoryTotals.stay ||
      categoryTotals.hotel ||
      0,

    food: categoryTotals.food || categoryTotals.meals || 0,

    transport:
      categoryTotals.local_transport ||
      categoryTotals.transport ||
      categoryTotals.travel ||
      0,

    activities:
      categoryTotals.activities ||
      categoryTotals.activity ||
      categoryTotals.sightseeing ||
      categoryTotals.interest_extra ||
      0,
  };
};

const getBudgetStatusLabel = (costBreakdown, totalEstimate, userBudget) => {
  const status = costBreakdown?.budget_status;

  if (status === "within_budget") return "Within planned budget";
  if (status === "near_budget") return "Close to planned budget";
  if (status === "over_budget") return "Above planned budget";

  if (userBudget && totalEstimate > userBudget) {
    return "Above planned budget";
  }

  return "Within planned budget";
};

const BudgetCard = ({ costBreakdown, budget }) => {
  const totalEstimate = getEstimateValue(costBreakdown);
  const categoryTotals = getCategoryTotals(costBreakdown);

  const userBudget = Number(
    budget || costBreakdown?.user_budget || costBreakdown?.budget || 0,
  );

  const statusLabel = getBudgetStatusLabel(
    costBreakdown,
    totalEstimate,
    userBudget,
  );

  const isOverBudget =
    costBreakdown?.within_budget === false ||
    costBreakdown?.budget_status === "over_budget" ||
    (userBudget > 0 && totalEstimate > userBudget);

  const budgetNote =
    costBreakdown?.budget_note ||
    costBreakdown?.note ||
    `The expected estimate for this trip is around ${formatCurrency(
      totalEstimate,
    )}${
      userBudget
        ? `, compared with your planned budget of ${formatCurrency(userBudget)}`
        : ""
    }. Budget confidence: ${costBreakdown?.confidence || "medium"}.`;

  return (
    <section className="budget-card">
      <div className="section-heading">
        <div className="section-icon">₹</div>

        <div>
          <p className="eyebrow">Budget</p>
          <h2>Cost estimate</h2>
        </div>
      </div>

      <div className="budget-total">{formatCurrency(totalEstimate)}</div>

      <div
        className={`budget-status ${
          isOverBudget ? "budget-status-warning" : "budget-status-success"
        }`}
      >
        {statusLabel}
      </div>

      <div className="budget-lines">
        <div className="budget-line">
          <span>Accommodation</span>
          <strong>{formatCurrency(categoryTotals.accommodation)}</strong>
        </div>

        <div className="budget-line">
          <span>Food</span>
          <strong>{formatCurrency(categoryTotals.food)}</strong>
        </div>

        <div className="budget-line">
          <span>Transport</span>
          <strong>{formatCurrency(categoryTotals.transport)}</strong>
        </div>

        <div className="budget-line">
          <span>Activities</span>
          <strong>{formatCurrency(categoryTotals.activities)}</strong>
        </div>
      </div>

      <p className="budget-note">{budgetNote}</p>

      {costBreakdown?.recommendations?.length > 0 && (
        <div className="budget-recommendations">
          <h4>Budget suggestions</h4>

          <ul>
            {costBreakdown.recommendations.slice(0, 4).map((item, index) => (
              <li key={`budget-rec-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {costBreakdown?.saving_plan?.length > 0 && (
        <div className="budget-recommendations">
          <h4>Saving plan</h4>

          <ul>
            {costBreakdown.saving_plan.slice(0, 4).map((item, index) => (
              <li key={`saving-plan-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

export default BudgetCard;
