import { useEffect, useState } from "react";
import { getCuratorProgress } from "../services/userService";

export default function CuratorProgress() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");

    getCuratorProgress(token)
      .then(res => setData(res))
      .catch(err => console.error(err));
  }, []);

  if (!data) return <div>Loading...</div>;

  const progressPercent =
    (data.currentXP / data.nextLevelXP) * 100;

  return (
    <div className="curator-card">
      <h2>Curator Status</h2>
      <p>Level {data.level} — {data.roleName}</p>

      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <p>{data.currentXP} / {data.nextLevelXP} XP</p>

      <div className="stats">
        <div>Total Shares: {data.stats.totalShares}</div>
        <div>Day Streak: {data.stats.dayStreak}</div>
        <div>Badges: {data.stats.badges}</div>
        <div>Early Finds: {data.stats.earlyFinds}</div>
      </div>
    </div>
  );
}
