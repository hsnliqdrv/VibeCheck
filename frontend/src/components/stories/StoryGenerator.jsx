import { useState } from "react";
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
  const handleSelectContent = (item) => {
    console.log("Выбран объект для сторис:", item);
    setSelectedContent(item);
  };

  const handleShare = async () => {
    if (!selectedContent) return;
    setSharing(true);
    try {
      await createShare({
        category,
        content: selectedContent,
        style,
        caption,
      });
      setShareResult({ type: "success" });
    } catch (err) {
      setShareResult({ type: "error", message: "Failed to share story" });
    } finally {
      setSharing(false);
    }
  };

  return (
    <div className="story-generator">
      <div className="story-generator__panel">
        <div className="story-generator__categories">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              className={`story-generator__cat-btn ${category === cat.key ? "active" : ""}`}
              onClick={() => handleCategoryChange(cat.key)}
            >
              <cat.icon size={18} />
              <span>{cat.label}</span>
            </button>
          ))}
        </div>

        <ContentSelector 
          category={category} 
          onSelect={handleSelectContent} 
        />

        <div className="story-generator__caption">
          <label>Add a caption</label>
          <textarea
            placeholder="What's the vibe?"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
          />
        </div>

        <StoryCustomizer
          style={style}
          onChange={(key, val) => setStyle((prev) => ({ ...prev, [key]: val }))}
        />
      </div>

      <div className="story-generator__preview">
        {selectedContent ? (
          <>
            <StoryCard
              category={category}
              content={selectedContent}
              caption={caption || undefined}
              customStyle={style}
            />

            <div className="story-generator__actions">
              <button
                className="story-generator__btn story-generator__btn--primary"
                onClick={handleShare}
                disabled={sharing}
              >
                <Download size={18} />
                {sharing ? "Sharing…" : "Export to Instagram Story"}
              </button>
              <button className="story-generator__btn story-generator__btn--secondary">
                <ExternalLink size={18} />
                Get the Vibe
              </button>
            </div>
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
