import { Building2, CarFront, MapPin } from "lucide-react";

const StayMobilityCard = ({ stayMobilityPlan }) => {
  const plan = stayMobilityPlan || {};

  const scoring =
    plan.stay_area_scoring_tool?.recommended_stay_areas ||
    plan.stay_area_scoring_tool?.recommended_areas ||
    [];

  const transport = plan.transport_cost_tool || {};
  const safety = plan.mobility_safety_tool || {};

  return (
    <section className="card mobility-card">
      <div className="section-heading">
        <div className="section-icon">
          <Building2 size={18} />
        </div>

        <div>
          <p className="eyebrow">Stay & Mobility</p>
          <h2>Area Strategy</h2>
        </div>
      </div>

      {scoring.length > 0 ? (
        <div className="stay-list">
          {scoring.slice(0, 3).map((area, index) => (
            <div className="stay-item" key={`${area.area_name}-${index}`}>
              <div className="stay-score">{area.score || index + 1}</div>

              <div>
                <h3>{area.area_name || "Recommended Area"}</h3>
                <p>
                  {area.stay_advice || "Suitable area based on trip context."}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">Stay-area scoring is limited for this response.</p>
      )}

      <div className="mobility-summary">
        <div>
          <CarFront size={17} />
          <span>
            {transport.transport_pattern
              ? `Transport pattern: ${transport.transport_pattern}`
              : "Transport pattern unavailable"}
          </span>
        </div>

        <div>
          <MapPin size={17} />
          <span>
            {safety.mobility_safety_level
              ? `Mobility safety: ${safety.mobility_safety_level}`
              : "Mobility safety details unavailable"}
          </span>
        </div>
      </div>

      {transport.budget_impact && (
        <p className="budget-note">{transport.budget_impact}</p>
      )}
    </section>
  );
};

export default StayMobilityCard;
