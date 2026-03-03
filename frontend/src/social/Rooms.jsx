import React, { useState, useEffect } from 'react';
import {
  Search,
  ChevronRight,
  Users,
  MessageSquare,
  Heart,
  LogIn,
  LogOut,
  Loader2,
  AlertCircle,
  Flame,
  Plus,
  X,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getAestheticRooms,
  getRoomById,
  getRoomPosts,
  createRoomPost,
  joinRoom,
  leaveRoom,
  likePost,
  unlikePost,
  getPostComments,
  addComment,
  getUserById,
} from '../services/api';
import './Rooms.css';

const PLATFORM_ICONS = {
  instagram: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5M12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10m0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>,
  twitter:   <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.835L1.254 2.25H8.08l4.253 5.622L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>,
  tiktok:    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M16.6 5.82s.51.5 0 0A4.278 4.278 0 0 1 15.54 3h-3.09v12.4a2.592 2.592 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64 0 3.33 2.76 5.7 5.69 5.7 3.14 0 5.69-2.55 5.69-5.7V9.01a7.35 7.35 0 0 0 4.3 1.38V7.3s-1.88.09-3.24-1.48z"/></svg>,
  youtube:   <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/></svg>,
  facebook:  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2.04c-5.5 0-10 4.49-10 10.02 0 5 3.66 9.15 8.44 9.9v-7H7.9v-2.9h2.54V9.85c0-2.51 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.78-1.63 1.57v1.88h2.78l-.45 2.9h-2.33v7a10 10 0 0 0 8.44-9.9c0-5.53-4.5-10.02-10.01-10.02z"/></svg>,
  linkedin:  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/></svg>,
  pinterest: <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M9.04 21.54c.96.29 1.93.46 2.96.46a10 10 0 0 0 10-10A10 10 0 0 0 12 2 10 10 0 0 0 2 12c0 4.25 2.67 7.9 6.44 9.34-.09-.78-.18-2.07 0-2.96l1.15-4.94s-.29-.58-.29-1.5c0-1.38.86-2.41 1.84-2.41.86 0 1.26.63 1.26 1.44 0 .86-.57 2.09-.86 3.27-.17.98.52 1.84 1.52 1.84 1.78 0 3.16-1.9 3.16-4.58 0-2.4-1.72-4.04-4.19-4.04-2.82 0-4.48 2.1-4.48 4.31 0 .86.28 1.73.71 2.22.06.09.09.17.06.29l-.29 1.09c0 .17-.11.23-.28.11-1.28-.56-2.02-2.38-2.02-3.85 0-3.16 2.24-6.03 6.56-6.03 3.44 0 6.12 2.47 6.12 5.75 0 3.44-2.13 6.2-5.18 6.2-.97 0-1.92-.52-2.26-1.13l-.67 2.37c-.23.86-.86 2.01-1.29 2.7z"/></svg>,
  spotify:   <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10 10 10 0 0 0 10-10A10 10 0 0 0 12 2m4.38 14.42c-.18.3-.5.38-.78.22-2.15-1.3-4.85-1.6-8.03-.87a.56.56 0 0 1-.66-.42.56.56 0 0 1 .42-.66c3.48-.8 6.47-.45 8.83 1 .3.15.38.54.22.73m1.18-2.68c-.24.36-.66.48-1 .24-2.46-1.52-6.2-1.96-9.11-1.07-.36.1-.76-.08-.87-.44-.1-.36.1-.76.45-.87 3.32-1.02 7.45-.52 10.27 1.22.35.2.46.65.24 1m.1-2.78c-2.95-1.76-7.8-1.92-10.62-1.06-.44.14-.92-.1-1.06-.55-.14-.45.1-.92.55-1.07 3.24-.98 8.62-.79 12.02 1.24.4.24.55.76.3 1.16-.24.4-.75.54-1.15.3z"/></svg>,
  twitch:    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M11.64 5.93h1.43v4.28h-1.43m3.93-4.28H17v4.28h-1.43M7 2 3.43 5.57v12.86h4.28V22l3.58-3.57h2.85L20.57 12V2m-1.43 9.29-2.85 2.85h-2.86l-2.5 2.5v-2.5H7.71V3.43h11.43z"/></svg>,
  other:     <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10.59 13.41c.41.39.41 1.03 0 1.42-.39.39-1.03.39-1.42 0a5.003 5.003 0 0 1 0-7.07l3.54-3.54a5.003 5.003 0 0 1 7.07 0 5.003 5.003 0 0 1 0 7.07l-1.49 1.49c.01-.36-.04-.72-.11-1.05l.79-.8a3.003 3.003 0 0 0 0-4.24 3.003 3.003 0 0 0-4.24 0l-3.53 3.53a3.003 3.003 0 0 0 0 4.24m2.82-4.24c.39-.39 1.03-.39 1.42 0a5.003 5.003 0 0 1 0 7.07l-3.54 3.54a5.003 5.003 0 0 1-7.07 0 5.003 5.003 0 0 1 0-7.07l1.49-1.49c-.01.36.04.72.11 1.05l-.79.8a3.003 3.003 0 0 0 0 4.24 3.003 3.003 0 0 0 4.24 0l3.53-3.53a3.003 3.003 0 0 0 0-4.24.974.974 0 0 1 0-1.42z"/></svg>,
};

const PLATFORM_LABELS = {
  instagram: 'Instagram', twitter: 'X', tiktok: 'TikTok', youtube: 'YouTube',
  facebook: 'Facebook', linkedin: 'LinkedIn', pinterest: 'Pinterest',
  spotify: 'Spotify', twitch: 'Twitch', other: 'Website',
};

const Rooms = () => {
  const normalizeCommentsResponse = (response) => {
    if (Array.isArray(response)) return response;
    if (Array.isArray(response?.comments)) return response.comments;
    if (Array.isArray(response?.data)) return response.data;
    if (Array.isArray(response?.data?.comments)) return response.data.comments;
    return [];
  };

  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [roomDetails, setRoomDetails] = useState(null);
  const [roomPosts, setRoomPosts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userRooms, setUserRooms] = useState(new Set());
  const [showPostForm, setShowPostForm] = useState(false);
  const [postFormData, setPostFormData] = useState({ title: '', category: 'cinema', image: '' });
  const [postLoading, setPostLoading] = useState(false);
  const [openCommentsByPost, setOpenCommentsByPost] = useState({});
  const [commentsByPost, setCommentsByPost] = useState({});
  const [commentInputs, setCommentInputs] = useState({});
  const [commentLoadingByPost, setCommentLoadingByPost] = useState({});

  const [profilePopup, setProfilePopup] = useState({ show: false, user: null, loading: false });

  useEffect(() => {
    const fetchRooms = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getAestheticRooms({ limit: 50, offset: 0 });
        const roomsData = response.data || response || [];
        setRooms(roomsData);
        const joined = new Set();
        roomsData.forEach((room) => {
          if (room.joined === true) {
            joined.add(room.id);
          }
        });
        setUserRooms(joined);
      } catch (err) {
        setError('Failed to fetch rooms');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRooms();
  }, []);

  useEffect(() => {
    if (!selectedRoom) return;

    const fetchRoomData = async () => {
      try {
        setLoading(true);
        const [details, posts] = await Promise.all([
          getRoomById(selectedRoom),
          getRoomPosts(selectedRoom, { limit: 20, offset: 0 }),
        ]);
        const detailsData = details.data || details || {};
        const postsData = Array.isArray(posts) ? posts : (posts.data || posts || []);
        
        setRoomDetails(detailsData);
        
        const postsWithLikeStatus = postsData.map((post) => ({
          ...post,
          isLiked: post.liked === true,
        }));
        setRoomPosts(postsWithLikeStatus);
        
        if (detailsData.joined === true) {
          setUserRooms((prev) => new Set([...prev, selectedRoom]));
        } else if (detailsData.joined === false) {
          setUserRooms((prev) => {
            const updated = new Set(prev);
            updated.delete(selectedRoom);
            return updated;
          });
        }
      } catch (err) {
        setError('Failed to fetch room details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRoomData();
  }, [selectedRoom]);

  const filteredRooms = rooms.filter((room) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      room.name?.toLowerCase().includes(searchLower) ||
      room.hashtag?.toLowerCase().includes(searchLower) ||
      room.description?.toLowerCase().includes(searchLower)
    );
  });

  const handleJoinRoom = async (roomId) => {
    try {
      await joinRoom(roomId);
      setUserRooms((prev) => new Set([...prev, roomId]));
    } catch (err) {
      setError('Failed to join room');
      console.error(err);
    }
  };

  const handleLeaveRoom = async (roomId) => {
    try {
      await leaveRoom(roomId);
      setUserRooms((prev) => {
        const updated = new Set(prev);
        updated.delete(roomId);
        return updated;
      });
    } catch (err) {
      setError('Failed to leave room');
      console.error(err);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!postFormData.title.trim()) return;

    try {
      setPostLoading(true);
      await createRoomPost(selectedRoom, {
        title: postFormData.title,
        category: postFormData.category,
        image: postFormData.image.trim(),
      });
      setPostFormData({ title: '', category: 'cinema', image: '' });
      setShowPostForm(false);
      const posts = await getRoomPosts(selectedRoom, { limit: 20, offset: 0 });
      const postsData = Array.isArray(posts) ? posts : (posts.data || posts || []);
      const postsWithLikeStatus = postsData.map((post) => ({
        ...post,
        isLiked: post.liked === true,
      }));
      setRoomPosts(postsWithLikeStatus);
    } catch (err) {
      setError('Failed to create post');
      console.error(err);
    } finally {
      setPostLoading(false);
    }
  };

  const handleToggleLikePost = async (post) => {
    if (!post?.id) return;

    const wasLiked = Boolean(post.isLiked);
    const previousLikes = Number(post.likes || 0);

    setRoomPosts((prev) =>
      prev.map((item) => {
        if (item.id !== post.id) return item;
        return {
          ...item,
          isLiked: !wasLiked,
          likes: Math.max(0, previousLikes + (wasLiked ? -1 : 1)),
        };
      })
    );

    try {
      if (wasLiked) {
        await unlikePost(post.id);
      } else {
        await likePost(post.id);
      }
    } catch (err) {
      setError('Failed to update like');
      setRoomPosts((prev) =>
        prev.map((item) => {
          if (item.id !== post.id) return item;
          return {
            ...item,
            isLiked: wasLiked,
            likes: previousLikes,
          };
        })
      );
      console.error(err);
    }
  };

  const handleToggleComments = async (postId) => {
    const isOpen = Boolean(openCommentsByPost[postId]);

    setOpenCommentsByPost((prev) => ({
      ...prev,
      [postId]: !isOpen,
    }));

    if (isOpen || commentsByPost[postId]) return;

    try {
      setCommentLoadingByPost((prev) => ({ ...prev, [postId]: true }));
      const response = await getPostComments(postId, { limit: 50 });
      const normalizedComments = normalizeCommentsResponse(response);
      setCommentsByPost((prev) => ({
        ...prev,
        [postId]: normalizedComments,
      }));
    } catch (err) {
      setError('Failed to load comments');
      console.error(err);
    } finally {
      setCommentLoadingByPost((prev) => ({ ...prev, [postId]: false }));
    }
  };

  const handleAddComment = async (event, postId) => {
    event.preventDefault();
    const text = (commentInputs[postId] || '').trim();
    if (!text) return;

    try {
      setCommentLoadingByPost((prev) => ({ ...prev, [postId]: true }));
      await addComment(postId, { text });

      const response = await getPostComments(postId, { limit: 50 });
      const updatedComments = normalizeCommentsResponse(response);

      setCommentsByPost((prev) => ({
        ...prev,
        [postId]: updatedComments,
      }));

      setCommentInputs((prev) => ({
        ...prev,
        [postId]: '',
      }));

      setRoomPosts((prev) =>
        prev.map((item) => {
          if (item.id !== postId) return item;
          return {
            ...item,
            comments: updatedComments.length,
          };
        })
      );
    } catch (err) {
      setError('Failed to add comment');
      console.error(err);
    } finally {
      setCommentLoadingByPost((prev) => ({ ...prev, [postId]: false }));
    }
  };

  const handleUsernameClick = async (post) => {
    const userId = post.userId || post.user_id;
    if (!userId) return;
    setProfilePopup({ show: true, user: null, loading: true });
    try {
      const userData = await getUserById(userId);
      setProfilePopup({ show: true, user: userData, loading: false });
    } catch (err) {
      console.error('Failed to load user profile:', err);
      setProfilePopup({ show: false, user: null, loading: false });
      setError('Failed to load user profile');
    }
  };

  if (selectedRoom) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rooms-detail-container"
      >
        {/* Back Button */}
        <div className="rooms-header">
          <button
            className="rooms-back-btn"
            onClick={() => {
              setSelectedRoom(null);
              setRoomDetails(null);
              setRoomPosts([]);
            }}
          >
            <ChevronRight size={24} style={{ transform: 'rotate(180deg)' }} />
            Back to Rooms
          </button>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rooms-error"
          >
            <AlertCircle size={18} />
            {error}
            <button onClick={() => setError(null)}>
              <X size={18} />
            </button>
          </motion.div>
        )}

        {loading ? (
          <div className="rooms-loading">
            <Loader2 className="rooms-spinner" />
            <p>Loading room details...</p>
          </div>
        ) : roomDetails ? (
          <>
            {/* Room Header */}
            <motion.div className="room-detail-header" style={{ background: roomDetails.coverGradient || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <div className="room-detail-header-content">
                <h1>{roomDetails.name}</h1>
                <p className="room-hashtag">{roomDetails.hashtag}</p>
                {roomDetails.description && (
                  <p className="room-description">{roomDetails.description}</p>
                )}
                <div className="room-stats">
                  <div className="room-stat">
                    <Users size={18} />
                    <span>{roomDetails.memberCount || 0} members</span>
                  </div>
                  <div className="room-stat">
                    <MessageSquare size={18} />
                    <span>{roomDetails.postCount || 0} posts</span>
                  </div>
                  {roomDetails.trending && (
                    <div className="room-stat trending">
                      <Flame size={18} />
                      <span>Trending</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Join/Leave Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`room-action-btn ${userRooms.has(selectedRoom) ? 'leave' : 'join'}`}
                onClick={() => {
                  if (userRooms.has(selectedRoom)) {
                    handleLeaveRoom(selectedRoom);
                  } else {
                    handleJoinRoom(selectedRoom);
                  }
                }}
              >
                {userRooms.has(selectedRoom) ? (
                  <>
                    <LogOut size={18} />
                    Leave Room
                  </>
                ) : (
                  <>
                    <LogIn size={18} />
                    Join Room
                  </>
                )}
              </motion.button>
            </motion.div>

            {/* Posts Section */}
            <motion.div
              className="room-posts-section"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <div className="posts-header">
                <h2>Posts in this room</h2>
                {userRooms.has(selectedRoom) && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="create-post-btn"
                    onClick={() => setShowPostForm(!showPostForm)}
                  >
                    <Plus size={18} />
                    New Post
                  </motion.button>
                )}
              </div>

              {/* Create Post Form */}
              <AnimatePresence>
                {showPostForm && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="create-post-form"
                  >
                    <form onSubmit={handleCreatePost}>
                      <div className="form-group">
                        <label htmlFor="title">Post Title</label>
                        <input
                          id="title"
                          type="text"
                          placeholder="Share what's on your mind..."
                          value={postFormData.title}
                          onChange={(e) =>
                            setPostFormData({ ...postFormData, title: e.target.value })
                          }
                          disabled={postLoading}
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="category">Category</label>
                        <select
                          id="category"
                          value={postFormData.category}
                          onChange={(e) =>
                            setPostFormData({ ...postFormData, category: e.target.value })
                          }
                          disabled={postLoading}
                        >
                          <option value="cinema">Cinema</option>
                          <option value="music">Music</option>
                          <option value="games">Games</option>
                          <option value="books">Books</option>
                          <option value="travel">Travel</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label htmlFor="image">Image URL</label>
                        <input
                          id="image"
                          type="url"
                          placeholder="https://example.com/your-image.jpg"
                          value={postFormData.image}
                          onChange={(e) =>
                            setPostFormData({ ...postFormData, image: e.target.value })
                          }
                          disabled={postLoading}
                        />
                      </div>
                      <div className="form-actions">
                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          type="submit"
                          className="submit-btn"
                          disabled={postLoading}
                        >
                          {postLoading ? (
                            <>
                              <Loader2 size={16} className="spinner" />
                              Posting...
                            </>
                          ) : (
                            'Post'
                          )}
                        </motion.button>
                        <button
                          type="button"
                          className="cancel-btn"
                          onClick={() => setShowPostForm(false)}
                          disabled={postLoading}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Posts List */}
              {roomPosts.length > 0 ? (
                <div className="posts-list">
                  {roomPosts.map((post, idx) => (
                    <motion.div
                      key={post.id || idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="post-card"
                    >
                      {post.image && (
                        <img src={post.image} alt={post.title} className="post-image" />
                      )}
                      <div className="post-content">
                        <h4>{post.title}</h4>
                        {post.username && (
                          <p
                            className="post-author post-author--clickable"
                            onClick={() => handleUsernameClick(post)}
                            role="button"
                            tabIndex={0}
                          >
                            by {post.username}
                          </p>
                        )}
                        {post.timestamp && (
                          <p className="post-time">
                            {new Date(post.timestamp).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      <div className="post-actions">
                        <button
                          className={`post-action-btn ${post.isLiked ? 'liked' : ''}`}
                          onClick={() => handleToggleLikePost(post)}
                          disabled={!post.id}
                        >
                          <Heart size={16} fill={post.isLiked ? 'currentColor' : 'none'} />
                          {post.likes || 0}
                        </button>
                        <button
                          className="post-action-btn"
                          onClick={() => post.id && handleToggleComments(post.id)}
                          disabled={!post.id}
                        >
                          <MessageSquare size={16} />
                          {post.comments || 0}
                        </button>
                      </div>

                      {post.id && openCommentsByPost[post.id] && (
                        <div className="post-comments-panel">
                          {commentLoadingByPost[post.id] ? (
                            <p className="post-comments-loading">Loading comments...</p>
                          ) : (
                            <>
                              <div className="post-comments-list">
                                {(commentsByPost[post.id] || []).length > 0 ? (
                                  (commentsByPost[post.id] || []).map((comment, commentIndex) => (
                                    <div key={comment.id || commentIndex} className="post-comment-item">
                                      <p 
                                        className="post-comment-author post-comment-author--clickable"
                                        onClick={() => {
                                          const userId = comment.userId || comment.user_id;
                                          if (userId) {
                                            handleUsernameClick({ userId });
                                          }
                                        }}
                                        role="button"
                                        tabIndex={0}
                                      >
                                        {comment.username || 'User'}
                                      </p>
                                      <p className="post-comment-text">{comment.text}</p>
                                    </div>
                                  ))
                                ) : (
                                  <p className="post-comments-empty">No comments yet.</p>
                                )}
                              </div>

                              <form
                                className="post-comment-form"
                                onSubmit={(event) => handleAddComment(event, post.id)}
                              >
                                <input
                                  type="text"
                                  placeholder="Write a comment..."
                                  value={commentInputs[post.id] || ''}
                                  onChange={(event) =>
                                    setCommentInputs((prev) => ({
                                      ...prev,
                                      [post.id]: event.target.value,
                                    }))
                                  }
                                  disabled={Boolean(commentLoadingByPost[post.id])}
                                />
                                <button
                                  type="submit"
                                  disabled={Boolean(commentLoadingByPost[post.id])}
                                >
                                  Comment
                                </button>
                              </form>
                            </>
                          )}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="no-posts">
                  <MessageSquare size={48} />
                  <p>No posts yet. Be the first to share!</p>
                </div>
              )}
            </motion.div>
          </>
        ) : null}

        {/* Profile Popup */}
        <AnimatePresence>
          {profilePopup.show && (
            <div
              className="rooms-profile-overlay"
              onClick={() => setProfilePopup({ show: false, user: null, loading: false })}
            >
              <motion.div
                className="rooms-profile-popup"
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  className="rooms-profile-close"
                  onClick={() => setProfilePopup({ show: false, user: null, loading: false })}
                >
                  <X size={20} />
                </button>
                {profilePopup.loading ? (
                  <div className="rooms-profile-loading">
                    <Loader2 className="rooms-spinner" />
                    <p>Loading profile...</p>
                  </div>
                ) : profilePopup.user ? (
                  <div className="rooms-profile-body">
                    {profilePopup.user.avatar && (
                      <img
                        src={profilePopup.user.avatar}
                        alt={profilePopup.user.username}
                        className="rooms-profile-avatar"
                      />
                    )}
                    <h3>{profilePopup.user.username}</h3>
                    {profilePopup.user.bio && <p className="rooms-profile-bio">{profilePopup.user.bio}</p>}
                    {profilePopup.user.socialMediaLinks?.length > 0 && (
                      <div className="rooms-profile-socials">
                        {profilePopup.user.socialMediaLinks.map((link, i) => {
                            const platform = (link.platform || 'other').toLowerCase();
                            return (
                              <a
                                key={i}
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={`rooms-profile-social-link rooms-profile-social-link--${platform}`}
                                title={PLATFORM_LABELS[platform] || link.platform}
                              >
                                {PLATFORM_ICONS[platform] || PLATFORM_ICONS.other}
                              </a>
                            );
                          })}
                      </div>
                    )}
                  </div>
                ) : null}
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="rooms-container"
    >
      <div className="rooms-hero">
        <h1>Aesthetic Rooms</h1>
        <p>Join communities of like-minded curators</p>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rooms-error"
        >
          <AlertCircle size={18} />
          {error}
          <button onClick={() => setError(null)}>
            <X size={18} />
          </button>
        </motion.div>
      )}

      <div className="rooms-search-section">
        <div className="rooms-search">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            placeholder="Search rooms by name, hashtag, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="rooms-loading">
          <Loader2 className="rooms-spinner" />
          <p>Loading rooms...</p>
        </div>
      ) : filteredRooms.length > 0 ? (
        <motion.div
          className="rooms-grid"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ staggerChildren: 0.05 }}
        >
          {filteredRooms.map((room, idx) => (
            <motion.div
              key={room.id || idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ y: -8 }}
              transition={{ delay: idx * 0.02 }}
              className="room-card"
              onClick={() => setSelectedRoom(room.id)}
            >
              <div
                className="room-card-banner"
                style={{
                  background: room.coverGradient || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                {room.trending && (
                  <div className="trending-badge">
                    <Flame size={14} />
                    Trending
                  </div>
                )}
              </div>

              <div className="room-card-content">
                <h3>{room.name}</h3>
                <p className="room-hashtag-card">{room.hashtag}</p>
                {room.description && (
                  <p className="room-description-card">{room.description}</p>
                )}

                <div className="room-info">
                  <div className="room-info-item">
                    <Users size={16} />
                    <span>{room.memberCount || 0}</span>
                  </div>
                  <div className="room-info-item">
                    <MessageSquare size={16} />
                    <span>{room.postCount || 0}</span>
                  </div>
                </div>

                <div className="room-card-footer">
                  {userRooms.has(room.id) ? (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="room-btn leave-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleLeaveRoom(room.id);
                      }}
                    >
                      <LogOut size={16} />
                      Leave
                    </motion.button>
                  ) : (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="room-btn join-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleJoinRoom(room.id);
                      }}
                    >
                      <LogIn size={16} />
                      Join
                    </motion.button>
                  )}
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="room-btn view-btn"
                  >
                    View
                    <ChevronRight size={16} />
                  </motion.button>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <div className="no-results">
          <Search size={48} />
          <p>No rooms found matching "{searchQuery}"</p>
          <button
            className="clear-search-btn"
            onClick={() => setSearchQuery('')}
          >
            Clear Search
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default Rooms;
