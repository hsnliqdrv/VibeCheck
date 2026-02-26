import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCommunityRooms } from '../../services/api';
import './Community.css';

export default function Community() {
  const [rooms, setRooms] = useState([]);

  useEffect(() => {
    getCommunityRooms().then(setRooms);
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
          {rooms.slice(0, 2).map(room => (
            <Link to={`/community/${room.id}`} key={room.id} className="trending-card" style={{ '--accent': room.color }}>
              <img src={room.image} alt={room.name} />
              <div className="card-content">
                <h3>{room.name}</h3>
                <span>{room.members} members</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="all-rooms-section">
        <h2 className="section-title">All Aesthetic Rooms</h2>
        <div className="rooms-grid">
          {rooms.map(room => (
            <Link to={`/community/${room.id}`} key={room.id} className="room-item">
              <div className="room-icon" style={{ backgroundColor: room.color }}></div>
              <div className="room-info">
                <h4>{room.name}</h4>
                <p>{room.members} members</p>
              </div>
              <button className="join-btn-small">Join</button>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
