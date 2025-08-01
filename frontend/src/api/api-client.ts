import axios from "axios";

/**
 * Base API client for making HTTP requests
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to handle authentication
apiClient.interceptors.request.use(
  (config) => {
    // You can add common request handling here
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common error responses here
    if (error.response?.status === 401) {
      // Handle unauthorized access
      // For example, redirect to login page or clear auth token
      localStorage.removeItem("openhands_auth_token");
    }
    return Promise.reject(error);
  }
);