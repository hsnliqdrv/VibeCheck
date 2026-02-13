import { BrowserRouter as Router, Routes, Route, Link, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Login from "./Login";
import Register from "./Register";
import { StoryGenerator } from "./components/stories";
import "./App.css";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("token"));

  useEffect(() => {
    const checkAuth = () => setIsAuthenticated(!!localStorage.getItem("token"));
    window.addEventListener("storage", checkAuth);
    return () => window.removeEventListener("storage", checkAuth);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setIsAuthenticated(false);
  };

  const handleAuthSuccess = () => setIsAuthenticated(true);

  return (
    <Router>
      <div className="app-wrapper">
        <nav className="app-nav">
          <div className="nav-container">
            <div className="brand">
              <span className="brand-mark">VC</span>
              <div className="brand-info">
                <p className="brand-name">VibeCheck</p>
                <p className="brand-tag">Aesthetic Social Companion</p>
              </div>
            </div>
            <div className="nav-links">
              {!isAuthenticated ? (
                <>
                  <Link to="/" className="nav-item">Login</Link>
                  <Link to="/register" className="nav-item">Register</Link>
                </>
              ) : (
                <>
                  <Link to="/stories" className="nav-item">Stories</Link>
                  <button onClick={handleLogout} className="logout-btn">Logout</button>
                </>
              )}
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={isAuthenticated ? <Navigate to="/stories" /> : <Login onLoginSuccess={handleAuthSuccess} />} />
            <Route path="/register" element={isAuthenticated ? <Navigate to="/stories" /> : <Register onRegisterSuccess={handleAuthSuccess} />} />
            <Route path="/stories" element={isAuthenticated ? <StoryGenerator /> : <Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
