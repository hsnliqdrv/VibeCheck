import { useState, useCallback, useRef, useMemo } from "react";
import { Clapperboard, Music, Gamepad2, BookOpen, Plane, Download, Share2, ExternalLink, Crosshair, Loader2 } from "lucide-react";
import * as htmlToImage from "html-to-image";
import StoryCard from "./StoryCard";
import ContentSelector from "./ContentSelector";
import StoryCustomizer from "./StoryCustomizer";
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

function getImageFromContent(category, content) {
  if (!content) return null;
  switch (category) {
    case "cinema":
      return content.poster || content.image;
    case "music":
    case "games":
    case "books":
      return content.cover || content.image;
    case "travel":
      return content.image;
    default:
      return null;
  }
}

export default function StoryGenerator() {
  const [category, setCategory] = useState("cinema");
  const [selectedContent, setSelectedContent] = useState(null);
  const [caption, setCaption] = useState("");
  const [shareResult, setShareResult] = useState(null);
  const [style, setStyle] = useState(DEFAULT_STYLE);
  const [exporting, setExporting] = useState(false);
  const exportRef = useRef(null);

  const CATEGORY_GRADIENTS = {
    cinema: "linear-gradient(145deg, #4a0e8f, #7b2ff7, #c471f5)",
    music: "linear-gradient(145deg, #0f2027, #2c5364, #203a43)",
    games: "linear-gradient(145deg, #1a1a2e, #16213e, #0f3460)",
    books: "linear-gradient(145deg, #2d1b69, #6b3fa0, #8e44ad)",
    travel: "linear-gradient(145deg, #134e5e, #71b280, #2ecc71)",
  };

  const exportBgStyle = useMemo(() => {
    const bgColor = style.bgColor;
    const dc = selectedContent?.dominantColor;
    if (bgColor) {
      return { background: `linear-gradient(145deg, ${bgColor}ff, ${bgColor}cc, ${bgColor}88)` };
    }
    if (dc) {
      return { background: `linear-gradient(145deg, ${dc}dd, ${dc}88, ${dc}44)` };
    }
    return { background: CATEGORY_GRADIENTS[category] || CATEGORY_GRADIENTS.cinema };
  }, [style.bgColor, selectedContent?.dominantColor, category]);

  const handleCategoryChange = (key) => {
    setCategory(key);
    setSelectedContent(null);
    setCaption("");
    setShareResult(null);
  };

  const updateStyle = (key, value) => {
    setStyle((prev) => ({ ...prev, [key]: value }));
  };


  const exportStoryImage = useCallback(async (node) => {
    const blob = await htmlToImage.toBlob(node, {
      cacheBust: true,
      pixelRatio: 2,
      width: 1080,
      height: 1920,
      style: {
        transform: 'scale(1)',
        transformOrigin: 'top left',
      },
    });
    return blob;
  }, []);

  const handleDownload = useCallback(async () => {
    if (!exportRef.current) return;
    setExporting(true);
    setShareResult(null);
    try {
      const blob = await exportStoryImage(exportRef.current);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "vibecheck-story.png";
      link.click();
      URL.revokeObjectURL(url);
      setShareResult({ type: "success", message: "Story downloaded!" });
    } catch (err) {
      console.error("Download failed:", err);
      setShareResult({ type: "error", message: "Failed to export image" });
    } finally {
      setExporting(false);
    }
  }, [exportStoryImage]);

  const handleShareImage = useCallback(async () => {
    if (!exportRef.current) return;
    setExporting(true);
    setShareResult(null);
    try {
      const blob = await exportStoryImage(exportRef.current);
      const file = new File([blob], "vibecheck-story.png", { type: "image/png" });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: "My VibeCheck Story" });
        setShareResult({ type: "success", message: "Story shared!" });
      } else {
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "vibecheck-story.png";
        link.click();
        URL.revokeObjectURL(url);
        setShareResult({ type: "success", message: "Story downloaded! Share it to Instagram manually." });
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Share failed:", err);
        setShareResult({ type: "error", message: "Failed to share image" });
      }
    } finally {
      setExporting(false);
    }
  }, [exportStoryImage]);

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
                className={`story-generator__cat-btn ${category === cat.key ? "story-generator__cat-btn--active" : ""
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
          <StoryCustomizer style={style} onChange={updateStyle} dominantColor={selectedContent?.dominantColor} />
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

            {/* Export container */}
            <div className="story-generator__export-wrap" aria-hidden="true">
              <div className="story-generator__export" ref={exportRef} style={exportBgStyle}>
                <StoryCard
                  category={category}
                  content={selectedContent}
                  dominantColor={selectedContent.dominantColor}
                  caption={caption || undefined}
                  customStyle={style}
                  className="story-card--export"
                />
              </div>
            </div>

            <div className="story-generator__actions">
              <button
                type="button"
                className="story-generator__btn story-generator__btn--share"
                onClick={handleShareImage}
                disabled={exporting}
              >
                {exporting ? (
                  <><Loader2 size={18} className="story-generator__spinner" /> Exporting…</>
                ) : (
                  <><Share2 size={18} /> Share to Story</>
                )}
              </button>
              <button
                type="button"
                className="story-generator__btn story-generator__btn--download"
                onClick={handleDownload}
                disabled={exporting}
              >
                <Download size={18} />
                Download Story
              </button>
              <button
                type="button"
                className="story-generator__btn story-generator__btn--secondary"
                onClick={() => {
                  window.location.href = selectedContent['url'] || "#";
                }}
              >
                <ExternalLink size={18} />
                Get the Vibe
              </button>
            </div>

            <p className="story-generator__share-hint">
              On mobile, "Share to Story" opens your share sheet — pick Instagram!
            </p>

            {shareResult && (
              <div
                className={`story-generator__result story-generator__result--${shareResult.type}`}
              >
                {shareResult.type === "success"
                  ? (shareResult.message || "Story shared successfully!")
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
