import axios from "axios";

const API = "http://localhost:3000/api/v1";

export const getCuratorProgress = async (token) => {
  const response = await axios.get(
    `${API}/users/curator-progress`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );

  return response.data;
};
