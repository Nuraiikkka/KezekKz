import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
})

export function getErrorText(error) {
  if (!error.response) {
    return 'Cannot connect to the server.'
  }
  const data = error.response.data
  if (data.detail) {
    return data.detail
  }
  const first = Object.values(data)[0]
  if (Array.isArray(first)) {
    return first[0]
  }
  if (typeof first === 'object') {
    return Object.values(first)[0]
  }
  return 'Something went wrong.'
}

export default api
