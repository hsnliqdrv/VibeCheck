import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence, type Variants } from 'framer-motion';
import {
  Trophy, Star, Flame, Zap, Crown, Heart, Globe, BookOpen,
  Gamepad2, Music, Clapperboard, Plane, Lock, Award, Sparkles,
  Target, Users, Compass, Moon, ChevronDown, ChevronUp,
} from 'lucide-react';
import { getUserBadges, getAllBadges } from '../services/api';
import './Badges.css';

interface Badge {
  id?: string;
  name: string;
  description?: string;
  icon?: string;
  rarity?: string;
  category?: string;
  unlocked: boolean;
  unlockedDate?: string;
}

// Maps badge icon/category/rarity strings to a Lucide component
const ICON_MAP: Record<string, React.ElementType> = {
  trophy: Trophy, star: Star, flame: Flame, fire: Flame,
  zap: Zap, crown: Crown, heart: Heart, globe: Globe,
  book: BookOpen, bookopen: BookOpen, game: Gamepad2, gamepad: Gamepad2,
  music: Music, film: Clapperboard, cinema: Clapperboard,
  plane: Plane, travel: Plane, award: Award, sparkles: Sparkles,
  target: Target, users: Users, compass: Compass, moon: Moon,
  early: Star, completionist: Trophy, streak: Flame, social: Users, special: Sparkles,
};

function resolveLucideIcon(badge: Badge): React.ElementType {
  if (badge.icon && !badge.icon.startsWith('http')) {
    const key = badge.icon.toLowerCase().replace(/\s+/g, '');
    if (ICON_MAP[key]) return ICON_MAP[key];
  }
  if (badge.category && ICON_MAP[badge.category.toLowerCase()]) {
    return ICON_MAP[badge.category.toLowerCase()];
  }
  const r = badge.rarity?.toLowerCase();
  if (r === 'legendary') return Crown;
  if (r === 'epic') return Zap;
  if (r === 'rare') return Star;
  return Award;
}

// Explicit Variants type annotation fixes TS2322 with framer-motion v12
const pageVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
};

const itemSlideIn: Variants = {
  initial: { y: 22, opacity: 0 },
  animate: { y: 0, opacity: 1, transition: { type: 'spring', stiffness: 260, damping: 22 } },
};

const RARITY_GRADIENT: Record<string, string> = {
  legendary: 'linear-gradient(135deg, #FF9500 0%, #FF0055 100%)',
  epic:      'linear-gradient(135deg, #9C2CF3 0%, #3A47D5 100%)',
  rare:      'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
  uncommon:  'linear-gradient(135deg, #059669 0%, #0891b2 100%)',
  common:    'linear-gradient(135deg, #6b6bf8 0%, #b44aff 100%)',
};

const RARITY_SHADOW: Record<string, string> = {
  legendary: 'rgba(255,149,0,0.35)',
  epic:      'rgba(156,44,243,0.35)',
  rare:      'rgba(37,99,235,0.35)',
  uncommon:  'rgba(5,150,105,0.35)',
  common:    'rgba(107,107,248,0.3)',
};

const VIEW_FILTERS = ['all', 'unlocked', 'locked'] as const;
const CATEGORY_FILTERS = ['all', 'early', 'completionist', 'streak', 'social', 'special'] as const;

const BadgesPage: React.FC = () => {
  const [badges, setBadges]                 = useState<Badge[]>([]);
  const [viewFilter, setViewFilter]         = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [isMenuOpen, setIsMenuOpen]         = useState<boolean>(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getUserBadges();
        const list: Badge[] = Array.isArray(res) ? res : (res?.badges ?? []);
        if (list.length > 0) {
          setBadges(list);
        } else {
          const all = await getAllBadges();
          setBadges(Array.isArray(all) ? all : []);
        }
      } catch (err) {
        console.error('Failed to load badges:', err);
      }
    };
    load();
  }, []);

  const filtered = badges.filter(b => {
    const matchView = viewFilter === 'all' || (viewFilter === 'unlocked' ? b.unlocked : !b.unlocked);
    const matchCat  = categoryFilter === 'all' || b.category?.toLowerCase() === categoryFilter;
    return matchView && matchCat;
  });

  const unlockedCount = badges.filter(b => b.unlocked).length;
  const progress = badges.length > 0 ? Math.round((unlockedCount / badges.length) * 100) : 0;

  const categoryLabel = categoryFilter === 'all'
    ? 'All Categories'
    : categoryFilter.charAt(0).toUpperCase() + categoryFilter.slice(1);

  return (
    <motion.div className="bg-page" variants={pageVariants} initial="initial" animate="animate">

      <header className="bg-header">
        <div className="bg-title-block">
          <motion.span variants={itemSlideIn} className="bg-eyebrow">Discovery</motion.span>
          <motion.h1 variants={itemSlideIn} className="bg-title">Badge Collection</motion.h1>
          <motion.p variants={itemSlideIn} className="bg-subtitle">
            {unlockedCount} of {badges.length} badges unlocked
          </motion.p>
        </div>

        <motion.div variants={itemSlideIn} className="bg-stat-card">
          <span className="bg-stat-num">{progress}%</span>
          <span className="bg-stat-label">Discovery Rate</span>
          <div className="bg-stat-track">
            <motion.div
              className="bg-stat-fill"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 1.2, ease: [0.2, 0.9, 0.2, 1] }}
            />
          </div>
        </motion.div>
      </header>

      <motion.div variants={itemSlideIn} className="bg-controls">
        <div className="bg-toggle">
          {VIEW_FILTERS.map(f => (
            <button
              key={f}
              type="button"
              className={`bg-pill ${viewFilter === f ? 'bg-pill--active' : ''}`}
              onClick={() => setViewFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        <div className="bg-dropdown-wrap" ref={menuRef}>
          <button
            type="button"
            className={`bg-pill bg-pill--dropdown ${isMenuOpen ? 'bg-pill--active' : ''}`}
            onClick={() => setIsMenuOpen(v => !v)}
          >
            <span className="bg-pill-label">{categoryLabel}</span>
            {isMenuOpen
              ? <ChevronUp size={13} strokeWidth={2.5} className="bg-chevron" />
              : <ChevronDown size={13} strokeWidth={2.5} className="bg-chevron" />}
          </button>

          <AnimatePresence>
            {isMenuOpen && (
              <motion.div
                className="bg-dropdown"
                initial={{ opacity: 0, scale: 0.92, y: -8 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.92, y: -8 }}
                transition={{ type: 'spring', stiffness: 320, damping: 26 }}
              >
                {CATEGORY_FILTERS.map(c => (
                  <button
                    key={c}
                    type="button"
                    className={`bg-dropdown-item ${categoryFilter === c ? 'bg-dropdown-item--active' : ''}`}
                    onClick={() => { setCategoryFilter(c); setIsMenuOpen(false); }}
                  >
                    {c === 'all' ? 'All Categories' : c.charAt(0).toUpperCase() + c.slice(1)}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      <motion.div variants={itemSlideIn} className="bg-progress-track">
        <motion.div
          className="bg-progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 1.2, ease: [0.2, 0.9, 0.2, 1] }}
        />
      </motion.div>

      {filtered.length === 0 ? (
        <motion.div variants={itemSlideIn} className="bg-empty">
          <Award size={48} strokeWidth={1.2} className="bg-empty-icon" />
          <p>No badges match your filters.</p>
        </motion.div>
      ) : (
        /* Cards use pure CSS animation (storyFloat) — same as StoryCard.css */
        <div className="bg-grid">
          {filtered.map(badge => {
            const rarity    = badge.rarity?.toLowerCase() ?? 'common';
            const gradient  = badge.unlocked ? (RARITY_GRADIENT[rarity] ?? RARITY_GRADIENT.common) : undefined;
            const shadow    = badge.unlocked ? (RARITY_SHADOW[rarity]   ?? RARITY_SHADOW.common)   : undefined;
            const BadgeIcon = resolveLucideIcon(badge);

            return (
              <div
                key={badge.id ?? badge.name}
                className={`bg-card ${badge.unlocked ? 'bg-card--unlocked' : 'bg-card--locked'}`}
                style={badge.unlocked ? { background: gradient, boxShadow: `0 18px 48px ${shadow}` } : undefined}
              >
                <div className="bg-card-top">
                  <div className="bg-icon-wrap">
                    {badge.unlocked ? (
                      badge.icon?.startsWith('http') ? (
                        <img src={badge.icon} alt={badge.name} className="bg-icon-img" />
                      ) : (
                        <BadgeIcon size={28} strokeWidth={1.8} className="bg-icon-lucide" />
                      )
                    ) : (
                      <Lock size={22} strokeWidth={2} className="bg-icon-lucide bg-icon-lucide--locked" />
                    )}
                  </div>

                  <div className="bg-status-wrap">
                    {badge.unlocked
                      ? <div className="bg-check">✓</div>
                      : <div className="bg-lock-dot" />}
                  </div>
                </div>

                <div className="bg-card-info">
                  <h3 className="bg-card-name">{badge.name}</h3>
                  <span className="bg-rarity-pill">{badge.rarity ?? 'Common'}</span>
                  <p className="bg-card-desc">{badge.description}</p>
                </div>

                <div className="bg-card-footer">
                  <span className="bg-card-date">
                    {badge.unlocked ? (badge.unlockedDate ?? '2026') : 'Locked'}
                  </span>
                  <span
                    className="bg-card-dot"
                    style={badge.unlocked ? { background: 'rgba(255,255,255,0.7)' } : undefined}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
};

export default BadgesPage;
