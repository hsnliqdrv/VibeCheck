// frontend/src/components/community/CommunityRoom.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getRoomShares } from '../../services/api';
import StoryCard from '../stories/StoryCard';
import './CommunityRoom.css';

export default function CommunityRoom() {
  const { roomId } = useParams();
  const [posts, setPosts] = useState([]);
  const [filter, setFilter] = useState('recent');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!roomId) {
      setPosts([]);
      return;
    }

    setLoading(true);
    setError(null);

    // Передаём фильтр как параметр (если API поддерживает)
    getRoomShares(roomId, { filter })
      .then((res) => {
        console.log('getRoomShares response for', roomId, res);

        // Нормализуем разный формат ответа
        let arr = [];
        if (Array.isArray(res)) {
          arr = res;
        } else if (res && Array.isArray(res.data)) {
          arr = res.data;
        } else if (res && Array.isArray(res.shares)) {
          arr = res.shares;
        } else {
          const maybeArray = Object.values(res || {}).find((v) => Array.isArray(v));
          if (maybeArray) arr = maybeArray;
        }

        setPosts(arr);
      })
      .catch((err) => {
        console.error('Error loading room shares:', err);
        setError(err);
        setPosts([]);
      })
      .finally(() => setLoading(false));
  }, [roomId, filter]);

  return (
    <div className="room-page">
      <div className="room-hero" style={{ background: `linear-gradient(180deg, var(--room-color, #7b2ff7) 0%, #121212 100%)` }}>
        <div className="room-hero-content">
          <div className="room-meta">
            <span className="room-tag">Public Space</span>
            <h1>{(roomId || '').replace(/-/g, ' ').toUpperCase()}</h1>
            <div className="room-stats">
              <span><b>12.4k</b> members</span>
              <span><b>450</b> online</span>
            </div>
          </div>
          <div className="room-actions">
            <button className="btn-join-large">Join Room</button>
            <div className="moderators">
              <span>Mod:</span>
              <div className="mod-avatar">V</div>
            </div>
          </div>
        </div>
      </div>

      <div className="room-content">
        <div className="content-filters">
          <button className={filter === 'popular' ? 'active' : ''} onClick={() => setFilter('popular')}>Popular</button>
          <button className={filter === 'recent' ? 'active' : ''} onClick={() => setFilter('recent')}>Recent</button>
        </div>

        <div className="masonry-grid">
          {loading && <div>Loading posts...</div>}
          {error && <div style={{ color: 'salmon' }}>Failed to load posts</div>}

          {!loading && !error && posts.length === 0 && <div>No posts yet</div>}
          {!loading && Array.isArray(posts) && posts.map((post) => (
            <StoryCard
              key={post.id}
              category={post.category}
              content={{ title: post.title, image: post.image }}
              caption={post.caption}
              dominantColor={post.dominant_color}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
