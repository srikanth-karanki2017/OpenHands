import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "#/api/auth-api";

/**
 * Hook for accepting the terms of service
 */
export function useAcceptTos() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => authApi.acceptTermsOfService(),
    onSuccess: () => {
      // Invalidate current user to update the TOS acceptance status
      queryClient.invalidateQueries({ queryKey: ["current-user"] });
    },
  });
}