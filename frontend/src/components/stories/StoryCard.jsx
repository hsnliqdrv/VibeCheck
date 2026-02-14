import { Clapperboard, Music, Gamepad2, BookOpen, Plane } from "lucide-react";
import "./StoryCard.css";

const CATEGORY_ICONS = { cinema: Clapperboard, music: Music, games: Gamepad2, books: BookOpen, travel: Plane };
const CATEGORY_LABELS = { cinema: "NOW WATCHING", music: "NOW LISTENING", games: "NOW PLAYING", books: "NOW READING", travel: "NOW EXPLORING" };
const TITLE_SIZES = { small: "1.2rem", normal: "1.5rem", large: "2rem" };

export default function StoryCard({ category, content, customStyle, caption }) {
  const image = content?.image || content?.poster || content?.image_url; 
  const title = content?.title || content?.name || "Untitled";
  const subtitle = content?.subtitle || content?.year || content?.director || content?.artist;

  const { font, textAlign, titleSize, cardLayout, bgColor } = customStyle || {};

  return (
    <div 
      className={`story-card story-card--layout-${cardLayout || 'default'}`} 
      style={{ 
        background: bgColor || 'linear-gradient(145deg, #4a0e8f, #7b2ff7)', 
        fontFamily: font 
      }}
    >
      <div className="story-card__badge-container">
        <span className="story-card__badge">{CATEGORY_LABELS[category]}</span>
      </div>

      <div className="story-card__image-wrap">
        {image ? (
          <img src={image} alt={title} className="story-card__image" />
        ) : (
          <div className="story-card__image-placeholder">
            {(() => {
              const Icon = CATEGORY_ICONS[category];
              return Icon ? <Icon size={56} opacity={0.6} /> : null;
            })()}
          </div>
        )}
      </div>

      <div className="story-card__info" style={{ textAlign: textAlign || 'left' }}>
        <h3 className="story-card__title" style={{ fontSize: TITLE_SIZES[titleSize] || TITLE_SIZES.normal }}>
          {title}
        </h3>
        {subtitle && <p className="story-card__subtitle">{subtitle}</p>}
        {caption && <p className="story-card__caption">"{caption}"</p>}
      </div>
    </div>
  );
}
