export const getAvatarUrl = (avatarUrl, versionToken) => {
  if (!avatarUrl) return "";
  if (!versionToken) return avatarUrl;

  try {
    const url = new URL(avatarUrl);
    const parsedTime = Date.parse(versionToken);
    const cacheValue = Number.isNaN(parsedTime) ? String(versionToken) : String(parsedTime);
    url.searchParams.set("v", cacheValue);
    return url.toString();
  } catch {
    // If avatar URL is not parseable, keep original value to avoid breaking rendering.
    return avatarUrl;
  }
};
