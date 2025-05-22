/**
 * Salts and hashes a plaintext password using SHA-256 (Edge Runtime compatible).
 * @param password The plaintext password
 * @returns The salted and hashed password as a hex string (Promise)
 */
export async function saltAndHashPassword(password: string): Promise<string> {
  // In production, use a unique salt per user and store it alongside the hash.
  // Here we use a static salt for demonstration purposes only.
  const salt = process.env.PASSWORD_SALT || "static_salt_change_me";
  const data = new TextEncoder().encode(salt + password);
  const digest = await crypto.subtle.digest("SHA-256", data);
  // Convert ArrayBuffer to hex string
  return Array.from(new Uint8Array(digest))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}
