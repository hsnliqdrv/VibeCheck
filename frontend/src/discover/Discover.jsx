import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search, SlidersHorizontal, Sparkles, Zap, Star,
    MessageCircle, UserPlus, Heart,
    Users, Activity, Fingerprint, Loader2,
    ChevronDown, ChevronUp, X, CheckCircle2, MessageSquare
} from 'lucide-react';
import { getAuraMatches } from '../services/api';
import './Discover.css';

const containerVariants = {
    initial: { opacity: 0 },
    animate: {
        opacity: 1,
        transition: {
            staggerChildren: 0.08,
            delayChildren: 0.1
        }
    }
};

const itemVariants = {
    initial: { y: 15, opacity: 0 },
    animate: {
        y: 0,
        opacity: 1,
        transition: { type: 'spring', stiffness: 300, damping: 24 }
    }
};

const getMatchType = (score) => {
    if (score >= 90) return 'Perfect';
    if (score >= 75) return 'Great';
    return 'Good';
};

const MatchCard = React.memo(({ match, itemVariants, onConnect, onLike, onChat }) => {
    const user = match.user || match;
    const matchType = getMatchType(match.similarityScore);
    const id = user.username || match.id || user.id;
    const [isFloating, setIsFloating] = useState(false);

    const handleConnectClick = () => {
        if (!match.isConnected) {
            setIsFloating(true);
            setTimeout(() => setIsFloating(false), 600);
        }
        onConnect(id);
    };

    const handleLikeClick = () => {
        onLike(id);
    };

    return (
        <motion.div
            layout
            variants={itemVariants}
            initial="initial"
            animate="animate"
            whileHover={{ y: -8, transition: { duration: 0.2 } }}
            whileTap={{ scale: 0.98 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            className="ds-card"
        >
            <div className={`ds-card-banner ds-card-banner--${matchType.toLowerCase()}`}>
                <div className="ds-match-badge">
                    {match.similarityScore}% <span>{matchType}</span>
                </div>
                {matchType === 'Perfect' && <Sparkles size={20} className="ds-banner-icon ds-banner-icon--sparkle" />}
                {matchType === 'Great' && <Zap size={20} className="ds-banner-icon ds-banner-icon--zap" />}
                {matchType === 'Good' && <Star size={20} className="ds-banner-icon ds-banner-icon--star" />}
            </div>

            <div className="ds-card-body">
                <div className="ds-user">
                    <div className="ds-avatar-wrap">
                        <img src={user.avatar} alt={user.username} className="ds-avatar" />
                        <div className="ds-online-indicator" />
                    </div>
                    <div className="ds-user-text">
                        <h3 className="ds-username">{user.username}</h3>
                        <p className="ds-tagline">{user.bio}</p>
                    </div>
                </div>

                <div className="ds-reason">
                    <div className="ds-reason-head">
                        <Sparkles size={12} />
                        <span>Why you match:</span>
                    </div>
                    <p className="ds-reason-text">{match.matchReason}</p>
                </div>

                <div className="ds-section">
                    <label>AESTHETIC MARKERS</label>
                    <div className="ds-tags">
                        {user.aestheticTags?.map(tag => (
                            <span key={tag} className="ds-tag">{tag}</span>
                        ))}
                    </div>
                </div>

                <div className="ds-section">
                    <label>VIBE SIGNATURE</label>
                    <div className="ds-aura">
                        {user.auraColors?.map((color, i) => (
                            <div
                                key={i}
                                className="ds-aura-dot"
                                style={{ backgroundColor: color }}
                                title={color}
                            />
                        ))}
                    </div>
                </div>

                <div className="ds-section">
                    <label>RECENT CURATIONS</label>
                    <div className="ds-vibes">
                        {user.recentShares?.slice(0, 5).map((share, i) => (
                            <div key={share.id || i} className="ds-vibe">
                                <img src={share.image} alt={share.title || 'Vibe'} />
                            </div>
                        ))}
                    </div>
                </div>

                <div className="ds-actions" style={{ position: 'relative' }}>
                    <AnimatePresence>
                        {isFloating && (
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.8 }}
                                animate={{ opacity: 1, y: -40, scale: 1.1 }}
                                exit={{ opacity: 0, y: -60, scale: 0.9 }}
                                transition={{ duration: 0.5, ease: "easeOut" }}
                                style={{
                                    position: 'absolute',
                                    top: -10,
                                    left: '20%',
                                    transform: 'translateX(-50%)',
                                    color: '#b44aff',
                                    fontWeight: '800',
                                    fontSize: '1rem',
                                    pointerEvents: 'none',
                                    textShadow: '0 2px 10px rgba(255,255,255,0.8)',
                                    zIndex: 10
                                }}
                            >
                                + Connected
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <button
                        className={`ds-btn ${match.isConnected ? 'ds-btn--secondary' : 'ds-btn--primary'}`}
                        onClick={handleConnectClick}
                    >
                        {match.isConnected ? <Users size={16} /> : <UserPlus size={16} />}
                        <span>{match.isConnected ? 'Connected' : 'Connect'}</span>
                    </button>
                    <button
                        className="ds-btn ds-btn--secondary"
                        onClick={() => onChat(user)}
                    >
                        <MessageCircle size={16} />
                    </button>
                    <button
                        className={`ds-icon-btn ${match.isLiked ? 'ds-liked' : ''}`}
                        onClick={handleLikeClick}
                    >
                        <Heart
                            size={18}
                            fill={match.isLiked ? "#ec4899" : "none"}
                            color={match.isLiked ? "#ec4899" : "currentColor"}
                        />
                    </button>
                </div>
            </div>
        </motion.div>
    );
});

const DiscoverPage = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('All');
    const [matches, setMatches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showFilters, setShowFilters] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState('All');

    useEffect(() => {
        const fetchMatches = async () => {
            try {
                setLoading(true);
                const response = await getAuraMatches();
                setMatches(response.data || []);
            } catch (err) {
                console.error('Failed to fetch matches:', err);
                setError('Could not load matches. Please try again later.');
            } finally {
                setLoading(false);
            }
        };

        fetchMatches();
    }, []);

    const categories = useMemo(() => {
        const cats = new Set();
        matches.forEach(m => {
            const user = m.user || m;
            (user.topCategories || []).forEach(c => cats.add(c.category));
        });
        return ['All', ...Array.from(cats)].sort();
    }, [matches]);

    const filteredMatches = useMemo(() => {
        return matches.filter(match => {
            const user = match.user || match;
            const usernameMatch = !searchQuery || user.username?.toLowerCase().includes(searchQuery.toLowerCase());
            const aestheticMatch = !searchQuery || user.aestheticTags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
            const matchesSearch = usernameMatch || aestheticMatch;

            const type = getMatchType(match.similarityScore);
            const matchesTab = activeTab === 'All' || activeTab === type;

            const userCats = (user.topCategories || []).map(c => c.category);
            const matchesCategory = selectedCategory === 'All' || userCats.includes(selectedCategory);

            return matchesSearch && matchesTab && matchesCategory;
        });
    }, [searchQuery, activeTab, selectedCategory, matches]);

    const avgCompatibility = useMemo(() => {
        if (filteredMatches.length === 0) return 0;
        const sum = filteredMatches.reduce((acc, m) => acc + (m.similarityScore || 0), 0);
        return Math.round(sum / filteredMatches.length);
    }, [filteredMatches]);

    const sharedAesthetics = useMemo(() => {
        const allTags = new Set();
        filteredMatches.forEach(m => {
            const user = m.user || m;
            (user.aestheticTags || []).forEach(tag => allTags.add(tag));
        });
        return allTags.size;
    }, [filteredMatches]);


    const [modalConfig, setModalConfig] = useState({ show: false, type: '', user: null });

    const handleConnect = React.useCallback((id) => {
        setMatches(current => current.map(m =>
            (m.id === id || m.user?.username === id) ? { ...m, isConnected: !m.isConnected } : m
        ));
    }, []);

    const handleLike = React.useCallback((id) => {
        setMatches(current => current.map(m =>
            (m.id === id || m.user?.username === id) ? { ...m, isLiked: !m.isLiked } : m
        ));
    }, []);

    const handleChat = React.useCallback((user) => {
        setModalConfig({ show: true, type: 'chat', user });
    }, []);

    const handleExploreMore = React.useCallback(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, []);

    if (error) {
        return (
            <div className="ds-error-state">
                <Activity size={40} />
                <h3>{error}</h3>
                <button onClick={() => window.location.reload()} className="ds-btn ds-btn--primary">
                    Retry
                </button>
            </div>
        );
    }

    return (
        <motion.div
            className="ds-page"
            initial="initial"
            animate="animate"
            variants={containerVariants}
        >
            <header className="ds-header">
                <motion.div variants={itemVariants} className="ds-title-block">
                    <div className="ds-eyebrow">
                        <Sparkles size={14} strokeWidth={2.5} />
                        <span>Smart Match Discovery</span>
                    </div>
                    <h1 className="ds-title">Discover Your Vibe Tribe</h1>
                    <p className="ds-subtitle">Connect with creators sharing your aesthetic DNA</p>
                </motion.div>

                <div className="ds-filter-wrapper">
                    <motion.button
                        variants={itemVariants}
                        className={`ds-filter-toggle ${showFilters ? 'ds-filter-toggle--active' : ''}`}
                        onClick={() => setShowFilters(!showFilters)}
                    >
                        <SlidersHorizontal size={16} />
                        <span className="ds-filter-btn-text">
                            {selectedCategory === 'All' ? 'Interests' : selectedCategory}
                        </span>
                        {showFilters ? (
                            <ChevronUp size={14} strokeWidth={2.5} />
                        ) : (
                            <ChevronDown size={14} strokeWidth={2.5} />
                        )}
                    </motion.button>

                    <AnimatePresence>
                        {showFilters && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.92, y: -8 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.92, y: -8 }}
                                transition={{ type: 'spring', stiffness: 320, damping: 26 }}
                                className="ds-filter-dropdown"
                            >
                                <div className="ds-dropdown-group">
                                    <div className="ds-dropdown-header">Filter by Passion</div>
                                    <div className="ds-dropdown-list">
                                        {categories.map(cat => (
                                            <button
                                                key={cat}
                                                className={`ds-dropdown-item ${selectedCategory === cat ? 'ds-dropdown-item--active' : ''}`}
                                                onClick={() => {
                                                    setSelectedCategory(cat);
                                                    setShowFilters(false);
                                                }}
                                            >
                                                {cat === 'All' ? 'All Interests' : cat}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </header>

            <motion.div variants={itemVariants} className="ds-controls">
                <div className="ds-search">
                    <Search size={20} className="ds-search-icon" />
                    <input
                        type="text"
                        placeholder="Search by username or aesthetic..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="ds-tabs-container">
                    <div className="ds-tabs">
                        {['All', 'Perfect', 'Great', 'Good'].map((tab) => (
                            <button
                                key={tab}
                                className={`ds-tab ${activeTab === tab ? 'ds-tab--active' : ''}`}
                                onClick={() => setActiveTab(tab)}
                            >
                                {tab === 'All' ? 'All' : tab}
                                <span className="ds-tab-badge">
                                    {tab === 'All' ? matches.length : matches.filter(m => getMatchType(m.similarityScore) === tab).length}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            </motion.div>

            <div className="ds-stats">
                <motion.div variants={itemVariants} className="ds-stat">
                    <div className="ds-stat-icon ds-stat-icon--blue">
                        <Users size={20} />
                    </div>
                    <div className="ds-stat-info">
                        <span className="ds-stat-val">{loading ? '--' : filteredMatches.length}</span>
                        <span className="ds-stat-label">Total Matches</span>
                    </div>
                </motion.div>

                <motion.div variants={itemVariants} className="ds-stat">
                    <div className="ds-stat-icon ds-stat-icon--purple">
                        <Activity size={20} />
                    </div>
                    <div className="ds-stat-info">
                        <span className="ds-stat-val">{loading ? '--' : `${avgCompatibility}%`}</span>
                        <span className="ds-stat-label">Avg Compatibility</span>
                    </div>
                </motion.div>

                <motion.div variants={itemVariants} className="ds-stat">
                    <div className="ds-stat-icon ds-stat-icon--amber">
                        <Fingerprint size={20} />
                    </div>
                    <div className="ds-stat-info">
                        <span className="ds-stat-val">{loading ? '--' : sharedAesthetics}</span>
                        <span className="ds-stat-label">Shared Aesthetics</span>
                    </div>
                </motion.div>
            </div>

            <div className="ds-grid">
                {loading ? (
                    <div className="ds-grid-loading">
                        <Loader2 size={32} className="ds-spinner" />
                        <p>Finding your tribe...</p>
                    </div>
                ) : (
                    <AnimatePresence mode='popLayout'>
                        {filteredMatches.map((match, idx) => {
                            const user = match.user || match;
                            const id = user.username || idx;

                            return (
                                <MatchCard
                                    key={id}
                                    match={match}
                                    itemVariants={itemVariants}
                                    onConnect={handleConnect}
                                    onLike={handleLike}
                                    onChat={handleChat}
                                />
                            );
                        })}
                    </AnimatePresence>
                )}
            </div>

            <motion.footer variants={itemVariants} className="ds-footer">
                <button className="ds-load-btn" onClick={handleExploreMore}>
                    Explore More
                </button>
            </motion.footer>

            <AnimatePresence>
                {modalConfig.show && (
                    <div className="ds-modal-overlay">
                        <motion.div
                            className="ds-modal-content"
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        >
                            <button className="ds-modal-close" onClick={() => setModalConfig({ ...modalConfig, show: false })}>
                                <X size={20} />
                            </button>

                            <div className="ds-modal-icon">
                                {modalConfig.type === 'connect' && <UserPlus size={40} className="ds-icon-purple" />}
                                {modalConfig.type === 'like' && <Heart size={40} fill="#ec4899" color="#ec4899" />}
                                {modalConfig.type === 'chat' && <MessageSquare size={40} className="ds-icon-blue" />}
                                {modalConfig.type === 'explore' && <Sparkles size={40} className="ds-icon-amber" />}
                            </div>

                            <div className="ds-modal-body">
                                <h2>
                                    {modalConfig.type === 'connect' && "Connection Request Sent!"}
                                    {modalConfig.type === 'like' && "Aesthetic Liked!"}
                                    {modalConfig.type === 'chat' && `Chat with ${modalConfig.user?.username}`}
                                    {modalConfig.type === 'explore' && "Fetching More Vibes..."}
                                </h2>
                                <p>
                                    {modalConfig.type === 'connect' && `We've sent your vibe signature to ${modalConfig.user?.username}. We'll notify you when they connect back!`}
                                    {modalConfig.type === 'like' && `You've expressed interest in ${modalConfig.user?.username}'s curated aesthetic.`}
                                    {modalConfig.type === 'chat' && `Direct message bridge is opening... Prepare to sync vibes with ${modalConfig.user?.username}.`}
                                    {modalConfig.type === 'explore' && "Expanding your search grid to find more compatible creators in the VibeCheck network."}
                                </p>
                            </div>

                            <div className="ds-modal-footer">
                                <button className="ds-btn ds-btn--primary" onClick={() => setModalConfig({ ...modalConfig, show: false })}>
                                    <CheckCircle2 size={18} />
                                    <span>Got it</span>
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default DiscoverPage;