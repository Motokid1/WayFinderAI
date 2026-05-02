import {
  CloudSun,
  Newspaper,
  ShieldCheck,
  Utensils,
  AlertCircle,
} from "lucide-react";

const normalizeList = (value) => {
  if (!value) return [];

  if (Array.isArray(value)) {
    return value.map((item) =>
      typeof item === "string" ? item : JSON.stringify(item),
    );
  }

  return [String(value)];
};

const InsightBlock = ({ icon, title, children }) => {
  return (
    <div className="insight-block">
      <div className="insight-title">
        {icon}
        <h3>{title}</h3>
      </div>

      {children}
    </div>
  );
};

const InsightCards = ({ travelPlan }) => {
  const foodSuggestions = normalizeList(travelPlan?.food_suggestions);
  const travelTips = normalizeList(travelPlan?.travel_tips);
  const safetyTips = normalizeList(travelPlan?.safety_tips);
  const limitations = normalizeList(travelPlan?.data_limitations);
  const localTrends = normalizeList(travelPlan?.local_trends);

  const weatherText =
    travelPlan?.weather_summary?.summary ||
    travelPlan?.weather_summary?.description ||
    travelPlan?.weather_summary?.weather ||
    "Weather details are limited for this destination.";

  return (
    <section className="card insight-card">
      <div className="section-heading">
        <div className="section-icon">
          <ShieldCheck size={18} />
        </div>

        <div>
          <p className="eyebrow">Travel Intelligence</p>
          <h2>Context & Safety</h2>
        </div>
      </div>

      <div className="insight-list">
        <InsightBlock icon={<CloudSun size={17} />} title="Weather Context">
          <p>
            {typeof weatherText === "string"
              ? weatherText
              : JSON.stringify(weatherText)}
          </p>
        </InsightBlock>

        {foodSuggestions.length > 0 && (
          <InsightBlock icon={<Utensils size={17} />} title="Food Suggestions">
            <ul>
              {foodSuggestions.slice(0, 4).map((item, index) => (
                <li key={`food-${index}`}>{item}</li>
              ))}
            </ul>
          </InsightBlock>
        )}

        {travelTips.length > 0 && (
          <InsightBlock icon={<Newspaper size={17} />} title="Travel Tips">
            <ul>
              {travelTips.slice(0, 4).map((item, index) => (
                <li key={`tip-${index}`}>{item}</li>
              ))}
            </ul>
          </InsightBlock>
        )}

        {safetyTips.length > 0 && (
          <InsightBlock icon={<ShieldCheck size={17} />} title="Safety Notes">
            <ul>
              {safetyTips.slice(0, 5).map((item, index) => (
                <li key={`safe-${index}`}>{item}</li>
              ))}
            </ul>
          </InsightBlock>
        )}

        {localTrends.length > 0 && (
          <InsightBlock icon={<Newspaper size={17} />} title="Local Trends">
            <ul>
              {localTrends.slice(0, 3).map((item, index) => (
                <li key={`trend-${index}`}>{item}</li>
              ))}
            </ul>
          </InsightBlock>
        )}

        {limitations.length > 0 && (
          <InsightBlock
            icon={<AlertCircle size={17} />}
            title="Data Limitations"
          >
            <ul>
              {limitations.slice(0, 4).map((item, index) => (
                <li key={`limit-${index}`}>{item}</li>
              ))}
            </ul>
          </InsightBlock>
        )}
      </div>
    </section>
  );
};

export default InsightCards;
