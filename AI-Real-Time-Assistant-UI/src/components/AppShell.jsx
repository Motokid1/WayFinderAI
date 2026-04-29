function AppShell({ children, serviceStatus }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">W</div>
          <div>
            <h1>WayFinder</h1>
            <p>Travel planning, refined.</p>
          </div>
        </div>

        <nav className="topnav">
          <a href="#planner">Planner</a>
          <a href="#insights">Insights</a>
          <a href="#safety">Safety</a>
        </nav>

        <div className={`service-pill ${serviceStatus}`}>
          <span></span>
          {serviceStatus === "online"
            ? "Service online"
            : serviceStatus === "offline"
              ? "Service offline"
              : "Checking service"}
        </div>
      </header>

      <main id="planner">{children}</main>
    </div>
  );
}

export default AppShell;
