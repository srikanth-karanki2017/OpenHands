import React, { createContext, useContext, useEffect, useState } from "react";
import { authApi, TokenResponse, UserResponse } from "#/api/auth-api";
import { apiClient } from "#/api/api-client";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserResponse | null;
  login: (token: TokenResponse) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_STORAGE_KEY = "openhands_auth_token";

/**
 * Provider component for authentication state
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [user, setUser] = useState<UserResponse | null>(null);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);

      if (storedToken) {
        try {
          const token = JSON.parse(storedToken) as TokenResponse;

          // Check if token is expired
          const expiresAt = new Date(token.expires_at);
          if (expiresAt > new Date()) {
            // Set auth header for API requests
            apiClient.defaults.headers.common["Authorization"] = `${token.token_type} ${token.access_token}`;

            // Fetch current user
            const userData = await authApi.getCurrentUser();
            setUser(userData);
            setIsAuthenticated(true);
          } else {
            // Token expired, remove it
            localStorage.removeItem(TOKEN_STORAGE_KEY);
          }
        } catch (error) {
          console.error("Error initializing auth:", error);
          localStorage.removeItem(TOKEN_STORAGE_KEY);
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = (token: TokenResponse) => {
    // Store token in localStorage
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(token));

    // Set auth header for API requests
    apiClient.defaults.headers.common["Authorization"] = `${token.token_type} ${token.access_token}`;

    // Update auth state
    setIsAuthenticated(true);

    // Fetch user data
    authApi.getCurrentUser()
      .then(userData => {
        setUser(userData);
      })
      .catch(error => {
        console.error("Error fetching user data:", error);
      });
  };

  const logout = () => {
    // Remove token from localStorage
    localStorage.removeItem(TOKEN_STORAGE_KEY);

    // Remove auth header
    delete apiClient.defaults.headers.common["Authorization"];

    // Update auth state
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access authentication state and methods
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
