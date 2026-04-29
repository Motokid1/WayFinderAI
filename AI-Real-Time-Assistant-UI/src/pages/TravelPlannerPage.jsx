import { useEffect, useState } from "react";

import { checkBackendHealth, createTravelPlan } from "../api/travelApi";

import AppShell from "../components/AppShell";
import TravelForm from "../components/TravelForm";
import PlanOverview from "../components/PlanOverview";
import WeatherCard from "../components/WeatherCard";
import BudgetCard from "../components/BudgetCard";
import NewsCard from "../components/NewsCard";
import RiskCard from "../components/RiskCard";
import ItineraryCard from "../components/ItineraryCard";
import TipsCard from "../components/TipsCard";
import LoadingState from "../components/LoadingState";

function TravelPlannerPage() {
  const [serviceStatus, setServiceStatus] = useState("checking");
  const [loading, setLoading] = useState(false);
  const [travelPlan, setTravelPlan] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const verifyService = async () => {
      try {
        await checkBackendHealth();
        setServiceStatus("online");
      } catch {
        setServiceStatus("offline");
      }
    };

    verifyService();
  }, []);

  const handleGeneratePlan = async (formData) => {
    setLoading(true);
    setError("");
    setTravelPlan(null);

    try {
      const result = await createTravelPlan(formData);
      setTravelPlan(result);
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        "We could not generate your itinerary right now. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell serviceStatus={serviceStatus}>
      <section className="planner-layout">
        <aside className="planner-sidebar">
          <TravelForm onSubmit={handleGeneratePlan} loading={loading} />
        </aside>

        <section className="planner-content">
          {!loading && !error && !travelPlan && (
            <div className="welcome-panel">
              <div className="welcome-content">
                <span className="soft-label">Personal travel intelligence</span>
                <h1>Build a safer, smarter itinerary in minutes.</h1>
                <p>
                  Enter your destination, budget, travel style, and interests.
                  WayFinder will prepare a practical trip plan with destination
                  conditions, estimated costs, local updates, and safety-aware
                  suggestions.
                </p>

                <div className="welcome-grid">
                  <div>
                    <strong>Personalized</strong>
                    <span>Plans based on your travel interests.</span>
                  </div>
                  <div>
                    <strong>Budget-aware</strong>
                    <span>Cost estimates aligned with your trip style.</span>
                  </div>
                  <div>
                    <strong>Context-aware</strong>
                    <span>Considers weather, local updates, and safety.</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {loading && <LoadingState />}

          {error && (
            <div className="error-panel">
              <span className="soft-label danger">Request failed</span>
              <h2>Something went wrong</h2>
              <p>{error}</p>
              <p className="muted">
                Please check that the backend service is running and try again.
              </p>
            </div>
          )}

          {travelPlan && (
            <div className="results-section">
              <PlanOverview plan={travelPlan} />

              <div className="insight-grid">
                <WeatherCard weather={travelPlan.weather_summary} />
                <BudgetCard budget={travelPlan.cost_breakdown} />
                <RiskCard risk={travelPlan.travel_risk} />
              </div>

              <ItineraryCard itinerary={travelPlan.itinerary} />

              <NewsCard
                newsSummary={travelPlan.news_summary}
                sentiment={travelPlan.news_sentiment}
                articles={travelPlan.news_articles}
                trends={travelPlan.local_trends}
              />

              <TipsCard
                foodSuggestions={travelPlan.food_suggestions}
                travelTips={travelPlan.travel_tips}
                safetyTips={travelPlan.safety_tips}
              />
            </div>
          )}
        </section>
      </section>
    </AppShell>
  );
}

export default TravelPlannerPage;
