import { useState } from "react";
import { useForm } from "react-hook-form";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function Login() {
  const { register, handleSubmit } = useForm();
  const [status, setStatus] = useState({ loading: false, error: "", success: "" });

  const onSubmit = async (data) => {
    setStatus({ loading: true, error: "", success: "" });

    try {
      const response = await axios.post(`${API_BASE_URL}/auth/login`, data);
      const { token, user } = response.data || {};

      if (!token || !user) {
        throw new Error("Unexpected response format.");
      }

      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      setStatus({ loading: false, error: "", success: `Welcome back, ${user.username}!` });
    } catch (error) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.error ||
        error.message ||
        "Login failed.";
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
        </form>
      </div>
    </div>
  );
}
