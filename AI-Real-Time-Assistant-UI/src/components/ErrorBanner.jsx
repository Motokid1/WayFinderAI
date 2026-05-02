import { AlertTriangle } from "lucide-react";

const ErrorBanner = ({ message }) => {
  return (
    <section className="error-banner">
      <AlertTriangle size={22} />

      <div>
        <h3>Unable to generate plan</h3>
        <p>{message}</p>
      </div>
    </section>
  );
};

export default ErrorBanner;
