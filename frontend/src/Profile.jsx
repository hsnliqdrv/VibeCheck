import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Clapperboard, Music, Gamepad2, BookOpen, Plane, Star, Flame, Trophy, TrendingUp } from "lucide-react";
import {
  getUserProfile,
  updateUserProfile,
  getAuraProfile,
  updateAuraProfile,
  getCuratorProgress
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [editingProfile, setEditingProfile] = useState(false);
  const [editingAura, setEditingAura] = useState(false);
  const [profileForm, setProfileForm] = useState({ bio: "", avatar: "" });
  const [auraForm, setAuraForm] = useState({ aestheticTags: [], auraColors: [] });
  const [newTag, setNewTag] = useState("");
  const [newColor, setNewColor] = useState("#FF6B9D");

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [userRes, auraRes, curatorRes] = await Promise.all([
          getUserProfile(),
          getAuraProfile(),
          getCuratorProgress(),
        ]);
        
        setUserProfile(userRes);
        setAuraProfile(auraRes);
        setCuratorData(curatorRes);

        setProfileForm({ bio: userRes.bio || "", avatar: userRes.avatar || "" });
        setAuraForm({
          aestheticTags: auraRes.aestheticTags || [],
          auraColors: auraRes.auraColors || [],
        });
        setError(null);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load profile");
        if (err.response?.status === 401) navigate("/");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [navigate]);

  if (loading) return <div className="profile-container">Loading...</div>;

  return (
    <div className="profile-container">
      {error && <div className="error-message">{error}</div>}
      <section className="profile-section">
        <div className="section-header">
          <h2>Profile</h2>
          <button className="edit-btn" onClick={() => setEditingProfile(!editingProfile)}>
            {editingProfile ? "Cancel" : "Edit"}
          </button>
        </div>
      </section>
      {curatorData && (
        <section className="curator-section">
          <div className="curator-card">
            <div className="curator-header">
              <div className="curator-title-group">
                <h3>Curator Status</h3>
                <p className="curator-subtitle">Your journey to legendary taste</p>
              </div>
              <div className="curator-level-badge">{curatorData.level}</div>
            </div>

            <div className="curator-status-row">
              <span className="curator-role">{curatorData.roleName}</span>
              <span className="curator-xp">{curatorData.currentXP} XP</span>
            </div>

            <div className="xp-progress-container">
              <div 
                className="xp-progress-fill" 
                style={{ width: `${(curatorData.currentXP / curatorData.nextLevelXP) * 100}%` }}
              ></div>
              <span className="xp-needed-text">
                {curatorData.nextLevelXP - curatorData.currentXP} XP needed to Level {curatorData.level + 1}
              </span>
            </div>

            <div className="curator-stats-grid">
              <div className="c-stat-item">
                <div className="c-icon-box blue"><Star size={18} /></div>
                <div className="c-stat-info">
                  <span className="c-val">{curatorData.stats.totalShares}</span>
                  <span className="c-lab">Total Shares</span>
                </div>
              </div>
              <div className="c-stat-item">
                <div className="c-icon-box orange"><Flame size={18} /></div>
                <div className="c-stat-info">
                  <span className="c-val">{curatorData.stats.dayStreak}</span>
                  <span className="c-lab">Day Streak</span>
                </div>
              </div>
              <div className="c-stat-item">
                <div className="c-icon-box purple"><Trophy size={18} /></div>
                <div className="c-stat-info">
                  <span className="c-val">{curatorData.stats.badges}</span>
                  <span className="c-lab">Badges</span>
                </div>
              </div>
              <div className="c-stat-item">
                <div className="c-icon-box green"><TrendingUp size={18} /></div>
                <div className="c-stat-info">
                  <span className="c-val">{curatorData.stats.earlyFinds}</span>
                  <span className="c-lab">Early Finds</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
      <section className="profile-section">
      </section>
      <section className="profile-section">
      </section>
    </div>
  );
}
