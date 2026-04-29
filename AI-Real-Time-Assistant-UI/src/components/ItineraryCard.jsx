function ItineraryCard({ itinerary }) {
  if (!itinerary || Object.keys(itinerary).length === 0) {
    return (
      <section className="planner-card">
        <span className="soft-label">Itinerary</span>
        <h2>No itinerary generated</h2>
      </section>
    );
  }

  return (
    <section className="planner-card">
      <div className="section-heading">
        <div>
          <span className="soft-label">Itinerary</span>
          <h2>Day-by-day plan</h2>
        </div>
      </div>

      <div className="timeline">
        {Object.entries(itinerary).map(([day, activities], index) => (
          <div className="timeline-item" key={day}>
            <div className="timeline-marker">{index + 1}</div>
            <div className="timeline-content">
              <h3>{formatDay(day)}</h3>
              <ul>
                {activities.map((activity, activityIndex) => (
                  <li key={activityIndex}>{activity}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function formatDay(day) {
  return day.replace("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export default ItineraryCard;
