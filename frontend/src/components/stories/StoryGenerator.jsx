import { useState, useCallback } from "react";
import { Clapperboard, Music, Gamepad2, BookOpen, Plane, Download, ExternalLink, Crosshair } from "lucide-react";
import StoryCard from "./StoryCard";
import ContentSelector from "./ContentSelector";
import StoryCustomizer from "./StoryCustomizer";
import { createShare } from "../../services/api";
import "./StoryGenerator.css";

const CATEGORIES = [
  { key: "cinema", label: "Films", icon: Clapperboard },
  { key: "music", label: "Songs", icon: Music },
  { key: "games", label: "Games", icon: Gamepad2 },
  { key: "books", label: "Books", icon: BookOpen },
  { key: "travel", label: "Places", icon: Plane },
];

const DEFAULT_STYLE = {
  font: "default",
  bgColor: null,
  bgTexture: "none",
  textAlign: "left",
  titleSize: "normal",
  cardLayout: "default",
};

export default function StoryGenerator() {
  const [category, setCategory] = useState("cinema");
  const [selectedContent, setSelectedContent] = useState(null);
  const [caption, setCaption] = useState("");
  const [sharing, setSharing] = useState(false);
  const [shareResult, setShareResult] = useState(null);
  const [style, setStyle] = useState(DEFAULT_STYLE);

  const handleCategoryChange = (key) => {
    setCategory(key);
    setSelectedContent(null);
    setCaption("");
    setShareResult(null);
  };

  const updateStyle = (key, value) => {
    setStyle((prev) => ({ ...prev, [key]: value }));
  };

  const handleShare = useCallback(async () => {
    if (!selectedContent) return;
    setSharing(true);
    setShareResult(null);
    try {
      const share = await createShare({
        category,
        contentId: selectedContent.id,
        caption: caption.trim() || undefined,
      });
      setShareResult({ type: "success", data: share });
    } catch (err) {
      setShareResult({
        type: "error",
        message: err.response?.data?.message || "Failed to share",
      });
    } finally {
      setSharing(false);
    }
  }, [category, selectedContent, caption]);

  return (
    <div className="story-generator">
      <div className="story-generator__panel">
        <div className="story-generator__categories">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            return (
              <button
                key={cat.key}
                type="button"
                className={`story-generator__cat-btn ${
                  category === cat.key ? "story-generator__cat-btn--active" : ""
                }`}
                onClick={() => handleCategoryChange(cat.key)}
              >
                <Icon size={16} />
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>

        <ContentSelector
          category={category}
          selected={selectedContent}
          onSelect={setSelectedContent}
        />

        {selectedContent && (
          <div className="story-generator__caption-wrap">
            <label className="story-generator__caption-label">
              Add a caption (optional)
            </label>
            <textarea
              className="story-generator__caption"
              placeholder="What's the vibe?"
              maxLength={500}
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              rows={2}
            />
            <span className="story-generator__char-count">
              {caption.length}/500
            </span>
          </div>
        )}

        {selectedContent && (
          <StoryCustomizer style={style} onChange={updateStyle} />
        )}
      </div>

      <div className="story-generator__preview">
        {selectedContent ? (
          <>
            <StoryCard
              category={category}
              content={selectedContent}
              dominantColor={selectedContent.dominantColor}
              caption={caption || undefined}
              customStyle={style}
            />

            <div className="story-generator__actions">
              <button
                type="button"
                className="story-generator__btn story-generator__btn--primary"
                onClick={handleShare}
                disabled={sharing}
              >
                <Download size={18} />
                {sharing ? "Sharing…" : "Export to Instagram Story"}
              </button>
              <button
                type="button"
                className="story-generator__btn story-generator__btn--secondary"
              >
                <ExternalLink size={18} />
                Get the Vibe
              </button>
            </div>

            {shareResult && (
              <div
                className={`story-generator__result story-generator__result--${shareResult.type}`}
              >
                {shareResult.type === "success"
                  ? "Story shared successfully!"
                  : shareResult.message}
              </div>
            )}
          </>
        ) : (
          <div className="story-generator__empty">
            <Crosshair size={48} strokeWidth={1.2} />
            <p>Select content to preview your story</p>
          </div>
        )}
      </div>
    </div>
  );
}
