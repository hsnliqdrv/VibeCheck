import { useState, useEffect } from "react";
import { getMyShares } from "./services/api";
import { Grid, LogOut, Heart } from "lucide-react";
import StoryCard from "./components/stories/StoryCard";
import "./Profile.css";

export default function Profile() {
  const [shares, setShares] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  useEffect(() => {
    const fetchShares = async () => {
      try {
        const data = await getMyShares();
        setShares(data);
      } catch (err) {
        console.error("Error fetching shares:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchShares();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.dispatchEvent(new Event("auth-changed"));
    window.location.href = "/";
  };

  return (
    <div className="profile-gradient-wrapper">
      <div className="profile-glass">
        
        {/* HEADER */}
        <header className="profile-header">
          <div className="profile-avatar-wrapper">
            <div className="profile-avatar">
              <span>
                {user.username?.charAt(0).toUpperCase() || "V"}
              </span>
            </div>
          </div>

          <div className="profile-details">
            <div className="profile-title-row">
              <h2 className="profile-username">
                {user.username || "vibe_user"}
              </h2>
              <button
                className="profile-logout-icon"
                onClick={handleLogout}
                title="Logout"
              >
                <LogOut size={20} />
              </button>
            </div>

            <div className="profile-stats">
              <div className="stat-item">
                <strong>{shares.length}</strong> posts
              </div>
              <div className="stat-item">
                <strong>1.2k</strong> followers
              </div>
              <div className="stat-item">
                <strong>450</strong> following
              </div>
            </div>

            <div className="profile-bio">
              <p className="bio-name">{user.username}</p>
              <p className="bio-text">
                Digital Curator of Aesthetics ✨ | Capturing vibes one aura at a time.
              </p>
            </div>
          </div>
        </header>

        {/* TABS */}
        <div className="profile-tabs">
          <div className="tab-item active">
            <Grid size={16} /> POSTS
          </div>
          <div className="tab-item">
            <Heart size={16} /> SAVED
          </div>
        </div>

        {/* GRID */}
        <div className="profile-grid">
          {loading ? (
            <div className="profile-loader">Loading vibes...</div>
          ) : shares.length > 0 ? (
            shares.map((share) => (
              <div key={share.id} className="profile-post-card">
                <div className="post-preview-scale">
                  <StoryCard
                    category={share.category}
                    content={share.content}
                    caption={share.caption}
                    customStyle={share.customStyle || {}}
                  />
                </div>
              </div>
            ))
          ) : (
            <div className="profile-empty">
              <p>No vibes shared yet. Start creating!</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
