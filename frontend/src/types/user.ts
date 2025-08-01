/**
 * User interface representing a user in the system
 */
export interface User {
  user_id: string;
  username: string;
  email?: string;
  email_verified: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

/**
 * Login request interface
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * Registration request interface
 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

/**
 * Token response interface
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}