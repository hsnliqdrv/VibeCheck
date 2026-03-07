import { useEffect, useState } from "react";
import { Clapperboard, Music, Gamepad2, BookOpen, Plane } from "lucide-react";
import {
  getUserProfile,
  updateUserProfile,
  getAuraProfile,
  updateAuraProfile,
  getCuratorStats,
  getAvatarUploadUrl,
  uploadToPresignedUrl,
} from "./services/api";
import { getAvatarUrl } from "./utils/avatarUrl";
import "./Profile.css";

const CATEGORY_ICONS = {
  cinema: Clapperboard,
  music: Music,
  games: Gamepad2,
  books: BookOpen,
  travel: Plane,
};

const PLATFORM_ICONS = {
  instagram: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5M12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10m0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>,
  twitter: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.835L1.254 2.25H8.08l4.253 5.622L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>,
  tiktok: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M16.6 5.82s.51.5 0 0A4.278 4.278 0 0 1 15.54 3h-3.09v12.4a2.592 2.592 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64 0 3.33 2.76 5.7 5.69 5.7 3.14 0 5.69-2.55 5.69-5.7V9.01a7.35 7.35 0 0 0 4.3 1.38V7.3s-1.88.09-3.24-1.48z"/></svg>,
  youtube: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/></svg>,
  facebook: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2.04c-5.5 0-10 4.49-10 10.02 0 5 3.66 9.15 8.44 9.9v-7H7.9v-2.9h2.54V9.85c0-2.51 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.78-1.63 1.57v1.88h2.78l-.45 2.9h-2.33v7a10 10 0 0 0 8.44-9.9c0-5.53-4.5-10.02-10.01-10.02z"/></svg>,
  linkedin: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/></svg>,
  pinterest: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M9.04 21.54c.96.29 1.93.46 2.96.46a10 10 0 0 0 10-10A10 10 0 0 0 12 2 10 10 0 0 0 2 12c0 4.25 2.67 7.9 6.44 9.34-.09-.78-.18-2.07 0-2.96l1.15-4.94s-.29-.58-.29-1.5c0-1.38.86-2.41 1.84-2.41.86 0 1.26.63 1.26 1.44 0 .86-.57 2.09-.86 3.27-.17.98.52 1.84 1.52 1.84 1.78 0 3.16-1.9 3.16-4.58 0-2.4-1.72-4.04-4.19-4.04-2.82 0-4.48 2.1-4.48 4.31 0 .86.28 1.73.71 2.22.06.09.09.17.06.29l-.29 1.09c0 .17-.11.23-.28.11-1.28-.56-2.02-2.38-2.02-3.85 0-3.16 2.24-6.03 6.56-6.03 3.44 0 6.12 2.47 6.12 5.75 0 3.44-2.13 6.2-5.18 6.2-.97 0-1.92-.52-2.26-1.13l-.67 2.37c-.23.86-.86 2.01-1.29 2.7z"/></svg>,
  spotify: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10 10 10 0 0 0 10-10A10 10 0 0 0 12 2m4.38 14.42c-.18.3-.5.38-.78.22-2.15-1.3-4.85-1.6-8.03-.87a.56.56 0 0 1-.66-.42.56.56 0 0 1 .42-.66c3.48-.8 6.47-.45 8.83 1 .3.15.38.54.22.73m1.18-2.68c-.24.36-.66.48-1 .24-2.46-1.52-6.2-1.96-9.11-1.07-.36.1-.76-.08-.87-.44-.1-.36.1-.76.45-.87 3.32-1.02 7.45-.52 10.27 1.22.35.2.46.65.24 1m.1-2.78c-2.95-1.76-7.8-1.92-10.62-1.06-.44.14-.92-.1-1.06-.55-.14-.45.1-.92.55-1.07 3.24-.98 8.62-.79 12.02 1.24.4.24.55.76.3 1.16-.24.4-.75.54-1.15.3z"/></svg>,
  twitch: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M11.64 5.93h1.43v4.28h-1.43m3.93-4.28H17v4.28h-1.43M7 2 3.43 5.57v12.86h4.28V22l3.58-3.57h2.85L20.57 12V2m-1.43 9.29-2.85 2.85h-2.86l-2.5 2.5v-2.5H7.71V3.43h11.43z"/></svg>,
  other: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10.59 13.41c.41.39.41 1.03 0 1.42-.39.39-1.03.39-1.42 0a5.003 5.003 0 0 1 0-7.07l3.54-3.54a5.003 5.003 0 0 1 7.07 0 5.003 5.003 0 0 1 0 7.07l-1.49 1.49c.01-.36-.04-.72-.11-1.05l.79-.8a3.003 3.003 0 0 0 0-4.24 3.003 3.003 0 0 0-4.24 0l-3.53 3.53a3.003 3.003 0 0 0 0 4.24m2.82-4.24c.39-.39 1.03-.39 1.42 0a5.003 5.003 0 0 1 0 7.07l-3.54 3.54a5.003 5.003 0 0 1-7.07 0 5.003 5.003 0 0 1 0-7.07l1.49-1.49c-.01.36.04.72.11 1.05l-.79.8a3.003 3.003 0 0 0 0 4.24 3.003 3.003 0 0 0 4.24 0l3.53-3.53a3.003 3.003 0 0 0 0-4.24.974.974 0 0 1 0-1.42z"/></svg>,
};

const PLATFORM_LABELS = {
  instagram: 'Instagram', twitter: 'X', tiktok: 'TikTok', youtube: 'YouTube',
  facebook: 'Facebook', linkedin: 'LinkedIn', pinterest: 'Pinterest',
  spotify: 'Spotify', twitch: 'Twitch', other: 'Website',
};

export default function Profile() {
  const AVATAR_ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"];

  const [userProfile, setUserProfile] = useState(null);
  const [auraProfile, setAuraProfile] = useState(null);
  const [curatorStats, setCuratorStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarCacheBuster, setAvatarCacheBuster] = useState(null);

  const [editingProfile, setEditingProfile] = useState(false);
  const [editingAura, setEditingAura] = useState(false);
  const [profileForm, setProfileForm] = useState({
    bio: "",
    avatar: "",
    socialMediaLinks: [],
  });
  const [auraForm, setAuraForm] = useState({
    aestheticTags: [],
    auraColors: [],
  });
  const [newTag, setNewTag] = useState("");
  const [newColor, setNewColor] = useState("#FF6B9D");

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
          setAvatarCacheBuster(userRes.value.updatedAt || null);
          setProfileForm({
            bio: userRes.value.bio || "",
            avatar: userRes.value.avatar || "",
            socialMediaLinks: userRes.value.socialMediaLinks || [],
          });
        } else {
          const err = userRes.reason;
          errorMessage = err.response?.data?.message || "Failed to load profile";
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
        }

        if (curatorRes.status === "fulfilled") {
          setCuratorStats(curatorRes.value);
        } else {
          const err = curatorRes.reason;
          errorMessage =
            errorMessage ||
            err.response?.data?.message ||
            "Failed to load curator stats";
        }

        setError(errorMessage);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load profile");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleProfileSave = async () => {
    try {
      const updated = await updateUserProfile(profileForm);
      setUserProfile(updated);
      // Avatar URL can stay the same while image content changes, so force a new cache token after save.
      setAvatarCacheBuster(Date.now());
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

  const PLATFORM_OPTIONS = [
    "instagram", "twitter", "tiktok", "youtube", "facebook",
    "linkedin", "pinterest", "spotify", "twitch", "other",
  ];

  const detectPlatform = (url) => {
    if (!url) return "other";
    const lower = url.toLowerCase();
    for (const p of PLATFORM_OPTIONS) {
      if (p !== "other" && lower.includes(p)) return p;
    }
    if (lower.includes("x.com")) return "twitter";
    return "other";
  };

  const addSocialLink = () => {
    setProfileForm({
      ...profileForm,
      socialMediaLinks: [
        ...profileForm.socialMediaLinks,
        { platform: "instagram", url: "" },
      ],
    });
  };

  const updateSocialLink = (index, field, value) => {
    const updated = [...profileForm.socialMediaLinks];
    updated[index] = { ...updated[index], [field]: value };
    if (field === "url") {
      updated[index].platform = detectPlatform(value);
    }
    setProfileForm({ ...profileForm, socialMediaLinks: updated });
  };

  const removeSocialLink = (index) => {
    setProfileForm({
      ...profileForm,
      socialMediaLinks: profileForm.socialMediaLinks.filter((_, i) => i !== index),
    });
  };

  const getFileExtension = (file) => {
    const fileName = file?.name || "";
    const extension = fileName.split(".").pop();
    return extension ? extension.toLowerCase() : "";
  };

  const handleAvatarFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const extension = getFileExtension(file);
    if (!AVATAR_ALLOWED_EXTENSIONS.includes(extension)) {
      setError("Invalid avatar format. Use jpg, jpeg, png, or webp.");
      event.target.value = "";
      return;
    }

    try {
      setAvatarUploading(true);
      setError(null);

      const uploadInfo = await getAvatarUploadUrl(extension);

      if (uploadInfo.max_size_bytes && file.size > uploadInfo.max_size_bytes) {
        throw new Error(
          `Avatar is too large. Maximum size is ${Math.floor(uploadInfo.max_size_bytes / (1024 * 1024))} MB.`
        );
      }

      await uploadToPresignedUrl(uploadInfo.presigned_url, file, file.type || "image/jpeg");

      setProfileForm((prev) => ({
        ...prev,
        avatar: uploadInfo.cdn_url,
      }));
      setAvatarCacheBuster(Date.now());
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.message || err.message || "Failed to upload avatar");
    } finally {
      setAvatarUploading(false);
      event.target.value = "";
    }
  };

  if (loading) return <div className="profile-container">Loading...</div>;

  return (
    <div className="profile-container">
      {error && <div className="error-message">{error}</div>}

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
              <label>Avatar</label>
              {editingProfile ? (
                <>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
                    onChange={handleAvatarFileChange}
                    className="text-input"
                    disabled={avatarUploading}
                  />
                  {avatarUploading && <p className="field-value">Uploading avatar...</p>}
                  {profileForm.avatar && (
                    <p className="field-value" style={{ wordBreak: "break-all" }}>
                      {profileForm.avatar}
                    </p>
                  )}
                </>
              ) : profileForm.avatar ? (
                <div className="avatar-preview">
                  <img
                    src={getAvatarUrl(profileForm.avatar, avatarCacheBuster || userProfile?.updatedAt)}
                    alt="Avatar"
                  />
                </div>
              ) : (
                <p className="field-value">No avatar</p>
              )}
            </div>

            <div className="profile-field">
              <label>Social Media Links</label>
              {editingProfile ? (
                <div className="social-links-editor">
                  {profileForm.socialMediaLinks.map((link, index) => (
                    <div key={index} className="social-link-row">
                      <select
                        value={link.platform}
                        onChange={(e) => updateSocialLink(index, "platform", e.target.value)}
                        className="text-input social-platform-select"
                      >
                        {PLATFORM_OPTIONS.map((p) => (
                          <option key={p} value={p}>
                            {PLATFORM_LABELS[p] || p.charAt(0).toUpperCase() + p.slice(1)}
                          </option>
                        ))}
                      </select>
                      <input
                        type="url"
                        value={link.url}
                        onChange={(e) => updateSocialLink(index, "url", e.target.value)}
                        className="text-input"
                        placeholder="https://instagram.com/yourprofile"
                      />
                      <button
                        type="button"
                        className="remove-social-btn"
                        onClick={() => removeSocialLink(index)}
                        title="Remove link"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  <button type="button" className="add-btn" onClick={addSocialLink}>
                    + Add Link
                  </button>
                </div>
              ) : profileForm.socialMediaLinks.length > 0 ? (
                <div className="social-links-display">
                  {profileForm.socialMediaLinks.map((link, i) => {
                    const platform = (link.platform || 'other').toLowerCase();
                    return (
                      <a
                        key={i}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`social-link-badge social-link-badge--${platform}`}
                        title={PLATFORM_LABELS[platform] || link.platform}
                      >
                        {PLATFORM_ICONS[platform] || PLATFORM_ICONS.other}
                      </a>
                    );
                  })}
                </div>
              ) : (
                <p className="field-value">No social links yet</p>
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
