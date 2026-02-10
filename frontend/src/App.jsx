import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Login from "./Login";
import Register from "./Register";
import "./App.css";

function App() {
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
            <Link to="/">Login</Link>
            <Link to="/register">Register</Link>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
