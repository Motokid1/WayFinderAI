function TipsCard({ foodSuggestions, travelTips, safetyTips }) {
  return (
    <section className="planner-card" id="safety">
      <div className="section-heading">
        <div>
          <span className="soft-label">Recommendations</span>
          <h2>Smart trip notes</h2>
        </div>
      </div>

      <div className="tips-layout">
        <TipColumn title="Food" items={foodSuggestions} />
        <TipColumn title="Travel" items={travelTips} />
        <TipColumn title="Safety" items={safetyTips} />
      </div>
    </section>
  );
}

function TipColumn({ title, items }) {
  return (
    <div className="tip-column">
      <h3>{title}</h3>
      {items?.length > 0 ? (
        <ul>
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No specific notes available.</p>
      )}
    </div>
  );
}

export default TipsCard;
