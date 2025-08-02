import { apiClient } from "./api-client";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface UserResponse {
  user_id: string;
  username: string;
  email?: string;
  created_at: string;
  last_login?: string;
  email_verified: boolean;
}

/**
 * API client for authentication
 */
export const authApi = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const formData = new FormData();
    formData.append("username", credentials.username);
    formData.append("password", credentials.password);

    const response = await apiClient.post<TokenResponse>("/api/auth/token", credentials);
    return response.data;
  },

  /**
   * Register a new user
   */
  register: async (userData: RegisterRequest): Promise<UserResponse> => {
    const response = await apiClient.post<UserResponse>("/api/auth/register", userData);
    return response.data;
  },

  /**
   * Get current user information
   */
  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>("/api/auth/me");
    return response.data;
  },
};
