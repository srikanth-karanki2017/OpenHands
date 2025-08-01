import { useQuery } from "@tanstack/react-query";
import { User } from "#/types/user";
import { authApi } from "#/api/auth-api";

/**
 * Hook for fetching the current authenticated user
 */
export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ["current-user"],
    queryFn: () => authApi.getCurrentUser(),
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}