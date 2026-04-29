function WeatherCard({ weather }) {
  if (!weather) return null;

  return (
    <article className="insight-card">
      <div className="card-header">
        <span className="icon-badge">☁️</span>
        <div>
          <span className="soft-label">Weather</span>
          <h3>{weather.city || "Destination"}</h3>
        </div>
      </div>

      <div className="large-metric">
        {weather.temperature !== null && weather.temperature !== undefined
          ? `${weather.temperature}°C`
          : "Unavailable"}
      </div>

      <div className="metric-list">
        <div>
          <span>Condition</span>
          <strong>{weather.condition || "Unavailable"}</strong>
        </div>
        <div>
          <span>Feels like</span>
          <strong>
            {weather.feels_like !== null && weather.feels_like !== undefined
              ? `${weather.feels_like}°C`
              : "Unavailable"}
          </strong>
        </div>
        <div>
          <span>Humidity</span>
          <strong>
            {weather.humidity !== null && weather.humidity !== undefined
              ? `${weather.humidity}%`
              : "Unavailable"}
          </strong>
        </div>
      </div>

      <p className="card-note">{weather.recommendation}</p>
    </article>
  );
}

export default WeatherCard;
