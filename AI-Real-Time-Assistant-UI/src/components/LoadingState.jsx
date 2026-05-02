import { Loader2 } from "lucide-react";

const LoadingState = () => {
  return (
    <section className="loading-card">
      <div className="loader-ring">
        <Loader2 size={34} />
      </div>

      <h2>Building your intelligent travel plan</h2>

      <p>
        WayFinderAI is checking destination context, weather, places, budget,
        mobility, and safety signals.
      </p>

      <div className="loading-steps">
        <span>Analyzing destination</span>
        <span>Estimating budget</span>
        <span>Building itinerary</span>
      </div>
    </section>
  );
};

export default LoadingState;
