import { useMutation } from "@tanstack/react-query";
import { authApi, RegisterRequest } from "#/api/auth-api";

/**
 * Hook to register a new user
 */
export function useRegister() {
  return useMutation({
    mutationFn: (userData: RegisterRequest) => authApi.register(userData),
  });
}