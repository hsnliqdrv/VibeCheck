import { useState } from "react";
import { Palette, Type, Layers, AlignLeft, AlignCenter, ChevronDown, ChevronUp, Droplets, Sparkles } from "lucide-react";
import "./StoryCustomizer.css";

const FONTS = [
  { key: "default", label: "Clean", preview: "Aa" },
  { key: "serif", label: "Classic", preview: "Aa" },
  { key: "mono", label: "Code", preview: "Aa" },
  { key: "handwritten", label: "Script", preview: "Aa" },
  { key: "display", label: "Bold", preview: "Aa" },
];

const BG_COLORS = [
  { key: null, label: "Auto" },
  { key: "__match__", label: "Match" },
  // Darks
  { key: "#1a1a2e", label: "Midnight" },
  { key: "#0f2027", label: "Deep Sea" },
  { key: "#1e1e1e", label: "Charcoal" },
  { key: "#0a0a0a", label: "Void" },
  // Purples & Blues
  { key: "#2d1b69", label: "Purple Night" },
  { key: "#4a0e8f", label: "Royal Purple" },
  { key: "#1e3a5f", label: "Navy" },
  { key: "#0d47a1", label: "Sapphire" },
  { key: "#006064", label: "Teal" },
  // Greens
  { key: "#1b4332", label: "Forest" },
  { key: "#2e7d32", label: "Emerald" },
  // Warms
  { key: "#7f1d1d", label: "Crimson" },
  { key: "#b91c1c", label: "Ruby" },
  { key: "#78350f", label: "Amber" },
  { key: "#c2410c", label: "Burnt Orange" },
  { key: "#92400e", label: "Bronze" },
  // Pastels & Lights
  { key: "#f5f0e8", label: "Cream" },
  { key: "#e8d5f5", label: "Lavender" },
  { key: "#d1e7dd", label: "Mint" },
  { key: "#fde2e4", label: "Blush" },
  { key: "#dbeafe", label: "Sky" },
];

const TEXTURES = [
  { key: "none", label: "None" },
  { key: "noise", label: "Grain" },
  { key: "dots", label: "Dots" },
  { key: "diagonal", label: "Lines" },
  { key: "grid", label: "Grid" },
  { key: "vignette", label: "Vignette" },
  { key: "frosted-glass", label: "Frosted", icon: Droplets },
  { key: "liquid-glass", label: "Liquid", icon: Sparkles },
];

const TITLE_SIZES = [
  { key: "small", label: "S" },
  { key: "normal", label: "M" },
  { key: "large", label: "L" },
];

const LAYOUTS = [
  { key: "default", label: "Standard" },
  { key: "centered", label: "Centered" },
  { key: "minimal", label: "Minimal" },
];

export default function StoryCustomizer({ style, onChange, dominantColor }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="story-customizer">
      <button
        type="button"
        className="story-customizer__toggle"
        onClick={() => setOpen((v) => !v)}
      >
        <Palette size={16} />
        <span>Customize Story</span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div className="story-customizer__body">
          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <Type size={14} />
              Font
            </div>
            <div className="story-customizer__chips">
              {FONTS.map((f) => (
                <button
                  key={f.key}
                  type="button"
                  className={`story-customizer__chip story-customizer__chip--font-${f.key} ${style.font === f.key ? "story-customizer__chip--active" : ""
                    }`}
                  onClick={() => onChange("font", f.key)}
                >
                  <span className="story-customizer__chip-preview">{f.preview}</span>
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <Palette size={14} />
              Background
            </div>
            <div className="story-customizer__swatches">
              {BG_COLORS.map((c) => {
                const isMatch = c.key === "__match__";
                const swatchColor = isMatch ? dominantColor : c.key;
                const isActive = isMatch
                  ? style.bgColor === dominantColor && dominantColor != null
                  : style.bgColor === c.key;

                return (
                  <button
                    key={c.key ?? "auto"}
                    type="button"
                    className={`story-customizer__swatch ${isActive ? "story-customizer__swatch--active" : ""
                      } ${isMatch ? "story-customizer__swatch--match" : ""}`}
                    style={{
                      background: swatchColor
                        ? swatchColor
                        : c.key === null
                          ? "conic-gradient(#6b6bf8, #b44aff, #ff6eb4, #6b6bf8)"
                          : "#888",
                    }}
                    title={isMatch ? `Match (${dominantColor || "no image"})` : c.label}
                    onClick={() =>
                      onChange("bgColor", isMatch ? dominantColor : c.key)
                    }
                    disabled={isMatch && !dominantColor}
                  />
                );
              })}
            </div>
          </div>

          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <Layers size={14} />
              Texture
            </div>
            <div className="story-customizer__chips">
              {TEXTURES.map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.key}
                    type="button"
                    className={`story-customizer__chip ${style.bgTexture === t.key ? "story-customizer__chip--active" : ""
                      } ${t.key === "frosted-glass" || t.key === "liquid-glass"
                        ? "story-customizer__chip--glass"
                        : ""
                      }`}
                    onClick={() => onChange("bgTexture", t.key)}
                  >
                    {Icon && <Icon size={13} />}
                    {t.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <AlignLeft size={14} />
              Alignment
            </div>
            <div className="story-customizer__chips">
              <button
                type="button"
                className={`story-customizer__chip ${style.textAlign === "left" ? "story-customizer__chip--active" : ""
                  }`}
                onClick={() => onChange("textAlign", "left")}
              >
                <AlignLeft size={14} />
                Left
              </button>
              <button
                type="button"
                className={`story-customizer__chip ${style.textAlign === "center" ? "story-customizer__chip--active" : ""
                  }`}
                onClick={() => onChange("textAlign", "center")}
              >
                <AlignCenter size={14} />
                Center
              </button>
            </div>
          </div>

          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <Type size={14} />
              Title Size
            </div>
            <div className="story-customizer__chips">
              {TITLE_SIZES.map((s) => (
                <button
                  key={s.key}
                  type="button"
                  className={`story-customizer__chip ${style.titleSize === s.key ? "story-customizer__chip--active" : ""
                    }`}
                  onClick={() => onChange("titleSize", s.key)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <Layers size={14} />
              Layout
            </div>
            <div className="story-customizer__chips">
              {LAYOUTS.map((l) => (
                <button
                  key={l.key}
                  type="button"
                  className={`story-customizer__chip ${style.cardLayout === l.key ? "story-customizer__chip--active" : ""
                    }`}
                  onClick={() => onChange("cardLayout", l.key)}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
