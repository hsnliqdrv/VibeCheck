import { useState, useEffect } from "react";
import { Search, Loader2, AlertCircle } from "lucide-react";
import { getContentByCategory } from "../../services/api";
import "./ContentSelector.css";

export default function ContentSelector({ category, selected, onSelect }) {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const loadContent = async (query = "") => {
    setLoading(true);
    setError(null);
    try {
      const response = await getContentByCategory(category, query);
      const data = response?.data || response;
      
      if (Array.isArray(data)) {
        setItems(data);
      } else {
        console.error("API returned non-array data:", data);
        setItems([]);
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Check the server connection");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    loadContent();
  }, [category]);
  const handleSearch = (e) => {
    e.preventDefault();
    loadContent(search);
  };

  return (
    <div className="content-selector">
      <form className="content-search" onSubmit={handleSearch}>
        <div className="search-input-wrapper">
          <input
            type="text"
            placeholder={`Search in category ${category}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
          </button>
        </div>
      </form>

      <div className="content-selector__results-container">
        {loading && (
          <div className="content-selector__status">
            <Loader2 className="animate-spin" /> Ищем...
          </div>
        )}

        {error && (
          <div className="content-selector__status content-selector__error">
            <AlertCircle size={18} /> {error}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="content-selector__status">Ничего не найдено</div>
        )}

        {!loading && items.length > 0 && (
          <div className="content-selector__list content-selector__list--visible">
            {items.map((item, index) => (
              <button
                key={item.id || index}
                type="button"
                className={`content-selector__item ${
                  selected?.id === item.id ? "content-selector__item--active" : ""
                }`}
                onClick={() => onSelect(item)}
              >
                <div className="content-selector__thumb">
                  {(item.poster || item.cover || item.image) ? (
                    <img src={item.poster || item.cover || item.image} alt={item.title} />
                  ) : (
                    <div className="content-selector__thumb-placeholder" />
                  )}
                </div>
                <div className="content-selector__meta">
                  <span className="content-selector__title">{item.title || item.name}</span>
                  <span className="content-selector__secondary">
                    {item.year || item.artist || item.author || ""}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
