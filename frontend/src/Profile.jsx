import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Clapperboard, Music, Gamepad2, BookOpen, Plane } from "lucide-react";
import {
  getUserProfile,
  updateUserProfile,
  getAuraProfile,
  updateAuraProfile,
  getCuratorStats,
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
  const [curatorStats, setCuratorStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Edit states
  const [editingProfile, setEditingProfile] = useState(false);
  const [editingAura, setEditingAura] = useState(false);
  const [profileForm, setProfileForm] = useState({
    bio: "",
    avatar: "",
  });
  const [auraForm, setAuraForm] = useState({
    aestheticTags: [],
    auraColors: [],
  });
  const [newTag, setNewTag] = useState("");
  const [newColor, setNewColor] = useState("#FF6B9D");

  // Load data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      let errorMessage = null;

      try {
        const [userRes, auraRes, curatorRes] = await Promise.allSettled([
          getUserProfile(),
          getAuraProfile(),
          getCuratorStats(),
        ]);

        if (userRes.status === "fulfilled") {
          setUserProfile(userRes.value);
          setProfileForm({
            bio: userRes.value.bio || "",
            avatar: userRes.value.avatar || "",
          });
        } else {
          const err = userRes.reason;
          errorMessage = err.response?.data?.message || "Failed to load profile";
          if (err.response?.status === 401) navigate("/");
        }

        if (auraRes.status === "fulfilled") {
          setAuraProfile(auraRes.value);
          setAuraForm({
            aestheticTags: auraRes.value.aestheticTags || [],
            auraColors: auraRes.value.auraColors || [],
          });
        } else {
          const err = auraRes.reason;
          errorMessage =
            errorMessage ||
            err.response?.data?.message ||
            "Failed to load aura profile";
          if (err.response?.status === 401) navigate("/");
        }

        if (curatorRes.status === "fulfilled") {
          setCuratorStats(curatorRes.value);
        } else {
          const err = curatorRes.reason;
          errorMessage =
            errorMessage ||
            err.response?.data?.message ||
            "Failed to load curator stats";
          if (err.response?.status === 401) navigate("/");
        }

        setError(errorMessage);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load profile");
        if (err.response?.status === 401) navigate("/");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [navigate]);

  const handleProfileSave = async () => {
    try {
      const updated = await updateUserProfile(profileForm);
      setUserProfile(updated);
      setEditingProfile(false);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to update profile");
    }
  };

  const handleAuraSave = async () => {
    try {
      const updated = await updateAuraProfile(auraForm);
      setAuraProfile(updated);
      setEditingAura(false);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to update aura");
    }
  };

  const addTag = () => {
    if (newTag.trim() && !auraForm.aestheticTags.includes(newTag)) {
      setAuraForm({
        ...auraForm,
        aestheticTags: [...auraForm.aestheticTags, newTag.trim()],
      });
      setNewTag("");
    }
  };

  const removeTag = (tag) => {
    setAuraForm({
      ...auraForm,
      aestheticTags: auraForm.aestheticTags.filter((t) => t !== tag),
    });
  };

  const addColor = () => {
    if (!auraForm.auraColors.includes(newColor)) {
      setAuraForm({
        ...auraForm,
        auraColors: [...auraForm.auraColors, newColor],
      });
    }
  };

  const removeColor = (color) => {
    setAuraForm({
      ...auraForm,
      auraColors: auraForm.auraColors.filter((c) => c !== color),
    });
  };

  if (loading) return <div className="profile-container">Loading...</div>;

  return (
    <div className="profile-container">
      {error && <div className="error-message">{error}</div>}

      {/* User Profile Section */}
      <section className="profile-section">
        <div className="section-header">
          <h2>Profile</h2>
          <button
            className="edit-btn"
            onClick={() => setEditingProfile(!editingProfile)}
          >
            {editingProfile ? "Cancel" : "Edit"}
          </button>
        </div>

        {userProfile && (
          <div className="profile-content">
            <div className="profile-field">
              <label>Username</label>
              <p className="field-value">{userProfile.username}</p>
            </div>

            <div className="profile-field">
              <label>Email</label>
              <p className="field-value">{userProfile.email}</p>
            </div>

            <div className="profile-field">
              <label>Bio</label>
              {editingProfile ? (
                <textarea
                  value={profileForm.bio}
                  onChange={(e) =>
                    setProfileForm({ ...profileForm, bio: e.target.value })
                  }
                  className="textarea-input"
                  placeholder="Tell us about yourself..."
                  maxLength="500"
                />
              ) : (
                <p className="field-value">{profileForm.bio || "No bio yet"}</p>
              )}
            </div>

            <div className="profile-field">
              <label>Avatar URL</label>
              {editingProfile ? (
                <input
                  type="url"
                  value={profileForm.avatar}
                  onChange={(e) =>
                    setProfileForm({ ...profileForm, avatar: e.target.value })
                  }
                  className="text-input"
                  placeholder="https://example.com/avatar.jpg"
                />
              ) : profileForm.avatar ? (
                <div className="avatar-preview">
                  <img src={profileForm.avatar} alt="Avatar" />
                </div>
              ) : (
                <p className="field-value">No avatar</p>
              )}
            </div>

            {editingProfile && (
              <button className="save-btn" onClick={handleProfileSave}>
                Save Changes
              </button>
            )}
          </div>
        )}
      </section>

      {/* Aura Profile Section */}
      <section className="profile-section">
        <div className="section-header">
          <h2>Aura Profile</h2>
          <button
            className="edit-btn"
            onClick={() => setEditingAura(!editingAura)}
          >
            {editingAura ? "Cancel" : "Edit"}
          </button>
        </div>

        {auraProfile && (
          <div className="profile-content">
            {/* Aesthetic Tags */}
            <div className="profile-field">
              <label>Aesthetic Tags</label>
              {editingAura ? (
                <div className="tags-editor">
                  <div className="tag-input-group">
                    <input
                      type="text"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && addTag()}
                      className="text-input"
                      placeholder="e.g., minimalist, vintage, dark academia"
                    />
                    <button className="add-btn" onClick={addTag}>
                      Add
                    </button>
                  </div>
                  <div className="tags-display">
                    {auraForm.aestheticTags.map((tag) => (
                      <div key={tag} className="tag">
                        {tag}
                        <button
                          className="remove-tag-btn"
                          onClick={() => removeTag(tag)}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="tags-display">
                  {auraForm.aestheticTags.length > 0 ? (
                    auraForm.aestheticTags.map((tag) => (
                      <div key={tag} className="tag">
                        {tag}
                      </div>
                    ))
                  ) : (
                    <p className="field-value">No tags yet</p>
                  )}
                </div>
              )}
            </div>

            {/* Aura Colors */}
            <div className="profile-field">
              <label>Aura Colors</label>
              {editingAura ? (
                <div className="colors-editor">
                  <div className="color-input-group">
                    <input
                      type="color"
                      value={newColor}
                      onChange={(e) => setNewColor(e.target.value)}
                      className="color-input"
                    />
                    <button className="add-btn" onClick={addColor}>
                      Add Color
                    </button>
                  </div>
                  <div className="colors-display">
                    {auraForm.auraColors.map((color) => (
                      <div key={color} className="color-item">
                        <div
                          className="color-swatch"
                          style={{ backgroundColor: color }}
                        />
                        <span>{color}</span>
                        <button
                          className="remove-color-btn"
                          onClick={() => removeColor(color)}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="colors-display">
                  {auraForm.auraColors.length > 0 ? (
                    auraForm.auraColors.map((color) => (
                      <div key={color} className="color-item">
                        <div
                          className="color-swatch"
                          style={{ backgroundColor: color }}
                        />
                        <span>{color}</span>
                      </div>
                    ))
                  ) : (
                    <p className="field-value">No colors yet</p>
                  )}
                </div>
              )}
            </div>

            {/* Top Categories */}
            {auraProfile.topCategories && auraProfile.topCategories.length > 0 && (
              <div className="profile-field">
                <label>Content Distribution</label>
                <div className="categories-stats">
                  {auraProfile.topCategories.map((cat) => (
                    <div key={cat.category} className="category-stat">
                      <span className="category-name">{cat.category}</span>
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{ width: `${cat.percentage}%` }}
                        />
                      </div>
                      <span className="percentage">{cat.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {editingAura && (
              <button className="save-btn" onClick={handleAuraSave}>
                Save Changes
              </button>
            )}
          </div>
        )}
      </section>

      {/* Curator Progress Section */}
      <section className="profile-section">
        <h2>Curator Progress</h2>
        {curatorStats ? (
          <div className="curator-progress">
            <div className="curator-stats-grid">
              <div className="curator-stat-card">
                <span className="curator-label">Current Level</span>
                <span className="curator-value">{curatorStats.currentLevel}</span>
              </div>
              <div className="curator-stat-card">
                <span className="curator-label">Total XP</span>
                <span className="curator-value">{curatorStats.totalXP}</span>
              </div>
              <div className="curator-stat-card">
                <span className="curator-label">Total Shares</span>
                <span className="curator-value">{curatorStats.totalShares}</span>
              </div>
              <div className="curator-stat-card">
                <span className="curator-label">Streak Days</span>
                <span className="curator-value">
                  {curatorStats.streakDays ?? 0}
                </span>
              </div>
            </div>

            <div className="curator-metrics">
              {typeof curatorStats.finishedBooks === "number" && (
                <div className="metric-row">
                  <span className="metric-label">Finished Books</span>
                  <span className="metric-value">{curatorStats.finishedBooks}</span>
                </div>
              )}
              {typeof curatorStats.earlyDiscoveries === "number" && (
                <div className="metric-row">
                  <span className="metric-label">Early Discoveries</span>
                  <span className="metric-value">{curatorStats.earlyDiscoveries}</span>
                </div>
              )}
              {curatorStats.completedFilmographies &&
                curatorStats.completedFilmographies.length > 0 && (
                  <div className="metric-row">
                    <span className="metric-label">Completed Filmographies</span>
                    <span className="metric-value">
                      {curatorStats.completedFilmographies.join(", ")}
                    </span>
                  </div>
                )}
            </div>

            <div className="curator-badges">
              <h3>Badges</h3>
              {curatorStats.badges && curatorStats.badges.length > 0 ? (
                <div className="badge-list">
                  {curatorStats.badges.map((badge) => {
                    const maxProgress = badge.maxProgress || 0;
                    const progressValue = badge.progress || 0;
                    const progressPercent =
                      maxProgress > 0
                        ? Math.min(
                            100,
                            Math.round((progressValue / maxProgress) * 100)
                          )
                        : null;

                    return (
                      <div
                        key={badge.id}
                        className={`badge-item ${badge.unlocked ? "unlocked" : ""}`}
                      >
                        <div className="badge-header">
                          <div>
                            <div className="badge-name">{badge.name}</div>
                            {badge.description && (
                              <div className="badge-description">
                                {badge.description}
                              </div>
                            )}
                          </div>
                          <div className="badge-meta">
                            <span className="badge-rarity">{badge.rarity}</span>
                            {badge.category && (
                              <span className="badge-category">
                                {badge.category}
                              </span>
                            )}
                          </div>
                        </div>

                        {progressPercent !== null && (
                          <div className="badge-progress">
                            <div className="badge-progress-bar">
                              <div
                                className="badge-progress-fill"
                                style={{ width: `${progressPercent}%` }}
                              />
                            </div>
                            <span className="badge-progress-text">
                              {progressValue}/{maxProgress}
                            </span>
                          </div>
                        )}

                        {badge.unlocked && badge.unlockedDate && (
                          <div className="badge-unlocked">
                            Unlocked on{" "}
                            {new Date(badge.unlockedDate).toLocaleDateString(
                              undefined,
                              {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                              }
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="empty-state">
                  No badges yet. Keep sharing to unlock more.
                </p>
              )}
            </div>
          </div>
        ) : (
          <p className="empty-state">
            Curator stats are not available yet.
          </p>
        )}
      </section>

      {/* Recent Shares Section */}
      <section className="profile-section">
        <h2>Recent Shares</h2>
        {auraProfile && auraProfile.recentShares && auraProfile.recentShares.length > 0 ? (
          <div className="shares-grid">
            {auraProfile.recentShares.map((share) => {
              const Icon = CATEGORY_ICONS[share.category];
              return (
                <div key={share.id} className="share-card">
                  {share.image && (
                    <div className="share-image-container">
                      <img src={share.image} alt={share.title} className="share-image" />
                      {share.dominantColor && (
                        <div
                          className="dominant-color-indicator"
                          style={{ backgroundColor: share.dominantColor }}
                          title={share.dominantColor}
                        />
                      )}
                      <div className="share-category-badge">
                        {Icon && <Icon size={16} />}
                        <span>{share.category}</span>
                      </div>
                    </div>
                  )}
                  <div className="share-info">
                    <h4 className="share-title">{share.title}</h4>
                    {share.caption && <p className="share-caption">{share.caption}</p>}
                    <p className="share-date">
                      {new Date(share.timestamp).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="empty-state">No shares yet. Start sharing your favorites!</p>
        )}
      </section>
    </div>
  );
}
