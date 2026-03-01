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
} from '../services/api';
import './Rooms.css';

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

  // Fetch rooms list
  useEffect(() => {
    const fetchRooms = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getAestheticRooms({ limit: 50, offset: 0 });
        const roomsData = response.data || response || [];
        setRooms(roomsData);
        // Extract joined status from backend response for authenticated users
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

  // Fetch room details when selected
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
        
        // Map liked flag from backend to isLiked for consistent frontend state
        const postsWithLikeStatus = postsData.map((post) => ({
          ...post,
          isLiked: post.liked === true,
        }));
        setRoomPosts(postsWithLikeStatus);
        
        // Update userRooms based on room's joined status
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

  // Filter rooms by search query
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
      // Refresh room posts
      const posts = await getRoomPosts(selectedRoom, { limit: 20, offset: 0 });
      const postsData = Array.isArray(posts) ? posts : (posts.data || posts || []);
      // Map liked flag from backend to isLiked
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
                          <p className="post-author">by {post.username}</p>
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
                                      <p className="post-comment-author">{comment.username || 'User'}</p>
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
