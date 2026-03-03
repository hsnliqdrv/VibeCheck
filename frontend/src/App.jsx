import { useCallback, useEffect, useRef, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from "react-router-dom";
import Login from "./Login";
import Register from "./Register";
import VerifyEmail from "./VerifyEmail";
import ForgotPassword from "./ForgotPassword";
import ResetPassword from "./ResetPassword";
import Profile from "./Profile";
import { StoryGenerator } from "./components/stories";
import BadgesPage from "./badges/Badges";
import DiscoverPage from "./discover/Discover";
import Rooms from "./social/Rooms";
import "./App.css";

function UnauthorizedPopup({ visible, onClose }) {
  if (!visible) return null;
  return (
    <div className="unauthorized-overlay" onClick={onClose}>
      <div className="unauthorized-popup" onClick={(e) => e.stopPropagation()}>
        <h3>Session Expired</h3>
        <p>You have been logged out. Please log in again.</p>
        <button className="auth-button" onClick={onClose}>
          Go to Login
        </button>
      </div>
    </div>
  );
}

function AppShell() {
  const [isAuthed, setIsAuthed] = useState(() => Boolean(localStorage.getItem("token")));
  const [showUnauthorized, setShowUnauthorized] = useState(false);
  const navigate = useNavigate();

  const syncAuthState = useCallback(() => {
    setIsAuthed(Boolean(localStorage.getItem("token")));
  }, []);

  const hadTokenRef = useRef(Boolean(localStorage.getItem("token")));

  useEffect(() => {
    syncAuthState();

    const handleStorage = (event) => {
      if (event.key === "token") syncAuthState();
    };
    const handleAuthChanged = () => {
      syncAuthState();
      hadTokenRef.current = Boolean(localStorage.getItem("token"));
    };
    const handleUnauthorized = () => {
      setShowUnauthorized(true);
    };

    // poll for same-tab token removal
    const pollInterval = setInterval(() => {
      const hasToken = Boolean(localStorage.getItem("token"));
      if (hadTokenRef.current && !hasToken) {
        localStorage.removeItem("user");
        window.dispatchEvent(new Event("auth-changed"));
        setShowUnauthorized(true);
      }
      hadTokenRef.current = hasToken;
    }, 500);

    window.addEventListener("storage", handleStorage);
    window.addEventListener("auth-changed", handleAuthChanged);
    window.addEventListener("show-unauthorized-popup", handleUnauthorized);
    return () => {
      clearInterval(pollInterval);
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener("auth-changed", handleAuthChanged);
      window.removeEventListener("show-unauthorized-popup", handleUnauthorized);
    };
  }, [syncAuthState]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setIsAuthed(false);
    window.dispatchEvent(new Event("auth-changed"));
    navigate("/");
  };

  const handleDismissUnauthorized = () => {
    setShowUnauthorized(false);
    navigate("/");
  };

  return (
    <div className="app">
      <nav className="app-nav">
        <div className="brand">
          <span className="brand-mark">VC</span>
          <div>
            <p className="brand-name">VibeCheck</p>
            <p className="brand-tag">Aesthetic Social Companion</p>
          </div>
        </div>
        <div className="nav-links">
          {!isAuthed && <Link to="/">Login</Link>}
          {!isAuthed && <Link to="/register">Register</Link>}
          {isAuthed && <Link to="/stories">Stories</Link>}
          {isAuthed && <Link to="/discover">Discover</Link>}
          {isAuthed && <Link to="/rooms">Rooms</Link>}
          {isAuthed && <Link to="/badges">Badges</Link>}
          {isAuthed && <Link to="/profile">Profile</Link>}
          {isAuthed && (
            <button type="button" className="nav-link-button" onClick={handleLogout}>
              Logout
            </button>
          )}
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/stories" element={<StoryGenerator />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/rooms" element={<Rooms />} />
        <Route path="/badges" element={<BadgesPage />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>

      <UnauthorizedPopup
        visible={showUnauthorized}
        onClose={handleDismissUnauthorized}
      />
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppShell />
    </Router>
  );
}
