function NewsCard({ newsSummary, sentiment, articles, trends }) {
  return (
    <section className="planner-card" id="insights">
      <div className="section-heading">
        <div>
          <span className="soft-label">Local intelligence</span>
          <h2>Destination updates</h2>
        </div>

        <div className="status-chip neutral">{sentiment || "Neutral"}</div>
      </div>

      <p className="section-summary">
        {newsSummary || "No local updates were analyzed for this plan."}
      </p>

      {trends?.length > 0 && (
        <div className="trend-grid">
          {trends.map((trend, index) => (
            <div className="trend-chip" key={index}>
              {trend}
            </div>
          ))}
        </div>
      )}

      {articles?.length > 0 && (
        <div className="article-grid">
          {articles.slice(0, 4).map((article, index) => (
            <article className="article-card" key={index}>
              <span>{article.source || "Local source"}</span>
              <h3>{article.title || "Untitled update"}</h3>
              <p>{article.description || "No description available."}</p>
              {article.url && (
                <a href={article.url} target="_blank" rel="noreferrer">
                  View source
                </a>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default NewsCard;
