import { useState } from "react";
import Header from "./components/Header";
import Hero from "./components/Hero";
import TravelForm from "./components/TravelForm";
import ResultDashboard from "./components/ResultDashboard";
import LoadingState from "./components/LoadingState";
import ErrorBanner from "./components/ErrorBanner";
import EmptyState from "./components/EmptyState";
import { createTravelPlan } from "./api/travelApi";

const initialFormData = {
  destination: "Hyderabad",
  days: 2,
  travelers: 1,
  budget: 15000,
  travel_style: "comfort",
  food_preference: "mixed",
  source_city: "Vijayawada",
  interests: "cafes, nightlife, food",
  news_required: false,
  news_limit: 2,
  risk_check: true,
};

function App() {
  const [formData, setFormData] = useState(initialFormData);
  const [travelPlan, setTravelPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState("");

  const buildPayload = () => {
    return {
      destination: formData.destination.trim(),
      days: Number(formData.days),
      travelers: Number(formData.travelers),
      budget: Number(formData.budget),
      travel_style: formData.travel_style,
      food_preference: formData.food_preference,
      source_city: formData.source_city.trim(),
      interests: formData.interests
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      news_required: Boolean(formData.news_required),
      news_limit: Number(formData.news_limit || 2),
      risk_check: Boolean(formData.risk_check),
    };
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setIsLoading(true);
    setApiError("");
    setTravelPlan(null);

    try {
      const payload = buildPayload();
      const result = await createTravelPlan(payload);
      setTravelPlan(result);
    } catch (error) {
      const message =
        error?.response?.data?.detail ||
        error?.message ||
        "Unable to generate travel plan. Please try again.";

      setApiError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <Header />

      <section className="page-grid">
        <div className="left-panel">
          <Hero />

          <TravelForm
            formData={formData}
            setFormData={setFormData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>

        <div className="right-panel">
          {apiError && <ErrorBanner message={apiError} />}

          {isLoading && <LoadingState />}

          {!isLoading && !travelPlan && !apiError && <EmptyState />}

          {!isLoading && travelPlan && (
            <ResultDashboard travelPlan={travelPlan} />
          )}
        </div>
      </section>
    </main>
  );
}

export default App;
