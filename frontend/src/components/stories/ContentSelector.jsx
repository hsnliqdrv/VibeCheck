import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import axios from "axios";

const API_BASE_URL = "http://localhost:3000";

export default function ContentSelector({ onSelect, category }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleTriggerSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/content/${category}?query=${query}`);
      setResults(response.data || []);
      console.log("Found results:", response.data);
    } catch (error) {
      console.error("Search error:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="content-selector">
      <div className="content-search">
        <div className="search-input-wrapper">
          <input 
            type="text" 
            placeholder={`Search ${category}...`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleTriggerSearch()}
          /> 
          
          <button type="button" onClick={handleTriggerSearch} className="search-btn" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
            <span>Search</span>
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="content-selector__list content-selector__list--visible">
          {results.map((item) => (
            <button
              key={item.id || item.imdbID}
              className="content-selector__item"
              onClick={() => onSelect(item)}
            >
              <div className="content-selector__thumb">
                {item.poster || item.image ? (
                  <img src={item.poster || item.image} alt={item.title} />
                ) : (
                  <div className="content-selector__thumb-placeholder" />
                )}
              </div>
              <div className="content-selector__meta">
                <span className="content-selector__title">{item.title || item.name}</span>
                <span className="content-selector__secondary">
                  {item.year} {item.director ? `· ${item.director}` : ''}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
