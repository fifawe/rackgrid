import { apiClient } from "./client";

export async function login(username: string, password: string): Promise<string> {
  const { data } = await apiClient.post<{ access_token: string; token_type: string }>("/auth/login", {
    username,
    password,
  });
  return data.access_token;
}

/** Lets the currently logged-in user change their own password (any
 * role). Throws (via axios) with a response detail on the wrong current
 * password (400) or too-short new password (422). */
export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await apiClient.put("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}
