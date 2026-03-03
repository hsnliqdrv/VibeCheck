import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { forgotPassword } from "./services/api";

export default function ForgotPassword() {
  const { register, handleSubmit } = useForm();
  const [status, setStatus] = useState({ loading: false, error: "", success: "" });

  const onSubmit = async (data) => {
    setStatus({ loading: true, error: "", success: "" });
    try {
      const response = await forgotPassword(data.email);
      setStatus({
        loading: false,
        error: "",
        success:
          response?.message ||
          "If an account with that email exists, a password reset link has been sent.",
      });
    } catch (error) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.error ||
        error.message ||
        "Failed to process request.";
      setStatus({ loading: false, error: message, success: "" });
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-eyebrow">Account Recovery</p>
          <h2>Forgot Password</h2>
          <p className="auth-subtitle">
            Enter your email and we'll send you a link to reset your password.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="auth-form">
          <label className="auth-label">
            Email
            <input
              {...register("email")}
              type="email"
              placeholder="you@example.com"
              required
            />
          </label>
          {status.error && <div className="auth-message error">{status.error}</div>}
          {status.success && <div className="auth-message success">{status.success}</div>}
          <button className="auth-button" type="submit" disabled={status.loading || status.success}>
            {status.loading ? "Sending..." : "Send Reset Link"}
          </button>
          <p className="auth-footer-text">
            <Link to="/">Back to Login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
