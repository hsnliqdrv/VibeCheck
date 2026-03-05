import { useState } from "react";
import { useForm } from "react-hook-form";
import { useSearchParams, Link } from "react-router-dom";
import { resetPassword } from "./services/api";

export default function ResetPassword() {
  const { register, handleSubmit } = useForm();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState({ loading: false, error: "", success: "" });
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const token = searchParams.get("token") || "";

  const onSubmit = async (data) => {
    if (!token) {
      setStatus({ loading: false, error: "Invalid reset link — no token found.", success: "" });
      return;
    }

    if (data.newPassword !== data.confirmPassword) {
      setStatus({ loading: false, error: "Passwords do not match.", success: "" });
      return;
    }

    setStatus({ loading: true, error: "", success: "" });
    try {
      const response = await resetPassword(token, data.newPassword);
      setStatus({
        loading: false,
        error: "",
        success: response?.message || "Your password has been reset successfully!",
      });
    } catch (error) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.error ||
        error.message ||
        "Failed to reset password. The link may be invalid or expired.";
      setStatus({ loading: false, error: message, success: "" });
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-eyebrow">Account Recovery</p>
          <h2>Reset Password</h2>
          <p className="auth-subtitle">Enter your new password below.</p>
        </div>

        {!token ? (
          <>
            <div className="auth-message error">
              Invalid reset link — no token found in the URL.
            </div>
            <p className="auth-footer-text">
              <Link to="/forgot-password">Request a new reset link</Link>
            </p>
          </>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="auth-form">
            <label className="auth-label">
              New Password
              <div style={{ position: 'relative', width: '100%' }}>
                <input
                  {...register("newPassword")}
                  type={showNewPassword ? "text" : "password"}
                  placeholder="Enter new password"
                  required
                  minLength={6}
                  style={{ width: '100%', paddingRight: '50px', boxSizing: 'border-box' }}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
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
                  aria-label={showNewPassword ? "Hide password" : "Show password"}
                >
                  {showNewPassword ? 'HIDE' : 'SHOW'}
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
            <label className="auth-label">
              Confirm Password
              <div style={{ position: 'relative', width: '100%' }}>
                <input
                  {...register("confirmPassword")}
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm new password"
                  required
                  minLength={6}
                  style={{ width: '100%', paddingRight: '50px', boxSizing: 'border-box' }}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
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
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? 'HIDE' : 'SHOW'}
                </button>
              </div>
            </label>
            {status.error && <div className="auth-message error">{status.error}</div>}
            {status.success && (
              <>
                <div className="auth-message success">{status.success}</div>
                <p className="auth-footer-text">
                  <Link to="/">Go to Login</Link>
                </p>
              </>
            )}
            {!status.success && (
              <button className="auth-button" type="submit" disabled={status.loading}>
                {status.loading ? "Resetting..." : "Reset Password"}
              </button>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
