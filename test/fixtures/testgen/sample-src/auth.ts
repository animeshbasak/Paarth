// Sample source file used by test-testgen-suggest.
// Lines 42–50, 91–103, 124 are flagged as uncovered in the jest fixture.

export function authenticate(token: string): boolean {
  if (!token) return false;
  return verifyToken(token);
}

export function verifyToken(token: string): boolean {
  return token.length > 0;
}

export async function refreshSession(refreshToken: string): Promise<string> {
  // refresh logic
  return refreshToken;
}

export class AuthError extends Error {
  constructor(message: string, public code: string) {
    super(message);
  }
}

export const isAdmin = (user: { roles: string[] }): boolean =>
  user.roles.includes("admin");
