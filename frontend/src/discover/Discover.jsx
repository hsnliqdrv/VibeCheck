import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search, SlidersHorizontal, Sparkles, Zap, Star,
    Users, Activity, Fingerprint, Loader2,
    ChevronDown, ChevronUp, X,
    ExternalLink, User
} from 'lucide-react';
import { getAuraMatches, getUserById } from '../services/api';
import { getAvatarUrl } from '../utils/avatarUrl';
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

const PLATFORM_ICONS = {
    instagram: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5M12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10m0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>
    ),
    twitter: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.835L1.254 2.25H8.08l4.253 5.622L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
    ),
    tiktok: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M16.6 5.82s.51.5 0 0A4.278 4.278 0 0 1 15.54 3h-3.09v12.4a2.592 2.592 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64 0 3.33 2.76 5.7 5.69 5.7 3.14 0 5.69-2.55 5.69-5.7V9.01a7.35 7.35 0 0 0 4.3 1.38V7.3s-1.88.09-3.24-1.48z"/></svg>
    ),
    youtube: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/></svg>
    ),
    facebook: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2.04c-5.5 0-10 4.49-10 10.02 0 5 3.66 9.15 8.44 9.9v-7H7.9v-2.9h2.54V9.85c0-2.51 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.78-1.63 1.57v1.88h2.78l-.45 2.9h-2.33v7a10 10 0 0 0 8.44-9.9c0-5.53-4.5-10.02-10.01-10.02z"/></svg>
    ),
    linkedin: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/></svg>
    ),
    pinterest: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M9.04 21.54c.96.29 1.93.46 2.96.46a10 10 0 0 0 10-10A10 10 0 0 0 12 2 10 10 0 0 0 2 12c0 4.25 2.67 7.9 6.44 9.34-.09-.78-.18-2.07 0-2.96l1.15-4.94s-.29-.58-.29-1.5c0-1.38.86-2.41 1.84-2.41.86 0 1.26.63 1.26 1.44 0 .86-.57 2.09-.86 3.27-.17.98.52 1.84 1.52 1.84 1.78 0 3.16-1.9 3.16-4.58 0-2.4-1.72-4.04-4.19-4.04-2.82 0-4.48 2.1-4.48 4.31 0 .86.28 1.73.71 2.22.06.09.09.17.06.29l-.29 1.09c0 .17-.11.23-.28.11-1.28-.56-2.02-2.38-2.02-3.85 0-3.16 2.24-6.03 6.56-6.03 3.44 0 6.12 2.47 6.12 5.75 0 3.44-2.13 6.2-5.18 6.2-.97 0-1.92-.52-2.26-1.13l-.67 2.37c-.23.86-.86 2.01-1.29 2.7z"/></svg>
    ),
    spotify: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10 10 10 0 0 0 10-10A10 10 0 0 0 12 2m4.38 14.42c-.18.3-.5.38-.78.22-2.15-1.3-4.85-1.6-8.03-.87a.56.56 0 0 1-.66-.42.56.56 0 0 1 .42-.66c3.48-.8 6.47-.45 8.83 1 .3.15.38.54.22.73m1.18-2.68c-.24.36-.66.48-1 .24-2.46-1.52-6.2-1.96-9.11-1.07-.36.1-.76-.08-.87-.44-.1-.36.1-.76.45-.87 3.32-1.02 7.45-.52 10.27 1.22.35.2.46.65.24 1m.1-2.78c-2.95-1.76-7.8-1.92-10.62-1.06-.44.14-.92-.1-1.06-.55-.14-.45.1-.92.55-1.07 3.24-.98 8.62-.79 12.02 1.24.4.24.55.76.3 1.16-.24.4-.75.54-1.15.3z"/></svg>
    ),
    twitch: (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M11.64 5.93h1.43v4.28h-1.43m3.93-4.28H17v4.28h-1.43M7 2 3.43 5.57v12.86h4.28V22l3.58-3.57h2.85L20.57 12V2m-1.43 9.29-2.85 2.85h-2.86l-2.5 2.5v-2.5H7.71V3.43h11.43z"/></svg>
    ),
};

const getPlatformIcon = (platform) => {
    const key = platform?.toLowerCase();
    return PLATFORM_ICONS[key] || <ExternalLink size={16} />;
};

const getPlatformLabel = (platform) => {
    const labels = {
        instagram: 'Instagram',
        twitter: 'X',
        tiktok: 'TikTok',
        youtube: 'YouTube',
        facebook: 'Facebook',
        linkedin: 'LinkedIn',
        pinterest: 'Pinterest',
        spotify: 'Spotify',
        twitch: 'Twitch',
        other: 'Website',
    };
    return labels[platform?.toLowerCase()] || platform || 'Link';
};

const MatchCard = React.memo(({ match, itemVariants, onOpenProfile }) => {
    const user = match.user || match;
    const matchType = getMatchType(match.similarityScore);

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
                        <img
                            src={getAvatarUrl(user.avatar, user.updatedAt)}
                            alt={user.username}
                            className="ds-avatar"
                        />
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

                {/* Social Media Links */}
                {user.socialMediaLinks && user.socialMediaLinks.length > 0 && (
                    <div className="ds-section">
                        <label>SOCIAL PROFILES</label>
                        <div className="ds-social-links">
                            {user.socialMediaLinks.map((link, i) => (
                                <a
                                    key={i}
                                    href={link.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={`ds-social-link ds-social-link--${link.platform?.toLowerCase() || 'other'}`}
                                    title={getPlatformLabel(link.platform)}
                                >
                                    {getPlatformIcon(link.platform)}
                                </a>
                            ))}
                        </div>
                    </div>
                )}

                {/* View Profile Button */}
                <div className="ds-card-actions">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="ds-profile-btn"
                        onClick={() => onOpenProfile(user.id || user.userId)}
                        title="View full profile"
                    >
                        <User size={16} />
                        View Profile
                    </motion.button>
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
    const [profilePopup, setProfilePopup] = useState({ show: false, user: null, loading: false });

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

    const handleOpenProfile = async (userId) => {
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
                                    onOpenProfile={handleOpenProfile}
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

            {/* Profile Popup */}
            <AnimatePresence>
                {profilePopup.show && (
                    <div
                        className="ds-profile-overlay"
                        onClick={() => setProfilePopup({ show: false, user: null, loading: false })}
                    >
                        <motion.div
                            className="ds-profile-popup"
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button
                                className="ds-profile-close"
                                onClick={() => setProfilePopup({ show: false, user: null, loading: false })}
                            >
                                <X size={20} />
                            </button>
                            {profilePopup.loading ? (
                                <div className="ds-profile-loading">
                                    <Loader2 className="ds-spinner" />
                                    <p>Loading profile...</p>
                                </div>
                            ) : profilePopup.user ? (
                                <div className="ds-profile-body">
                                    {profilePopup.user.avatar && (
                                        <img
                                            src={getAvatarUrl(profilePopup.user.avatar, profilePopup.user.updatedAt)}
                                            alt={profilePopup.user.username}
                                            className="ds-profile-avatar"
                                        />
                                    )}
                                    <h3>{profilePopup.user.username}</h3>
                                    {profilePopup.user.bio && <p className="ds-profile-bio">{profilePopup.user.bio}</p>}
                                    {profilePopup.user.socialMediaLinks?.length > 0 && (
                                        <div className="ds-profile-socials">
                                            {profilePopup.user.socialMediaLinks.map((link, i) => {
                                                const platform = (link.platform || 'other').toLowerCase();
                                                return (
                                                    <a
                                                        key={i}
                                                        href={link.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className={`ds-profile-social-link ds-profile-social-link--${platform}`}
                                                        title={getPlatformLabel(link.platform)}
                                                    >
                                                        {getPlatformIcon(link.platform)}
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
};

export default DiscoverPage;