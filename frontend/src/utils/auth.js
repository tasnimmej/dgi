// Simple auth helper using localStorage for access token

export function saveToken(token) {
  localStorage.setItem('access_token', token)
}

export function getToken() {
  return localStorage.getItem('access_token')
}

export function removeToken() {
  localStorage.removeItem('access_token')
}

export function authHeader() {
  const token = getToken()
  if (!token) return {}
  return { Authorization: `Bearer ${token}` }
}
