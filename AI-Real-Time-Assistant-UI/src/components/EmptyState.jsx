import { Map } from "lucide-react";

const EmptyState = () => {
  return (
    <section className="empty-state">
      <div className="empty-icon">
        <Map size={42} />
      </div>

      <h2>Your travel intelligence dashboard will appear here</h2>

      <p>
        Enter trip details and generate a personalized plan with itinerary,
        budget, mobility, places, weather, and safety insights.
      </p>
    </section>
  );
};

export default EmptyState;
