import { useEffect, useMemo, useState } from "react";
import { deleteModeratedRoomPost, getModerationReports, suspendUser } from "./services/api";

export default function ModeratorPage() {
  const [status, setStatus] = useState({ loading: true, error: "" });
  const [reports, setReports] = useState([]);
  const [durations, setDurations] = useState({});
  const [reasons, setReasons] = useState({});
  const [busyReportId, setBusyReportId] = useState("");

  const currentUser = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem("user") || "null");
    } catch {
      return null;
    }
  }, []);

  const loadReports = async () => {
    setStatus({ loading: true, error: "" });
    try {
      const response = await getModerationReports({ limit: 100, offset: 0 });
      setReports(response?.data || []);
      setStatus({ loading: false, error: "" });
    } catch (error) {
      setStatus({
        loading: false,
        error: error.response?.data?.message || "Failed to load reports",
      });
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const onSuspend = async (item) => {
    const ownerId = item?.owner?.userId;
    const reportId = item?.report?.id;
    if (!ownerId || !reportId) return;

    const durationHours = Number(durations[reportId] || 24);
    const reason = reasons[reportId] || "Suspended by moderator";

    setBusyReportId(reportId);
    try {
      await suspendUser(ownerId, { durationHours, reason });
      await loadReports();
    } catch (_error) {
      // best effort UI; list reload already handles detailed errors
    } finally {
      setBusyReportId("");
    }
  };

  const onDeletePost = async (item) => {
    const postId = item?.post?.id;
    const reportId = item?.report?.id;
    if (!postId || !reportId) return;

    setBusyReportId(reportId);
    try {
      await deleteModeratedRoomPost(postId);
      await loadReports();
    } catch (_error) {
      // best effort UI; list reload already handles detailed errors
    } finally {
      setBusyReportId("");
    }
  };

  if (!currentUser || currentUser.role !== "moderator") {
    return (
      <div className="moderator-page">
        <div className="moderator-empty">Moderator access required.</div>
      </div>
    );
  }

  return (
    <div className="moderator-page">
      <div className="moderator-header">
        <h1>Reported Room Posts</h1>
        <button className="auth-button" onClick={loadReports} disabled={status.loading}>
          {status.loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {status.error && <div className="auth-message error">{status.error}</div>}

      {!status.loading && reports.length === 0 && (
        <div className="moderator-empty">No reports found.</div>
      )}

      <div className="moderator-grid">
        {reports.map((item) => {
          const report = item.report || {};
          const post = item.post || {};
          const room = item.room || {};
          const reporter = item.reporter || {};
          const owner = item.owner || {};
          const isBusy = busyReportId === report.id;

          return (
            <article key={report.id} className="moderator-card">
              <div className="moderator-card__top">
                <p><strong>Report:</strong> {report.id}</p>
                <p><strong>Room:</strong> {room.name || "Unknown"}</p>
                <p><strong>Post:</strong> {post.title || "Deleted"}</p>
                <p><strong>Reason:</strong> {report.reason}</p>
                <p><strong>Reporter:</strong> {reporter.username || report.reporterId}</p>
                <p><strong>Owner:</strong> {owner.username || report.ownerId}</p>
                <p><strong>Reported At:</strong> {report.createdAt}</p>
              </div>

              {post.image && <img src={post.image} alt={post.title || "Reported post"} className="moderator-preview" />}

              <div className="moderator-actions">
                <label>
                  Suspension (hours)
                  <input
                    type="number"
                    min="1"
                    max="8760"
                    value={durations[report.id] || 24}
                    onChange={(e) => setDurations((prev) => ({ ...prev, [report.id]: e.target.value }))}
                  />
                </label>
                <label>
                  Suspension reason
                  <input
                    type="text"
                    value={reasons[report.id] || ""}
                    onChange={(e) => setReasons((prev) => ({ ...prev, [report.id]: e.target.value }))}
                    placeholder="Optional reason"
                  />
                </label>
                <div className="moderator-actions__buttons">
                  <button type="button" className="auth-button" onClick={() => onSuspend(item)} disabled={isBusy}>
                    Suspend Owner
                  </button>
                  <button type="button" className="moderator-danger" onClick={() => onDeletePost(item)} disabled={isBusy || !post.id}>
                    Delete Room Post
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
