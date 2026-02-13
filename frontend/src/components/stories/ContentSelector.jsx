import { useState } from "react";
import { Search } from "lucide-react";

export default function ContentSelector({ onSelect, category }) {
  const [query, setQuery] = useState("");

  const handleTriggerSearch = () => {
    console.log("Searching for:", query);
  };

  return (
    <div className="content-search">
      <div className="search-input-wrapper">
        <input 
          type="text" 
          placeholder={`Search ${category}...`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="button" onClick={handleTriggerSearch} className="search-btn">
          <Search size={18} />
          <span>Search</span>
        </button>
      </div>
    </div>
  );
}
