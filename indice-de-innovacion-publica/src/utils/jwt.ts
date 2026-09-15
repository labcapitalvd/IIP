/**
 * Minimal client-side JWT payload decoder.
 *
 * This does NOT verify the signature — that is the backend's job (Ed25519,
 * see Packages/shared/src/shared/utils/tokens). It only reads the claims
 * already issued by /public/auth/login so the UI can know who is logged in
 * and whether the access token is still fresh, without another round trip.
 */

export interface JwtClaims {
  sub?: string;
  username?: string;
  token_type?: 'access' | 'refresh';
  iat?: number;
  exp?: number;
  jti?: string;
  [key: string]: unknown;
}

export function decodeJwt(token: string): JwtClaims | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;

    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);

    const json = decodeURIComponent(
      atob(padded)
        .split('')
        .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('')
    );

    return JSON.parse(json) as JwtClaims;
  } catch {
    return null;
  }
}

export function isJwtExpired(token: string, skewSeconds = 10): boolean {
  const claims = decodeJwt(token);
  if (!claims?.exp) return true;
  return Date.now() / 1000 >= claims.exp - skewSeconds;
}
