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

  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
  };

  return (
    <Router>
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
            {!isAuthenticated ? (
              <>
                <Link to="/">Login</Link>
                <Link to="/register">Register</Link>
              </>
            ) : (
              <>
                <Link to="/stories">Stories</Link>
                <button onClick={handleLogout} className="logout-btn">Logout</button>
              </>
            )}
          </div>
        </nav>

        <Routes>
          <Route 
            path="/" 
            element={isAuthenticated ? <Navigate to="/stories" /> : <Login onLoginSuccess={handleAuthSuccess} />} 
          />
          <Route 
            path="/register" 
            element={isAuthenticated ? <Navigate to="/stories" /> : <Register onRegisterSuccess={handleAuthSuccess} />} 
          />
          <Route 
            path="/stories" 
            element={isAuthenticated ? <StoryGenerator /> : <Navigate to="/" />} 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
