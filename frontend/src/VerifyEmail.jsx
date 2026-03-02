import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { verifyEmail } from "./services/api";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState({ loading: true, error: "", success: "" });

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus({ loading: false, error: "No verification token provided.", success: "" });
      return;
    }

    (async () => {
      try {
        const response = await verifyEmail(token);
        // If the backend returns a JWT on verify, store it
        if (response?.token && response?.user) {
          localStorage.setItem("token", response.token);
          localStorage.setItem("user", JSON.stringify(response.user));
          window.dispatchEvent(new Event("auth-changed"));
        }
        setStatus({
          loading: false,
          error: "",
          success: response?.message || "Your email has been verified successfully!",
        });
      } catch (error) {
        const message =
          error.response?.data?.message ||
          error.response?.data?.error ||
          error.message ||
          "Verification failed. The link may be invalid or expired.";
        setStatus({ loading: false, error: message, success: "" });
      }
    })();
  }, [searchParams]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-eyebrow">Email Verification</p>
          <h2>Verify Your Email</h2>
        </div>

        {status.loading && <p className="auth-subtitle">Verifying your email...</p>}
        {status.error && <div className="auth-message error">{status.error}</div>}
        {status.success && (
          <>
            <div className="auth-message success">{status.success}</div>
            <p className="auth-footer-text">
              <Link to="/">Go to Login</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
