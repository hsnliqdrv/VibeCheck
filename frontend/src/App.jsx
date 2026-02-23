import { useCallback, useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from "react-router-dom";
import Login from "./Login";
import Register from "./Register";
import Profile from "./Profile";
import { StoryGenerator } from "./components/stories";
import BadgesPage from "./badges/Badges";
import DiscoverPage from "./discover/Discover";
import "./App.css";

function AppShell() {
  const [isAuthed, setIsAuthed] = useState(() => Boolean(localStorage.getItem("token")));
  const navigate = useNavigate();

  const syncAuthState = useCallback(() => {
    setIsAuthed(Boolean(localStorage.getItem("token")));
  }, []);

  useEffect(() => {
    syncAuthState();
    const handleStorage = (event) => {
      if (event.key === "token") syncAuthState();
    };
    const handleAuthChanged = () => syncAuthState();
    window.addEventListener("storage", handleStorage);
    window.addEventListener("auth-changed", handleAuthChanged);
    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener("auth-changed", handleAuthChanged);
    };
  }, [syncAuthState]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setIsAuthed(false);
    window.dispatchEvent(new Event("auth-changed"));
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
        <Route path="/stories" element={<StoryGenerator />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/badges" element={<BadgesPage />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
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
