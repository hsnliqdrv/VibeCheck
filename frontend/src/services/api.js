// frontend/src/services/api.js
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL; // например: http://localhost:5000/api

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/* ===================== COMMUNITY / SHARES ===================== */

/**
 * Попытка получить shares для комнаты.
 * Сначала пробуем /community/rooms/:roomId/shares,
 * при 404 — пробуем /aura/shares?room_id=roomId (fallback).
 */
export const getRoomShares = async (roomId, params = {}) => {
  if (!roomId) return [];
  try {
    const res = await api.get(`/community/rooms/${roomId}/shares`, { params });
    return res.data;
  } catch (err) {
    // если endpoint не найден на бекенде — пробуем fallback
    if (err.response && err.response.status === 404) {
      const res2 = await api.get("/aura/shares", {
        params: { room_id: roomId, ...params },
      });
      return res2.data;
    }
    // пробрасываем остальные ошибки
    throw err;
  }
};

export const getCommunityRooms = (params = {}) =>
  api.get("/community/rooms", { params }).then((r) => r.data);

export const getCommunityRoomDetails = (roomId) =>
  api.get(`/community/rooms/${roomId}`).then((r) => r.data);

export const createCommunityRoom = (body) =>
  api.post("/community/rooms", body).then((r) => r.data);

/* ===================== CONTENT ===================== */

export const getMovies = (params = {}) =>
  api.get("/content/movies", { params }).then((r) => r.data);

export const getMovieDetails = (id) =>
  api.get(`/content/movies/${id}`).then((r) => r.data);

export const getAlbums = (params = {}) =>
  api.get("/content/albums", { params }).then((r) => r.data);

export const getAlbumDetails = (id) =>
  api.get(`/content/albums/${id}`).then((r) => r.data);

export const getGames = (params = {}) =>
  api.get("/content/games", { params }).then((r) => r.data);

export const getGameDetails = (id) =>
  api.get(`/content/games/${id}`).then((r) => r.data);

export const getBooks = (params = {}) =>
  api.get("/content/books", { params }).then((r) => r.data);

export const getBookDetails = (id) =>
  api.get(`/content/books/${id}`).then((r) => r.data);

export const getLocations = (params = {}) =>
  api.get("/content/locations", { params }).then((r) => r.data);

export const getLocationDetails = (id) =>
  api.get(`/content/locations/${id}`).then((r) => r.data);

/* ===================== SEARCH ===================== */

export const globalSearch = (params) =>
  api.get("/search", { params }).then((r) => r.data);

/* ===================== USER / AURA ===================== */

export const getUserProfile = () =>
  api.get("/users/profile").then((r) => r.data);

export const updateUserProfile = (body) =>
  api.put("/users/profile", body).then((r) => r.data);

export const getUserById = (userId) =>
  api.get(`/users/${userId}`).then((r) => r.data);

export const getAuraProfile = () =>
  api.get("/aura/profile").then((r) => r.data);

export const updateAuraProfile = (body) =>
  api.put("/aura/profile", body).then((r) => r.data);

export const getUserAura = (userId) =>
  api.get(`/aura/profile/${userId}`).then((r) => r.data);

export const getMyShares = (params = {}) =>
  api.get("/aura/shares", { params }).then((r) => r.data);

export const createShare = (body) =>
  api.post("/aura/shares", body).then((r) => r.data);

/* ===================== CATEGORIES HELPERS ===================== */

const CATEGORY_FETCHERS = {
  cinema: getMovies,
  music: getAlbums,
  games: getGames,
  books: getBooks,
  travel: getLocations,
};

export const getContentByCategory = (category, params = {}) => {
  const fetcher = CATEGORY_FETCHERS[category];
  if (!fetcher) throw new Error(`Unknown category: ${category}`);
  return fetcher(params);
};

/* ===================== AUTH ===================== */

export const loginUser = (credentials) =>
  api.post("/auth/login", credentials).then((r) => r.data);

export const registerUser = (userData) =>
  api.post("/auth/register", userData).then((r) => r.data);

/* ===================== EXTERNAL / MOCK ===================== */

export const getCuratorProgress = () =>
  axios
    .get("https://mock.apidog.com/m1/1194510-1189388-default/users/curator-progress")
    .then((r) => r.data);

export default api;
