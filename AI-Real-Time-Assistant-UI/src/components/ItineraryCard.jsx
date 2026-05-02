import { CalendarCheck } from "lucide-react";

const formatDayTitle = (key) => {
  return key.replace("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
};

const ItineraryCard = ({ itinerary }) => {
  const days = Object.entries(itinerary || {});

  return (
    <section className="card itinerary-card">
      <div className="section-heading">
        <div className="section-icon">
          <CalendarCheck size={18} />
        </div>

        <div>
          <p className="eyebrow">Personalized Schedule</p>
          <h2>Recommended Itinerary</h2>
        </div>
      </div>

      {days.length === 0 ? (
        <p className="muted">No itinerary available.</p>
      ) : (
        <div className="timeline">
          {days.map(([dayKey, activities]) => (
            <div className="timeline-day" key={dayKey}>
              <div className="timeline-dot" />

              <div className="timeline-content">
                <h3>{formatDayTitle(dayKey)}</h3>

                <ul>
                  {(activities || []).map((activity, index) => (
                    <li key={`${dayKey}-${index}`}>{activity}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default ItineraryCard;
