import { useMutation } from "@tanstack/react-query";
import { authApi, LoginRequest } from "#/api/auth-api";
import { useAuth } from "#/hooks/use-auth";

/**
 * Hook to login a user
 */
export function useLogin() {
  const { login } = useAuth();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (data) => {
      login(data);
    },
  });
}
