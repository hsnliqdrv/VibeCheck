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

const AUTH_ONLY_PATHS = [
  "/auth/login",
  "/auth/register",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
  "/auth/moderator-login",
];

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestPath = error.config?.url || "";
    const isAuthEndpoint = AUTH_ONLY_PATHS.some((p) => requestPath.includes(p));
    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.dispatchEvent(new Event("auth-changed"));
      window.dispatchEvent(
        new CustomEvent("show-unauthorized-popup", {
          detail: { message: "Unauthorized — please log in again." },
        })
      );
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (data) => api.post("/auth/login", data).then((r) => r.data);
export const register = (data) => api.post("/auth/register", data).then((r) => r.data);
export const verifyEmail = (token) =>
  api.get("/auth/verify-email", { params: { token } }).then((r) => r.data);
export const forgotPassword = (email) =>
  api.post("/auth/forgot-password", { email }).then((r) => r.data);
export const resetPassword = (token, newPassword) =>
  api.post("/auth/reset-password", { token, newPassword }).then((r) => r.data);
export const moderatorLogin = (token) =>
  api.get(`/auth/moderator-login/${token}`).then((r) => r.data);
export const getModerationReports = (params = {}) =>
  api.get("/moderation/reports", { params }).then((r) => r.data);
export const suspendUser = (userId, body) =>
  api.post(`/moderation/users/${userId}/suspend`, body).then((r) => r.data);
export const deleteModeratedRoomPost = (postId) =>
  api.delete(`/moderation/room-posts/${postId}`).then((r) => r.data);

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
export const getAuraMatches = (params = {}) =>
  api.get("/aura/matches", { params }).then((r) => r.data);

// Curator Stats
export const getCuratorStats = () =>
  api.get("/curator/stats").then((r) => r.data);

// Shares
export const getMyShares = (params = {}) =>
  api.get("/aura/shares", { params }).then((r) => r.data);
export const createShare = (body) =>
  api.post("/aura/shares", body).then((r) => r.data);

// Badges (OpenAPI: /badges, /badges/user)
export const getAllBadges = (params = {}) =>
  api.get("/badges", { params }).then((r) => r.data);
export const getUserBadges = (params = {}) =>
  api.get("/badges/user", { params }).then((r) => r.data);
export const getUserBadgesById = (userId) =>
  api.get(`/badges/user/${userId}`).then((r) => r.data);

// Social - Rooms
export const getAestheticRooms = (params = {}) =>
  api.get("/social/rooms", { params }).then((r) => r.data);
export const getRoomById = (roomId) =>
  api.get(`/social/rooms/${roomId}`).then((r) => r.data);
export const getRoomPosts = (roomId, params = {}) =>
  api.get(`/social/rooms/${roomId}/posts`, { params }).then((r) => r.data);
export const createRoomPost = (roomId, body) =>
  api.post(`/social/rooms/${roomId}/posts`, body).then((r) => r.data);
export const reportRoomPost = (roomId, postId, body) =>
  api.post(`/social/rooms/${roomId}/posts/${postId}/report`, body).then((r) => r.data);
export const joinRoom = (roomId) =>
  api.post(`/social/rooms/${roomId}/join`).then((r) => r.data);
export const leaveRoom = (roomId) =>
  api.post(`/social/rooms/${roomId}/leave`).then((r) => r.data);

// Social - Post interactions
export const likePost = (postId) =>
  api.post(`/social/posts/${postId}/like`).then((r) => r.data);
export const unlikePost = (postId) =>
  api.delete(`/social/posts/${postId}/like`).then((r) => r.data);
export const getPostComments = (postId, params = {}) =>
  api.get(`/social/posts/${postId}/comments`, { params }).then((r) => r.data);
export const addComment = (postId, body) =>
  api.post(`/social/posts/${postId}/comments`, body).then((r) => r.data);

// Discovery Feed
export const getDiscoveryFeed = (params = {}) =>
  api.get("/discovery/feed", { params }).then((r) => r.data);

// Uploads
export const getAvatarUploadUrl = (fileExtension) =>
  api
    .post("/upload/avatar", null, { params: { file_extension: fileExtension } })
    .then((r) => r.data);

export const getPostUploadUrl = (fileExtension) =>
  api
    .post("/upload/post", null, { params: { file_extension: fileExtension } })
    .then((r) => r.data);

export const uploadToPresignedUrl = async (presignedUrl, fileBlob, fileType) => {
  const response = await fetch(presignedUrl, {
    method: "PUT",
    body: fileBlob,
    headers: {
      "Content-Type": fileType,
      "x-amz-acl": "public-read",
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Upload failed (${response.status}): ${body}`);
  }

  return true;
};

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
