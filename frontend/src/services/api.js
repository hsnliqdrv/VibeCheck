import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Content
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

// Search
export const globalSearch = (params) =>
  api.get("/search", { params }).then((r) => r.data);

// User Profile
export const getUserProfile = () =>
  api.get("/users/profile").then((r) => r.data);
export const updateUserProfile = (body) =>
  api.put("/users/profile", body).then((r) => r.data);
export const getUserById = (userId) =>
  api.get(`/users/${userId}`).then((r) => r.data);

// Aura Profile
export const getAuraProfile = () =>
  api.get("/aura/profile").then((r) => r.data);
export const updateAuraProfile = (body) =>
  api.put("/aura/profile", body).then((r) => r.data);
export const getUserAura = (userId) =>
  api.get(`/aura/profile/${userId}`).then((r) => r.data);

// Curator Stats
export const getCuratorStats = () =>
  api.get("/curator/stats").then((r) => r.data);

// Shares
export const getMyShares = (params = {}) =>
  api.get("/aura/shares", { params }).then((r) => r.data);
export const createShare = (body) =>
  api.post("/aura/shares", body).then((r) => r.data);

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

export default api;
