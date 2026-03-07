import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { register as registerUser } from "./services/api";

export default function Register() {
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
      const response = await registerUser(data);

      setStatus({
        loading: false,
        error: "",
        success:
          response?.message ||
          "Account created! Please check your email to verify your account before logging in.",
      });
    } catch (error) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.error ||
        error.message ||
        "Registration failed.";
      setStatus({ loading: false, error: message, success: "" });
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-eyebrow">Start your aura</p>
          <h2>Register</h2>
          <p className="auth-subtitle">Create a profile that feels like you.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="auth-form">
          <label className="auth-label">
            Username
            <input {...register("username")} placeholder="aesthetic_anna" required />
          </label>
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
                placeholder="Create a strong password"
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
            <div style={{ 
              marginTop: '8px', 
              fontSize: '12px', 
              color: '#666',
              lineHeight: '1.5'
            }}>
              <div style={{ marginBottom: '4px', fontWeight: '500' }}>Password requirements:</div>
              <ul style={{ margin: 0, paddingLeft: '20px' }}>
                <li>At least 8 characters long</li>
                <li>Contains at least one uppercase letter</li>
                <li>Contains at least one lowercase letter</li>
                <li>Contains at least one digit</li>
              </ul>
            </div>
          </label>
          {status.error && <div className="auth-message error">{status.error}</div>}
          {status.success && <div className="auth-message success">{status.success}</div>}
          <button className="auth-button" type="submit" disabled={status.loading || status.success}>
            {status.loading ? "Creating..." : "Create Account"}
          </button>
          <p className="auth-footer-text">
            Already have an account? <Link to="/">Login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
