import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { login as loginUser } from "./services/api";

export default function Login() {
  const { register, handleSubmit } = useForm();
  const [status, setStatus] = useState({ loading: false, error: "", success: "" });
  const [showPassword, setShowPassword] = useState(false);
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
            <div style={{ position: 'relative', width: '100%' }}>
              <input
                {...register("password")}
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                required
                style={{ width: '100%', paddingRight: '50px', boxSizing: 'border-box' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '11px',
                  color: '#888',
                  padding: '4px 6px',
                  fontWeight: '500',
                  letterSpacing: '0.5px',
                  transition: 'color 0.2s',
                  userSelect: 'none'
                }}
                onMouseEnter={(e) => e.target.style.color = '#555'}
                onMouseLeave={(e) => e.target.style.color = '#888'}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? 'HIDE' : 'SHOW'}
              </button>
            </div>
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
