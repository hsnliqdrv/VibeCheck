import { useState } from "react";
import { Palette, Type, Layers, AlignLeft, AlignCenter, ChevronDown, ChevronUp } from "lucide-react";
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
  { key: "#1a1a2e", label: "Midnight" },
  { key: "#0f2027", label: "Deep Sea" },
  { key: "#2d1b69", label: "Purple Night" },
  { key: "#1b4332", label: "Forest" },
  { key: "#7f1d1d", label: "Crimson" },
  { key: "#78350f", label: "Amber" },
  { key: "#1e1e1e", label: "Charcoal" },
  { key: "#f5f0e8", label: "Cream" },
];

const TEXTURES = [
  { key: "none", label: "None" },
  { key: "noise", label: "Grain" },
  { key: "dots", label: "Dots" },
  { key: "diagonal", label: "Lines" },
  { key: "grid", label: "Grid" },
  { key: "vignette", label: "Vignette" },
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

export default function StoryCustomizer({ style, onChange }) {
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
          {/* Font */}
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
                  className={`story-customizer__chip story-customizer__chip--font-${f.key} ${
                    style.font === f.key ? "story-customizer__chip--active" : ""
                  }`}
                  onClick={() => onChange("font", f.key)}
                >
                  <span className="story-customizer__chip-preview">{f.preview}</span>
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Background Color */}
          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <Palette size={14} />
              Background
            </div>
            <div className="story-customizer__swatches">
              {BG_COLORS.map((c) => (
                <button
                  key={c.key ?? "auto"}
                  type="button"
                  className={`story-customizer__swatch ${
                    style.bgColor === c.key ? "story-customizer__swatch--active" : ""
                  }`}
                  style={{
                    background: c.key
                      ? c.key
                      : "conic-gradient(#6b6bf8, #b44aff, #ff6eb4, #6b6bf8)",
                  }}
                  title={c.label}
                  onClick={() => onChange("bgColor", c.key)}
                />
              ))}
            </div>
          </div>

          {/* Texture */}
          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <Layers size={14} />
              Texture
            </div>
            <div className="story-customizer__chips">
              {TEXTURES.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  className={`story-customizer__chip ${
                    style.bgTexture === t.key ? "story-customizer__chip--active" : ""
                  }`}
                  onClick={() => onChange("bgTexture", t.key)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Text Align */}
          <div className="story-customizer__section">
            <div className="story-customizer__section-label">
              <AlignLeft size={14} />
              Alignment
            </div>
            <div className="story-customizer__chips">
              <button
                type="button"
                className={`story-customizer__chip ${
                  style.textAlign === "left" ? "story-customizer__chip--active" : ""
                }`}
                onClick={() => onChange("textAlign", "left")}
              >
                <AlignLeft size={14} />
                Left
              </button>
              <button
                type="button"
                className={`story-customizer__chip ${
                  style.textAlign === "center" ? "story-customizer__chip--active" : ""
                }`}
                onClick={() => onChange("textAlign", "center")}
              >
                <AlignCenter size={14} />
                Center
              </button>
            </div>
          </div>

          {/* Title Size */}
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
                  className={`story-customizer__chip ${
                    style.titleSize === s.key ? "story-customizer__chip--active" : ""
                  }`}
                  onClick={() => onChange("titleSize", s.key)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Layout */}
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
                  className={`story-customizer__chip ${
                    style.cardLayout === l.key ? "story-customizer__chip--active" : ""
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
