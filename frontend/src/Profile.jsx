import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Clapperboard, Music, Gamepad2, BookOpen, Plane, 
  Star, Flame, Trophy, TrendingUp, Plus, X, Save 
} from "lucide-react";
import {
  getUserProfile,
  updateUserProfile,
  getAuraProfile,
  updateAuraProfile,
  getCuratorProgress,
  getMyShares
} from "./services/api";
import "./Profile.css";

const CATEGORY_ICONS = {
  cinema: Clapperboard,
  music: Music,
  games: Gamepad2,
  books: BookOpen,
  travel: Plane,
};

export default function Profile() {
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState(null);
  const [auraProfile, setAuraProfile] = useState(null);
  const [curatorData, setCuratorData] = useState(null);
  const [shares, setShares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Editing States
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({ bio: "", avatar: "" });
  const [newTag, setNewTag] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const results = await Promise.allSettled([
          getUserProfile(),
          getAuraProfile(),
          getCuratorProgress(),
          getMyShares()
        ]);
        
        if (results[0].status === 'fulfilled') {
          setUserProfile(results[0].value);
          setProfileForm({ 
            bio: results[0].value.bio || "", 
            avatar: results[0].value.avatar || "" 
          });
        }
        if (results[1].status === 'fulfilled') setAuraProfile(results[1].value);
        if (results[2].status === 'fulfilled') setCuratorData(results[2].value);
        if (results[3].status === 'fulfilled') setShares(results[3].value.data || []);

        setError(null);
      } catch (err) {
        setError("Failed to load profile data");
        if (err.response?.status === 401) navigate("/");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [navigate]);

  const handleUpdateProfile = async () => {
    try {
      const updated = await updateUserProfile(profileForm);
      setUserProfile(updated);
      setEditingProfile(false);
    } catch (err) {
      setError("Failed to update profile");
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim()) return;
    const updatedTags = [...(auraProfile?.aestheticTags || []), newTag.trim()];
    try {
      const updated = await updateAuraProfile({ aestheticTags: updatedTags });
      setAuraProfile(updated);
      setNewTag("");
    } catch (err) { setError("Failed to add tag"); }
  };

  const handleRemoveTag = async (tagToRemove) => {
    const updatedTags = (auraProfile?.aestheticTags || []).filter(t => t !== tagToRemove);
    try {
      const updated = await updateAuraProfile({ aestheticTags: updatedTags });
      setAuraProfile(updated);
    } catch (err) { setError("Failed to remove tag"); }
  };

  if (loading) return <div className="profile-container">Loading...</div>;

  return (
    <div className="profile-container">
      {error && <div className="error-message">{error}</div>}
      
      {/* 1. Identity Section */}
      <section className="profile-section">
        <div className="section-header">
          <div className="user-info-main">
            <div className="profile-avatar-container">
              <img src={userProfile?.avatar || "/default-avatar.png"} alt="Avatar" />
            </div>
            <div>
              <h2>{userProfile?.username}</h2>
              <p className="user-bio-text">{userProfile?.bio || "No bio yet..."}</p>
            </div>
          </div>
          <button className="edit-btn" onClick={() => setEditingProfile(!editingProfile)}>
            {editingProfile ? "Cancel" : "Edit Profile"}
          </button>
        </div>

        {editingProfile && (
          <div className="edit-form-overlay">
            <div className="profile-field">
              <label>Bio</label>
              <textarea 
                value={profileForm.bio} 
                onChange={(e) => setProfileForm({...profileForm, bio: e.target.value})}
                className="textarea-input"
              />
            </div>
            <div className="profile-field">
              <label>Avatar URL</label>
              <input 
                type="text" 
                value={profileForm.avatar} 
                onChange={(e) => setProfileForm({...profileForm, avatar: e.target.value})}
                className="text-input"
              />
            </div>
            <button className="save-btn" onClick={handleUpdateProfile}><Save size={16}/> Save Changes</button>
          </div>
        )}
      </section>

      {/* 2. Curator Status (статичный блок, добавленный по запросу) */}
      <section className="curator-section">
        <div className="curator-card">
          <div className="curator-header">
            <div>
              <h3>Curator Status</h3>
              <p>Your journey to legendary taste</p>
            </div>
            <div className="curator-level-badge">7</div>
          </div>

          <div className="xp-progress-container">
            <div className="xp-progress-fill" style={{ width: "65%" }}></div>
          </div>

          <div className="curator-stats-grid">
            <div className="c-stat-item">
              <div className="c-icon-box blue">XP</div>
              <div>
                <p className="stat-title">XP</p>
                <p className="stat-value">3,240</p>
              </div>
            </div>
            <div className="c-stat-item">
              <div className="c-icon-box orange">📤</div>
              <div>
                <p className="stat-title">Total Shares</p>
                <p className="stat-value">128</p>
              </div>
            </div>
            <div className="c-stat-item">
              <div className="c-icon-box green">🔥</div>
              <div>
                <p className="stat-title">Day Streak</p>
                <p className="stat-value">14</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Vibe Profile (Aura & Tags) */}
      <section className="profile-section">
        <div className="section-header">
          <h3>Your Vibe Profile</h3>
        </div>
        
        <div className="vibe-grid">
          <div className="vibe-main">
            <h4>Aura Colors</h4>
            <div className="colors-display">
              {auraProfile?.auraColors?.map((color, i) => (
                <div key={i} className="color-item">
                  <div className="color-swatch" style={{ backgroundColor: color }}></div>
                  <span>{color}</span>
                </div>
              ))}
            </div>

            <h4 style={{marginTop: '1.5rem'}}>Aesthetic Tags</h4>
            <div className="tags-editor">
              <div className="tags-display">
                {auraProfile?.aestheticTags?.map(tag => (
                  <span key={tag} className="tag">
                    {tag} <X size={14} onClick={() => handleRemoveTag(tag)} style={{cursor: 'pointer'}}/>
                  </span>
                ))}
              </div>
              <div className="tag-input-group">
                <input 
                  type="text" 
                  placeholder="Add a vibe..." 
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                />
                <button onClick={handleAddTag} className="add-btn"><Plus size={16}/></button>
              </div>
            </div>
          </div>

          <div className="categories-stats">
            <h4>Category Progress</h4>
            {Object.entries(auraProfile?.categoryStats || {}).map(([cat, val]) => {
              const Icon = CATEGORY_ICONS[cat] || Star;
              return (
                <div key={cat} className="category-stat">
                  <div className="category-name"><Icon size={14}/> {cat}</div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${val}%` }}></div>
                  </div>
                  <span className="percentage">{val}%</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 4. My Shares Gallery */}
      <section className="shares-section">
        <h3>Recent Shares</h3>
        <div className="shares-grid">
          {shares.length > 0 ? shares.map(share => (
            <div key={share.id} className="share-card">
              <div className="share-image-container">
                <img src={share.image} alt={share.title} className="share-image" />
                <div className="dominant-color-indicator" style={{ backgroundColor: share.dominantColor }}></div>
                <div className="share-category-badge">
                   {(() => { const Icon = CATEGORY_ICONS[share.category] || Star; return <Icon size={12}/>; })()}
                   {share.category}
                </div>
              </div>
              <div className="share-info">
                <h4 className="share-title">{share.title}</h4>
                <p className="share-caption">{share.caption}</p>
                <span className="share-date">{new Date(share.timestamp).toLocaleDateString()}</span>
              </div>
            </div>
          )) : <p className="empty-text">No shares yet. Go discover something!</p>}
        </div>
      </section>

      {/* 5. Recent Achievements Block */}
      <section className="achievements-section-modern">
        <h3>Recent Achievements</h3>
        <div className="achievements-container">
          <div className="achievement-badge vanguard">
            <span className="ach-icon">🎯</span>
            <span className="ach-text">Vanguard</span>
          </div>
          <div className="achievement-badge director">
            <span className="ach-icon">🎬</span>
            <span className="ach-text">Director's Cut</span>
          </div>
          <div className="achievement-badge vinyl">
            <span className="ach-icon">💿</span>
            <span className="ach-text">Vinyl Collector</span>
          </div>
          <div className="achievement-badge earlybird">
            <span className="ach-icon">🌅</span>
            <span className="ach-text">Early Bird</span>
          </div>
          <div className="achievement-badge nightowl">
            <span className="ach-icon">🦉</span>
            <span className="ach-text">Night Owl</span>
          </div>
        </div>
      </section>
    </div>
  );
}
