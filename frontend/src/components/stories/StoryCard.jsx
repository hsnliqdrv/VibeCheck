import { useMemo } from "react";
import { Clapperboard, Music, Gamepad2, BookOpen, Plane } from "lucide-react";
import "./StoryCard.css";

const CATEGORY_ICONS = {
  cinema: Clapperboard,
  music: Music,
  games: Gamepad2,
  books: BookOpen,
  travel: Plane,
};

const CATEGORY_LABELS = {
  cinema: "NOW WATCHING",
  music: "NOW LISTENING",
  games: "NOW PLAYING",
  books: "NOW READING",
  travel: "NOW EXPLORING",
};

const CATEGORY_GRADIENTS = {
  cinema: "linear-gradient(145deg, #4a0e8f, #7b2ff7, #c471f5)",
  music: "linear-gradient(145deg, #0f2027, #2c5364, #203a43)",
  games: "linear-gradient(145deg, #1a1a2e, #16213e, #0f3460)",
  books: "linear-gradient(145deg, #2d1b69, #6b3fa0, #8e44ad)",
  travel: "linear-gradient(145deg, #134e5e, #71b280, #2ecc71)",
};

const FONT_FAMILIES = {
  default: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  serif: '"Georgia", "Times New Roman", serif',
  mono: '"SF Mono", "Fira Code", "Consolas", monospace',
  handwritten: '"Segoe Script", "Comic Sans MS", cursive',
  display: '"Impact", "Arial Black", sans-serif',
};

const TITLE_SIZES = {
  small: "1.05rem",
  normal: "1.35rem",
  large: "1.75rem",
};

const TEXTURE_OVERLAYS = {
  none: null,
  noise: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.15'/%3E%3C/svg%3E\")",
  dots: "radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1px)",
  diagonal: "repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.04) 10px, rgba(255,255,255,0.04) 20px)",
  grid: "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
  vignette: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)",
};

const TEXTURE_SIZES = {
  dots: "16px 16px",
  grid: "24px 24px",
};

function getSubtitle(category, content) {
  if (!content) return "";
  switch (category) {
    case "cinema":
      return [content.year, content.director].filter(Boolean).join("  ·  ");
    case "music":
      return content.artist || "";
    case "games":
      return content.platform || "";
    case "books":
      return content.author || "";
    case "travel":
      return [content.city, content.country].filter(Boolean).join(", ");
    default:
      return "";
  }
}

function getContentImage(category, content) {
  if (!content) return null;
  switch (category) {
    case "cinema":
      return content.poster || content.image;
    case "music":
      return content.cover || content.image;
    case "games":
      return content.cover || content.image;
    case "books":
      return content.cover || content.image;
    case "travel":
      return content.image;
    default:
      return content.image;
  }
}

export default function StoryCard({
  category = "cinema",
  content,
  dominantColor,
  caption,
  customStyle = {},
  className = "",
}) {
  const label = CATEGORY_LABELS[category] || "NOW VIBING";
  const title = content?.title || content?.name || "Untitled";
  const subtitle = getSubtitle(category, content);
  const image = getContentImage(category, content);

  const {
    font = "default",
    bgColor = null,
    bgTexture = "none",
    textAlign = "left",
    titleSize = "normal",
    cardLayout = "default",
  } = customStyle;

  const bgStyle = useMemo(() => {
    if (bgColor) {
      return {
        background: `linear-gradient(145deg, ${bgColor}ff, ${bgColor}cc, ${bgColor}88)`,
      };
    }
    if (dominantColor) {
      return {
        background: `linear-gradient(145deg, ${dominantColor}dd, ${dominantColor}88, ${dominantColor}44)`,
      };
    }
    return { background: CATEGORY_GRADIENTS[category] };
  }, [dominantColor, category, bgColor]);

  const isLight = bgColor && isLightColor(bgColor);
  const textColor = isLight ? "#1d1b22" : "#fff";

  const cardClasses = [
    "story-card",
    `story-card--layout-${cardLayout}`,
    className,
  ].filter(Boolean).join(" ");

  const showEpisodeBadge =
    category === "cinema" &&
    content?.type === "tv" &&
    content?.season != null &&
    content?.episode != null;

  return (
    <div className={cardClasses} style={{ ...bgStyle, fontFamily: FONT_FAMILIES[font], color: textColor }}>
      {/* Texture overlay */}
      {bgTexture !== "none" && TEXTURE_OVERLAYS[bgTexture] && (
        <div
          className="story-card__texture"
          style={{
            backgroundImage: TEXTURE_OVERLAYS[bgTexture],
            backgroundSize: TEXTURE_SIZES[bgTexture] || "cover",
          }}
        />
      )}

      <div className="story-card__top">
        <span className="story-card__badge story-card__badge--category">
          {label}
        </span>
        {showEpisodeBadge && (
          <span className="story-card__badge story-card__badge--episode">
            S{content.season} E{content.episode}
          </span>
        )}
        {category === "games" && content?.difficulty && (
          <span className="story-card__badge story-card__badge--difficulty">
            {content.difficulty}
          </span>
        )}
        {category === "books" && content?.totalPages && (
          <span className="story-card__badge story-card__badge--pages">
            {content.totalPages}p
          </span>
        )}
        {category === "travel" && content?.weather && (
          <span className="story-card__badge story-card__badge--weather">
            {content.weather}{" "}
            {content.temperature != null ? `${content.temperature}°` : ""}
          </span>
        )}
      </div>

      <div className="story-card__image-wrap">
        {image ? (
          <img src={image} alt={title} className="story-card__image" />
        ) : (
          <div className="story-card__image-placeholder">
            {(() => {
              const Icon = CATEGORY_ICONS[category];
              return Icon ? <Icon size={56} strokeWidth={1.2} opacity={0.6} /> : null;
            })()}
          </div>
        )}
      </div>

      <div className="story-card__info" style={{ textAlign }}>
        <h3 className="story-card__title" style={{ fontSize: TITLE_SIZES[titleSize] }}>{title}</h3>
        {subtitle && <p className="story-card__subtitle">{subtitle}</p>}
        {caption && <p className="story-card__caption">"{caption}"</p>}
      </div>
    </div>
  );
}

function isLightColor(hex) {
  const c = hex.replace("#", "");
  const r = parseInt(c.substring(0, 2), 16);
  const g = parseInt(c.substring(2, 4), 16);
  const b = parseInt(c.substring(4, 6), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 160;
}
