// frontend/src/components/community/Community.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  getCommunityRooms,
  getCommunityRoomDetails,
} from '../../services/api';
import './Community.css';

const FallbackRooms = [
  { id: 'neon-noir', name: 'Neon Noir', members: 12453, posts: 3842, image: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f', color: '#ff6fb3' },
  { id: 'dark-academia', name: 'Dark Academia', members: 18926, posts: 5621, image: 'https://images.unsplash.com/photo-1514894780063-588132192a9a', color: '#8a5a3b' },
  { id: 'gothic-romance', name: 'Gothic Romance', members: 8456, posts: 2341, image: 'https://images.unsplash.com/photo-1509395176047-4a66953fd231', color: '#8b2b2b' },
];

function normalizeRoomsResponse(res) {
  // Универсальная нормализация — возвращаем массив объектов {id,name,image,members,posts,color,is_trending,tags}
  let arr = [];
  if (!res) return arr;
  if (Array.isArray(res)) arr = res;
  else if (res.rooms) arr = res.rooms;
  else if (res.data) arr = res.data;
  else if (res.items) arr = res.items;
  else {
    const maybe = Object.values(res).find((v) => Array.isArray(v));
    if (maybe) arr = maybe;
  }
  return arr.map((r, i) => ({
    id: r.id || r._id || `room-${i}`,
    name: r.title || r.name || r.display_name || 'Untitled',
    subtitle: r.subtitle || r.description || '',
    image: r.image || r.header_image || r.cover || '',
    members: (r.members_count ?? r.members ?? r.followers ?? 0),
    posts: (r.posts_count ?? r.posts ?? r.shares ?? 0),
    color: r.color || r.accent || ['#7b2ff7','#ff7ab6','#f6a623'][i % 3],
    is_trending: !!r.is_trending || !!r.trending,
    tags: r.tags || r.hashtags || [],
  }));
}

export default function Community() {
  const [rooms, setRooms] = useState(FallbackRooms);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getCommunityRooms()
      .then((res) => {
        if (!mounted) return;
        const arr = normalizeRoomsResponse(res);
        if (arr.length) setRooms(arr);
      })
      .catch((err) => {
        console.warn('getCommunityRooms failed:', err);
        setError(err);
      })
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, []);

  const trending = rooms.filter(r => r.is_trending).slice(0, 3);
  const top = trending.length ? trending : rooms.slice(0, 3);

  return (
    <div className="community-page">
      <header className="community-header">
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
          <div>
            <h1>Community Moodboards</h1>
            <p>Join aesthetic rooms and share your curated vibes</p>
          </div>
          <div style={{display:'flex', gap:12, alignItems:'center'}}>
            <button className="btn-create">+ Create Room</button>
          </div>
        </div>
      </header>

      <section className="trending-section">
        <h2 className="section-title">Trending Now</h2>
        <div className="trending-grid">
          {loading && <div className="placeholder">Loading trending...</div>}
          {!loading && top.map(room => (
            <Link
              key={room.id}
              to={`/community/${room.id}`}
              className="trending-card"
              style={{ '--accent': room.color }}
            >
              {room.image ? <img src={room.image} alt={room.name} /> : <div className="no-image" />}
              <div className="card-content">
                <div className="card-meta">
                  {room.is_trending && <span className="badge-trending">Trending</span>}
                </div>
                <h3>{room.name}</h3>
                <span>{Number(room.members).toLocaleString()} members • {Number(room.posts).toLocaleString()} posts</span>
                {room.tags && room.tags.length > 0 && <div className="tags-row">{room.tags.slice(0,3).map(t=> <span className="tag" key={t}>{t}</span>)}</div>}
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="all-rooms-section">
        <h2 className="section-title">All Aesthetic Rooms</h2>
        <div className="rooms-grid">
          {loading && <div className="placeholder">Loading rooms...</div>}
          {!loading && rooms.map(room => (
            <Link to={`/community/${room.id}`} key={room.id} className="room-item">
              <div className="room-icon" style={{ backgroundImage: `linear-gradient(135deg, ${room.color}22, #00000022)`, backgroundColor: room.color }} />
              <div className="room-info">
                <h4>{room.name}</h4>
                <p>{Number(room.members).toLocaleString()} members</p>
              </div>
              <button className="join-btn-small">Join</button>
            </Link>
          ))}
          {!loading && rooms.length === 0 && <div className="placeholder">No rooms yet</div>}
        </div>
      </section>
    </div>
  );
}
