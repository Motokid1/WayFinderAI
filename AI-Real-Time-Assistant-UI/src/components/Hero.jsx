import { CloudSun, IndianRupee, MapPinned, Route } from "lucide-react";

const Hero = () => {
  return (
    <section className="hero-card">
      <div className="hero-badge">Client-ready AI travel planning platform</div>

      <h2>
        Plan smarter trips with real-time intelligence, budget control, and
        local safety context.
      </h2>

      <p>
        WayFinderAI creates personalized itineraries using live weather, dynamic
        places, mobility insights, budget estimation, and safety signals.
      </p>

      <div className="hero-metrics">
        <div>
          <MapPinned size={20} />
          <span>Dynamic Places</span>
        </div>

        <div>
          <IndianRupee size={20} />
          <span>Budget-Aware</span>
        </div>

        <div>
          <CloudSun size={20} />
          <span>Weather Context</span>
        </div>

        <div>
          <Route size={20} />
          <span>Mobility Planning</span>
        </div>
      </div>
    </section>
  );
};

export default Hero;
