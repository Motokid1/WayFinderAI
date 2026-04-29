import { useState } from "react";

const initialFormData = {
  destination: "Hyderabad",
  days: 2,
  budget: 10000,
  travel_style: "comfort",
  food_preference: "mixed",
  source_city: "Vijayawada",
  interests: "clubs, pubs, nightlife, cafes",
  news_required: true,
  news_limit: 5,
  risk_check: true,
};

function TravelForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState(initialFormData);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setFormData((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? checked
          : name === "days" || name === "budget" || name === "news_limit"
            ? Number(value)
            : value,
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const payload = {
      ...formData,
      interests: formData.interests
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    };

    onSubmit(payload);
  };

  return (
    <form className="planner-card travel-form" onSubmit={handleSubmit}>
      <div className="form-title">
        <span className="soft-label">Trip details</span>
        <h2>Create your plan</h2>
        <p>Tell us where you are going and what kind of experience you want.</p>
      </div>

      <div className="form-group">
        <label>Destination</label>
        <input
          type="text"
          name="destination"
          value={formData.destination}
          onChange={handleChange}
          placeholder="Enter destination"
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Duration</label>
          <input
            type="number"
            name="days"
            min="1"
            max="15"
            value={formData.days}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Budget</label>
          <input
            type="number"
            name="budget"
            min="500"
            value={formData.budget}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="form-group">
        <label>Starting from</label>
        <input
          type="text"
          name="source_city"
          value={formData.source_city}
          onChange={handleChange}
          placeholder="Optional"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Travel style</label>
          <select
            name="travel_style"
            value={formData.travel_style}
            onChange={handleChange}
          >
            <option value="budget friendly">Budget</option>
            <option value="comfort">Comfort</option>
            <option value="premium">Premium</option>
            <option value="luxury">Luxury</option>
          </select>
        </div>

        <div className="form-group">
          <label>Food preference</label>
          <select
            name="food_preference"
            value={formData.food_preference}
            onChange={handleChange}
          >
            <option value="veg">Veg</option>
            <option value="non-veg">Non-Veg</option>
            <option value="mixed">Mixed</option>
            <option value="vegan">Vegan</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label>Interests</label>
        <textarea
          name="interests"
          value={formData.interests}
          onChange={handleChange}
          rows="4"
          placeholder="nightlife, cafes, shopping, historical places"
        />
        <p className="input-hint">Separate interests using commas.</p>
      </div>

      <div className="toggle-card">
        <label>
          <input
            type="checkbox"
            name="news_required"
            checked={formData.news_required}
            onChange={handleChange}
          />
          <span>
            <strong>Include local updates</strong>
            <small>Check recent destination activity and alerts.</small>
          </span>
        </label>
      </div>

      <div className="toggle-card">
        <label>
          <input
            type="checkbox"
            name="risk_check"
            checked={formData.risk_check}
            onChange={handleChange}
          />
          <span>
            <strong>Include safety review</strong>
            <small>Assess travel risk using available context.</small>
          </span>
        </label>
      </div>

      <button type="submit" className="primary-action" disabled={loading}>
        {loading ? "Preparing your plan..." : "Generate itinerary"}
      </button>
    </form>
  );
}

export default TravelForm;
