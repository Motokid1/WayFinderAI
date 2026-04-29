function LoadingSpinner() {
  return (
    <div className="loading-card">
      <div className="spinner"></div>
      <h3>Generating your AI travel plan...</h3>
      <p>
        Checking weather, budget, RAG city guide, live news, sentiment, and
        travel risk.
      </p>
    </div>
  );
}

export default LoadingSpinner;
