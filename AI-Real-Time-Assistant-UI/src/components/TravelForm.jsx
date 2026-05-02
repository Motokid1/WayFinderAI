import {
  CalendarDays,
  IndianRupee,
  MapPin,
  Plane,
  Search,
  Users,
} from "lucide-react";

const TravelForm = ({ formData, setFormData, onSubmit, isLoading }) => {
  const updateField = (field, value) => {
    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  return (
    <section className="form-card">
      <div className="section-heading">
        <div className="section-icon">
          <Plane size={18} />
        </div>

        <div>
          <p className="eyebrow">Trip Request</p>
          <h2>Create a travel plan</h2>
        </div>
      </div>

      <form onSubmit={onSubmit} className="travel-form">
        <div className="form-grid two">
          <label>
            <span>
              <MapPin size={15} />
              Destination
            </span>
            <input
              value={formData.destination}
              onChange={(event) =>
                updateField("destination", event.target.value)
              }
              placeholder="Hyderabad"
              required
            />
          </label>

          <label>
            <span>
              <MapPin size={15} />
              Source City
            </span>
            <input
              value={formData.source_city}
              onChange={(event) =>
                updateField("source_city", event.target.value)
              }
              placeholder="Vijayawada"
            />
          </label>
        </div>

        <div className="form-grid three">
          <label>
            <span>
              <CalendarDays size={15} />
              Days
            </span>
            <input
              type="number"
              min="1"
              max="10"
              value={formData.days}
              onChange={(event) => updateField("days", event.target.value)}
              required
            />
          </label>

          <label>
            <span>
              <Users size={15} />
              Travelers
            </span>
            <input
              type="number"
              min="1"
              max="10"
              value={formData.travelers}
              onChange={(event) => updateField("travelers", event.target.value)}
              required
            />
          </label>

          <label>
            <span>
              <IndianRupee size={15} />
              Budget
            </span>
            <input
              type="number"
              min="1000"
              value={formData.budget}
              onChange={(event) => updateField("budget", event.target.value)}
              required
            />
          </label>
        </div>

        <div className="form-grid two">
          <label>
            <span>Travel Style</span>
            <select
              value={formData.travel_style}
              onChange={(event) =>
                updateField("travel_style", event.target.value)
              }
            >
              <option value="budget">Budget</option>
              <option value="comfort">Comfort</option>
              <option value="premium">Premium</option>
              <option value="luxury">Luxury</option>
            </select>
          </label>

          <label>
            <span>Food Preference</span>
            <select
              value={formData.food_preference}
              onChange={(event) =>
                updateField("food_preference", event.target.value)
              }
            >
              <option value="veg">Vegetarian</option>
              <option value="non-veg">Non-Vegetarian</option>
              <option value="mixed">Mixed</option>
              <option value="local">Local Cuisine</option>
            </select>
          </label>
        </div>

        <label>
          <span>Interests</span>
          <textarea
            value={formData.interests}
            onChange={(event) => updateField("interests", event.target.value)}
            placeholder="cafes, nightlife, food, heritage, shopping"
            rows="3"
          />
          <small>Separate interests using commas.</small>
        </label>

        <div className="advanced-options">
          <label className="check-row">
            <input
              type="checkbox"
              checked={formData.news_required}
              onChange={(event) =>
                updateField("news_required", event.target.checked)
              }
            />
            <span>Include live news and local trend signals</span>
          </label>

          <label className="check-row">
            <input
              type="checkbox"
              checked={formData.risk_check}
              onChange={(event) =>
                updateField("risk_check", event.target.checked)
              }
            />
            <span>Include travel risk and safety analysis</span>
          </label>
        </div>

        <button type="submit" className="primary-button" disabled={isLoading}>
          <Search size={18} />
          {isLoading ? "Generating Plan..." : "Generate Travel Plan"}
        </button>
      </form>
    </section>
  );
};

export default TravelForm;
