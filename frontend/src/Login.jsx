import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { login as loginUser } from "./services/api";

export default function Login() {
  const { register, handleSubmit } = useForm();
  const [status, setStatus] = useState({ loading: false, error: "", success: "" });
  const navigate = useNavigate();

  useEffect(() => {
    if (localStorage.getItem("token")) {
      navigate("/stories");
    }
  }, [navigate]);

  const onSubmit = async (data) => {
    setStatus({ loading: true, error: "", success: "" });

    try {
      const response = await loginUser(data);
      const { token, user } = response || {};

      if (!token || !user) {
        throw new Error("Unexpected response format.");
      }

      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      setStatus({ loading: false, error: "", success: `Welcome back, ${user.username}!` });
      window.dispatchEvent(new Event("auth-changed"));
      navigate("/stories");
    } catch (error) {
      let message =
        error.response?.data?.message ||
        error.response?.data?.error ||
        error.message ||
        "Login failed.";

      // 403 = email not verified
      if (error.response?.status === 403) {
        message =
          error.response?.data?.message ||
          "Your email is not verified. Please check your inbox for a verification link.";
      }

      setStatus({ loading: false, error: message, success: "" });
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-eyebrow">Welcome back</p>
          <h2>Login</h2>
          <p className="auth-subtitle">Sign in to continue building your vibe.</p>
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
          <label className="auth-label">
            Password
            <input
              {...register("password")}
              type="password"
              placeholder="Enter your password"
              required
            />
          </label>
          {status.error && <div className="auth-message error">{status.error}</div>}
          {status.success && <div className="auth-message success">{status.success}</div>}
          <button className="auth-button" type="submit" disabled={status.loading}>
            {status.loading ? "Signing in..." : "Login"}
          </button>
          <p className="auth-footer-text">
            <Link to="/forgot-password">Forgot password?</Link>
          </p>
          <p className="auth-footer-text">
            Don't have an account? <Link to="/register">Register</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
