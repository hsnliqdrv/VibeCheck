import { useState, useEffect, useRef } from "react";
import { getContentByCategory } from "../../services/api";
import "./ContentSelector.css";

const CATEGORY_CONTENT_LABEL = {
  cinema: "Movie or Show",
  music: "Album",
  games: "Game",
  books: "Book",
  travel: "Destination",
};

function getThumbnail(category, item) {
  switch (category) {
    case "cinema":
      return item.poster;
    case "music":
    case "games":
    case "books":
      return item.cover;
    case "travel":
      return item.image;
    default:
      return null;
  }
}

function getSecondary(category, item) {
  switch (category) {
    case "cinema":
      return [item.director, item.year].filter(Boolean).join("  ·  ");
    case "music":
      return item.artist || "";
    case "games":
      return item.platform || "";
    case "books":
      return item.author || "";
    case "travel":
      return [item.city, item.country].filter(Boolean).join(", ");
    default:
      return "";
  }
}

export default function ContentSelector({ category, selected, onSelect }) {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [revealed, setRevealed] = useState(false);
  const [animKey, setAnimKey] = useState(0);
  const prevCategory = useRef(category);
  const reqId = useRef(0);

  const fetchContent = (cat, searchQuery = "") => {
    const id = ++reqId.current;
    setLoading(true);
    setRevealed(false);
    setError(null);
    setItems([]);
    const params = { limit: 5 };
    if (searchQuery) params.search = searchQuery;
    getContentByCategory(cat, params)
      .then((res) => {
        if (id !== reqId.current) return;
        setItems(res.data || []);
        setLoading(false);
        requestAnimationFrame(() => setRevealed(true));
      })
      .catch(() => {
        if (id !== reqId.current) return;
        setItems([]);
        setError("Couldn't load content. Check the server.");
        setLoading(false);
      });
  };

  useEffect(() => {
    if (prevCategory.current !== category) {
      prevCategory.current = category;
      setSearch("");
      setAnimKey((k) => k + 1);
    }

    const delay = search ? 300 : 0;
    const timer = setTimeout(() => {
      fetchContent(category, search.trim());
    }, delay);

    return () => clearTimeout(timer);
  }, [category, search]);

  const contentLabel = CATEGORY_CONTENT_LABEL[category] || "Content";

  return (
    <div className="content-selector">
      <label className="content-selector__label">
        Select a {contentLabel}
      </label>

      <input
        type="text"
        className="content-selector__search"
        placeholder={`Search ${contentLabel.toLowerCase()}s…`}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className={`content-selector__list ${revealed ? "content-selector__list--visible" : ""}`} key={animKey}>
        {loading && (
          <div className="content-selector__status">Loading…</div>
        )}
        {!loading && error && (
          <div className="content-selector__status content-selector__error">{error}</div>
        )}
        {!loading && !error && items.length === 0 && (
          <div className="content-selector__status">No results found</div>
        )}
        {items.map((item, index) => {
          const isActive = selected?.id === item.id;
          const thumb = getThumbnail(category, item);
          const secondary = getSecondary(category, item);

          return (
            <button
              key={item.id}
              type="button"
              className={`content-selector__item ${
                isActive ? "content-selector__item--active" : ""
              }`}
              style={{ animationDelay: `${index * 50}ms` }}
              onClick={() => onSelect(item)}
            >
              <div className="content-selector__thumb">
                {thumb ? (
                  <img src={thumb} alt={item.title || item.name} />
                ) : (
                  <div className="content-selector__thumb-placeholder" />
                )}
              </div>
              <div className="content-selector__meta">
                <span className="content-selector__title">
                  {item.title || item.name}
                </span>
                {secondary && (
                  <span className="content-selector__secondary">
                    {secondary}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
