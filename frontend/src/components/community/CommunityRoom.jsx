import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getRoomShares } from '../../services/api';
import StoryCard from '../stories/StoryCard';
import './CommunityRoom.css';

export default function CommunityRoom() {
  const { roomId } = useParams();
  const [posts, setPosts] = useState([]);
  const [filter, setFilter] = useState('recent');

  useEffect(() => {
    // В реальности здесь будет вызов API с фильтром roomId
    getRoomShares(roomId).then(res => setPosts(res.data || []));
  }, [roomId, filter]);

  return (
    <div className="room-page">
      <div className="room-hero" style={{ background: `linear-gradient(180deg, var(--room-color, #7b2ff7) 0%, #121212 100%)` }}>
        <div className="room-hero-content">
          <div className="room-meta">
            <span className="room-tag">Public Space</span>
            <h1>{roomId.replace('-', ' ').toUpperCase()}</h1>
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
          {posts.map(post => (
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
