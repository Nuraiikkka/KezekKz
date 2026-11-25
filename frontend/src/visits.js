function read(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key))
    return value || fallback
  } catch {
    return fallback
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    return
  }
}

export function getTokens() {
  return read('visits', [])
}

export function addToken(token) {
  const tokens = getTokens()
  if (!tokens.includes(token)) {
    write('visits', [token, ...tokens])
  }
}

export function getProfile() {
  return read('profile', { name: '', phone: '' })
}

export function saveProfile(profile) {
  write('profile', profile)
}
