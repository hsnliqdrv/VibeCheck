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
  const [profileForm, setProfileForm] = useState({ bio: "", avatar: "" });

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // Используем Promise.allSettled вместо Promise.all
        // Это позволит профилю загрузиться, даже если один из запросов (например, мок) упадет
        const results = await Promise.allSettled([
          getUserProfile(),
          getAuraProfile(),
          getCuratorProgress(),
        ]);
        
        if (results[0].status === 'fulfilled') {
          setUserProfile(results[0].value);
          setProfileForm({ bio: results[0].value.bio || "", avatar: results[0].value.avatar || "" });
        }
        
        if (results[1].status === 'fulfilled') setAuraProfile(results[1].value);
        if (results[2].status === 'fulfilled') setCuratorData(results[2].value);

        setError(null);
      } catch (err) {
        console.error("Load error:", err);
        setError("Failed to load some profile data");
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
          <h2>Profile: {userProfile?.username}</h2>
          <button className="edit-btn" onClick={() => setEditingProfile(!editingProfile)}>
            {editingProfile ? "Cancel" : "Edit"}
          </button>
        </div>
      </section>

      {/* Безопасная отрисовка куратора */}
      {curatorData && (
        <section className="curator-section">
          <div className="curator-card">
            <div className="curator-header">
              <div className="curator-title-group">
                <h3>Curator Status</h3>
                <p className="curator-subtitle">Your journey to legendary taste</p>
              </div>
              {/* Используем ?. везде */}
              <div className="curator-level-badge">{curatorData?.level || 0}</div>
            </div>

            <div className="curator-status-row">
              <span className="curator-role">{curatorData?.roleName || "Explorer"}</span>
              <span className="curator-xp">{curatorData?.currentXP || 0} XP</span>
            </div>

            <div className="xp-progress-container">
              <div 
                className="xp-progress-fill" 
                style={{ 
                  width: `${(curatorData?.currentXP / (curatorData?.nextLevelXP || 100)) * 100}%` 
                }}
              ></div>
              <span className="xp-needed-text">
                {(curatorData?.nextLevelXP || 0) - (curatorData?.currentXP || 0)} XP needed to Level {(curatorData?.level || 0) + 1}
              </span>
            </div>

            <div className="curator-stats-grid">
              <div className="c-stat-item">
                <div className="c-icon-box blue"><Star size={18} /></div>
                <div className="c-stat-info">
                  {/* САМОЕ ВАЖНОЕ МЕСТО: curatorData?.stats?.totalShares */}
                  <span className="c-val">{curatorData?.stats?.totalShares ?? 0}</span>
                  <span className="c-lab">Total Shares</span>
                </div>
              </div>
              <div className="c-stat-item">
                <div className="c-icon-box orange"><Flame size={18} /></div>
                <div className="c-stat-info">
                  <span className="c-val">{curatorData?.stats?.dayStreak ?? 0}</span>
                  <span className="c-lab">Day Streak</span>
                </div>
              </div>
              <div className="c-stat-item">
                <div className="c-icon-box purple"><Trophy size={18} /></div>
                <div className="c-stat-info">
                  <span className="c-val">{curatorData?.stats?.badges ?? 0}</span>
                  <span className="c-lab">Badges</span>
                </div>
              </div>
              <div className="c-stat-item">
                <div className="c-icon-box green"><TrendingUp size={18} /></div>
                <div className="c-stat-info">
                  <span className="c-val">{curatorData?.stats?.earlyFinds ?? 0}</span>
                  <span className="c-lab">Early Finds</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
