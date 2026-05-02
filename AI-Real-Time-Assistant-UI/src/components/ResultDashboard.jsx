import BudgetCard from "./BudgetCard";
import ItineraryCard from "./ItineraryCard";
import InsightCards from "./InsightCards";
import PlacesCard from "./PlacesCard";
import StayMobilityCard from "./StayMobilityCard";

const ResultDashboard = ({ travelPlan }) => {
  return (
    <section className="result-dashboard">
      <div className="result-header">
        <div>
          <p className="eyebrow">Generated Plan</p>
          <h2>{travelPlan.destination}</h2>
          <p>
            {travelPlan.days} day{travelPlan.days > 1 ? "s" : ""} •{" "}
            {travelPlan.travelers} traveler
            {travelPlan.travelers > 1 ? "s" : ""} • {travelPlan.travel_style}{" "}
            travel
          </p>
        </div>

        <div className="status-pill">Ready</div>
      </div>

      {travelPlan.final_summary && (
        <div className="summary-card">
          <h3>Executive Summary</h3>
          <p>{travelPlan.final_summary}</p>
        </div>
      )}

      <div className="dashboard-grid">
        <BudgetCard
          costBreakdown={travelPlan.cost_breakdown}
          budget={travelPlan.budget}
        />

        <InsightCards travelPlan={travelPlan} />
      </div>

      <ItineraryCard itinerary={travelPlan.itinerary} />

      <div className="dashboard-grid">
        <PlacesCard places={travelPlan.discovered_places} />
        <StayMobilityCard stayMobilityPlan={travelPlan.stay_mobility_plan} />
      </div>
    </section>
  );
};

export default ResultDashboard;
