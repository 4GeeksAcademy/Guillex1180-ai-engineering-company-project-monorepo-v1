import axios from "axios";
import { apiClient } from "../lib/apiClient";

export const ACCESS_TOKEN_KEY = "trackflow_access_token";

export type AuthMessage = {
  message: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<{ detail?: string }>(error)) {
    return error.response?.data?.detail ?? fallback;
  }
  return fallback;
}

export async function requestPasswordReset(email: string): Promise<AuthMessage> {
  const response = await apiClient.post<AuthMessage>("/auth/forgot-password", { email });
  return response.data;
}

export async function resetPassword(token: string, newPassword: string): Promise<AuthMessage> {
  const response = await apiClient.post<AuthMessage>("/auth/reset-password", {
    token,
    new_password: newPassword,
  });
  return response.data;
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
  accessToken: string,
): Promise<AuthMessage> {
  const response = await apiClient.post<AuthMessage>(
    "/auth/change-password",
    {
      current_password: currentPassword,
      new_password: newPassword,
    },
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );
  return response.data;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams({ username: email, password });
  const response = await apiClient.post<LoginResponse>("/auth/login", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}
