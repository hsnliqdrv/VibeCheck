// frontend/src/components/community/Community.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCommunityRooms } from '../../services/api';
import './Community.css';

const initialRooms = [
  {
    id: 'neon-noir',
    name: 'Neon Noir',
    members: '12,453',
    image: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f',
    color: '#ff00cc',
  },
  {
    id: 'dark-academia',
    name: 'Dark Academia',
    members: '18,926',
    image: 'https://images.unsplash.com/photo-1514894780063-588132192a9a',
    color: '#5d4037',
  },
];

export default function Community() {
  const [rooms, setRooms] = useState(initialRooms);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    getCommunityRooms()
      .then((res) => {
        console.log('getCommunityRooms response:', res);

        // Нормализуем ответ в массив комнат.
        let roomsArray = [];
        if (Array.isArray(res)) {
          roomsArray = res;
        } else if (res && Array.isArray(res.data)) {
          roomsArray = res.data;
        } else if (res && Array.isArray(res.rooms)) {
          roomsArray = res.rooms;
        } else if (res && Array.isArray(res.items)) {
          roomsArray = res.items;
        } else {
          const maybeArray = Object.values(res || {}).find((v) => Array.isArray(v));
          if (maybeArray) roomsArray = maybeArray;
        }

        // Если пришёл непустой список — обновляем комнаты.
        if (Array.isArray(roomsArray) && roomsArray.length > 0) {
          setRooms(roomsArray);
        } else {
          // оставляем initialRooms как fallback
          setRooms((prev) => prev && prev.length > 0 ? prev : []);
        }
      })
      .catch((err) => {
        console.error('Error loading community rooms:', err);
        setError(err);
        setRooms([]); // можно оставить примеры, но: устанавливаем пустой список для явного состояния ошибки
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="community-page">
      <header className="community-header">
        <h1>Community</h1>
        <p>Explore aesthetic spaces curated by the vibe.</p>
      </header>

      <section className="trending-section">
        <h2 className="section-title">Trending Now</h2>
        <div className="trending-grid">
          {loading && <div>Loading...</div>}
          {error && <div style={{ color: 'salmon' }}>Failed to load rooms</div>}

          {!loading && !error && Array.isArray(rooms) && rooms.slice(0, 2).map((room) => (
            <Link
              to={`/community/${room.id}`}
              key={room.id}
              className="trending-card"
              style={{ '--accent': room.color || '#7b2ff7' }}
            >
              {room.image ? <img src={room.image} alt={room.name} /> : <div style={{height: '100%', background:'#222'}}/>}
              <div className="card-content">
                <h3>{room.name}</h3>
                <span>{room.members ?? 0} members</span>
              </div>
            </Link>
          ))}

          {!loading && !error && (!Array.isArray(rooms) || rooms.length === 0) && (
            <div>No rooms yet</div>
          )}
        </div>
      </section>

      <section className="all-rooms-section">
        <h2 className="section-title">All Aesthetic Rooms</h2>
        <div className="rooms-grid">
          {Array.isArray(rooms) && rooms.map((room) => (
            <Link to={`/community/${room.id}`} key={room.id} className="room-item">
              <div className="room-icon" style={{ backgroundColor: room.color || '#444' }} />
              <div className="room-info">
                <h4>{room.name}</h4>
                <p>{room.members ?? 0} members</p>
              </div>
              <button className="join-btn-small">Join</button>
            </Link>
          ))}

          {!Array.isArray(rooms) && !loading && <div>No rooms to show</div>}
        </div>
      </section>
    </div>
  );
}
