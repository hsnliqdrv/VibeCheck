// frontend/src/components/community/CommunityRoom.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getRoomShares, getCommunityRoomDetails } from '../../services/api';
import StoryCard from '../stories/StoryCard';
import './CommunityRoom.css';

export default function CommunityRoom() {
  const { roomId } = useParams();
  const [room, setRoom] = useState(null);
  const [posts, setPosts] = useState([]);
  const [filter, setFilter] = useState('popular');
  const [cursor, setCursor] = useState(null);
  const [loadingRoom, setLoadingRoom] = useState(true);
  const [loadingPosts, setLoadingPosts] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!roomId) return;
    setLoadingRoom(true);
    getCommunityRoomDetails(roomId)
      .then((res) => {
        // Try normalize: res.room || res.data || res
        const r = res && (res.room || res.data || res);
        setRoom({
          id: r.id || roomId,
          title: r.title || r.name || roomId,
          subtitle: r.subtitle || r.description || '',
          header_image: r.header_image || r.image || r.cover || '',
          members: r.members_count || r.members || 0,
          posts_count: r.posts_count || r.posts || 0,
          moderators: r.moderators || r.mods || [],
          tags: r.tags || r.hashtags || [],
          color: r.color || '#7b2ff7',
        });
      })
      .catch((err) => {
        console.warn('getCommunityRoomDetails failed', err);
        setError(err);
      })
      .finally(() => setLoadingRoom(false));
  }, [roomId]);

  useEffect(() => {
    if (!roomId) return;
    setLoadingPosts(true);
    setError(null);
    getRoomShares(roomId, { filter, cursor: null, limit: 12 })
      .then((res) => {
        // Normalize posts array
        let arr = [];
        if (Array.isArray(res)) arr = res;
        else if (res.data) arr = res.data;
        else if (res.shares) arr = res.shares;
        else {
          const maybe = Object.values(res || {}).find((v) => Array.isArray(v));
          if (maybe) arr = maybe;
        }
        setPosts(arr);
        // try to set next cursor if backend provides it
        if (res && res.next_cursor) setCursor(res.next_cursor);
        else setCursor(null);
      })
      .catch((err) => {
        console.warn('getRoomShares failed', err);
        setError(err);
        setPosts([]);
      })
      .finally(() => setLoadingPosts(false));
  }, [roomId, filter]);

  const loadMore = () => {
    if (!roomId || !cursor) return;
    setLoadingPosts(true);
    getRoomShares(roomId, { filter, cursor, limit: 12 })
      .then((res) => {
        let arr = [];
        if (Array.isArray(res)) arr = res;
        else if (res.data) arr = res.data;
        else if (res.shares) arr = res.shares;
        else {
          const maybe = Object.values(res || {}).find((v) => Array.isArray(v));
          if (maybe) arr = maybe;
        }
        setPosts(p => [...p, ...arr]);
        if (res && res.next_cursor) setCursor(res.next_cursor);
        else setCursor(null);
      })
      .catch((err) => {
        console.warn('loadMore failed', err);
      })
      .finally(() => setLoadingPosts(false));
  };

  return (
    <div className="room-page">
      <div
        className="room-hero"
        style={{
          background: room && room.header_image
            ? `url(${room.header_image}) center/cover no-repeat`
            : `linear-gradient(90deg, ${room?.color || '#7b2ff7'}, #121212)`,
        }}
      >
        <div className="room-hero-content">
          <div className="room-meta">
            <span className="room-tag">Public Space</span>
            <h1>{room ? room.title : (roomId || '').replace(/-/g, ' ')}</h1>
            <div className="room-stats">
              <span><b>{room ? Number(room.members).toLocaleString() : '—'}</b> members</span>
              <span>•</span>
              <span><b>{room ? Number(room.posts_count).toLocaleString() : '—'}</b> posts</span>
            </div>
            <div style={{marginTop:8}}>
              {room && room.tags && room.tags.slice(0,3).map(t=> <span key={t} className="tag" style={{marginRight:8}}>{t}</span>)}
            </div>
          </div>

          <div className="room-actions">
            <button className="btn-join-large">Join Room</button>
            <div style={{marginTop:12}}>
              {room && room.moderators && room.moderators.slice(0,3).map((m,i)=> (
                <img key={i} src={m.avatar || m.photo || ''} alt={m.display_name || m.name} style={{width:36,height:36,borderRadius:10,objectFit:'cover',marginLeft:8}} />
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="room-content">
        <div className="content-filters" style={{marginTop:12}}>
          <div style={{flex:1}}>
            <input className="search-input" placeholder="Search posts in this room..." style={{width:'100%', padding:12, borderRadius:12, border:'1px solid rgba(255,255,255,0.06)'}} />
          </div>
          <div style={{display:'flex', gap:12, marginLeft:12}}>
            <button className={filter === 'popular' ? 'active' : ''} onClick={() => setFilter('popular')}>Popular</button>
            <button className={filter === 'recent' ? 'active' : ''} onClick={() => setFilter('recent')}>Recent</button>
          </div>
        </div>

        <div className="masonry-grid">
          {loadingPosts && <div className="placeholder">Loading posts...</div>}
          {!loadingPosts && posts.length === 0 && <div className="placeholder">No posts yet. Be the first to share!</div>}
          {!loadingPosts && posts.map(p => (
            <StoryCard
              key={p.id || p._id}
              category={p.category || p.type || ''}
              content={{ title: p.title || '', image: p.image || p.cover || p.media }}
              caption={p.caption || p.excerpt || ''}
              dominantColor={p.dominant_color || p.color}
            />
          ))}
        </div>

        {cursor && (
          <div style={{textAlign:'center', marginTop:20}}>
            <button className="btn-create" onClick={loadMore}>{loadingPosts ? 'Loading...' : 'Load More Posts'}</button>
          </div>
        )}
      </div>
    </div>
  );
}
