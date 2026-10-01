import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
})

/** Turn a DRF error response into { message, fields }. */
export function parseApiError(error) {
  const data = error?.response?.data
  if (!error?.response) {
    return { message: 'Cannot reach the server. Check your connection and try again.', fields: {} }
  }
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const fields = {}
    let message = data.detail || ''
    for (const [key, value] of Object.entries(data)) {
      if (key === 'detail') continue
      if (key === 'non_field_errors') {
        message = [].concat(value).join(' ')
      } else if (value && typeof value === 'object' && !Array.isArray(value)) {
        Object.assign(fields, value) // nested serializer errors, e.g. answers.* / patient.*
      } else {
        fields[key] = [].concat(value).join(' ')
      }
    }
    if (!message) message = Object.values(fields)[0] || 'Something went wrong.'
    return { message, fields }
  }
  return { message: 'Something went wrong. Please try again.', fields: {} }
}

export default client
