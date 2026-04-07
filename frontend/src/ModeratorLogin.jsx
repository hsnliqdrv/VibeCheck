import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { moderatorLogin } from "./services/api";

export default function ModeratorLogin() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState("Verifying moderator link...");

  useEffect(() => {
    const run = async () => {
      if (!token) {
        setMessage("Invalid moderator link.");
        return;
      }

      try {
        const response = await moderatorLogin(token);
        const { user, token: accessToken } = response || {};

        if (!accessToken || !user) {
          throw new Error("Invalid response");
        }

        localStorage.setItem("token", accessToken);
        localStorage.setItem("user", JSON.stringify(user));
        window.dispatchEvent(new Event("auth-changed"));

        setMessage("Moderator access granted. Redirecting...");
        navigate("/stories");
      } catch (_error) {
        setMessage("This moderator link is invalid or has expired.");
      }
    };

    run();
  }, [token, navigate]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-eyebrow">Moderator Access</p>
          <h2>Secure Sign In</h2>
          <p className="auth-subtitle">{message}</p>
        </div>
      </div>
    </div>
  );
}
