import { Compass, ShieldCheck, Sparkles } from "lucide-react";

const Header = () => {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">
          <Compass size={22} />
        </div>

        <div>
          <h1>WayFinderAI</h1>
          <p>Real-Time Travel Intelligence</p>
        </div>
      </div>

      <div className="topbar-badges">
        <span>
          <Sparkles size={15} />
          AI Planner
        </span>

        <span>
          <ShieldCheck size={15} />
          Safety-Aware
        </span>
      </div>
    </header>
  );
};

export default Header;
