import { useCognitoAuth } from './useCognitoAuth.js'

const baseUrl = import.meta.env.VUE_APP_API_BASE_URL || ''

export async function apiFetch(path, options = {}) {
  const { idToken, refreshSession } = useCognitoAuth()

  const doFetch = () => {
    const headers = { ...options.headers }
    if (idToken.value) {
      headers['Authorization'] = `Bearer ${idToken.value}`
    }
    return fetch(`${baseUrl}${path}`, { ...options, headers })
  }

  let res = await doFetch()

  if (res.status === 401) {
    const refreshed = await refreshSession()
    if (refreshed) {
      res = await doFetch()
    }
  }

  return res
}
