import { MapPinned } from "lucide-react";

const PlacesCard = ({ places }) => {
  const safePlaces = Array.isArray(places) ? places : [];

  return (
    <section className="card places-card">
      <div className="section-heading">
        <div className="section-icon">
          <MapPinned size={18} />
        </div>

        <div>
          <p className="eyebrow">Dynamic Discovery</p>
          <h2>Recommended Places</h2>
        </div>
      </div>

      {safePlaces.length === 0 ? (
        <p className="muted">
          No dynamic places were returned for this request.
        </p>
      ) : (
        <div className="places-list">
          {safePlaces.slice(0, 8).map((place, index) => (
            <div className="place-item" key={`${place.name}-${index}`}>
              <div>
                <h3>{place.name || "Unnamed Place"}</h3>
                <p>{place.address || "Address unavailable"}</p>
              </div>

              <span>{place.category || "place"}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default PlacesCard;
