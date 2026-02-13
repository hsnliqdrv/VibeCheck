import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API_BASE_URL = "http://localhost:3000";

export default function Login({ onLoginSuccess }) {
  const { register, handleSubmit } = useForm();
  const navigate = useNavigate();
  const [status, setStatus] = useState({ loading: false, error: "", success: "" });

const onSubmit = async (data) => {
    console.log("Клик сработал! Данные формы:", data);
    setStatus({ loading: true, error: "", success: "" });
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, data);     
      const { token, user } = response.data || {};

      if (!token || !user) throw new Error("Unexpected response format.");

      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      
      onLoginSuccess();
      navigate("/stories");
    } catch (error) {
      console.error("Ошибка при входе:", error);
      const message = error.response?.data?.message || "Login failed.";
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
            <input {...register("email")} type="email" placeholder="you@example.com" required />
          </label>
          <label className="auth-label">
            Password
            <input {...register("password")} type="password" placeholder="Enter your password" required />
          </label>
          {status.error && <div className="auth-message error">{status.error}</div>}
          <button className="auth-button" type="submit" disabled={status.loading}>
            {status.loading ? "Signing in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
