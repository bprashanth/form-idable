import { ref } from 'vue'

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const SCOPES = 'https://www.googleapis.com/auth/drive.file'

const accessToken = ref(null)
let tokenClient = null

function initTokenClient() {
  if (tokenClient) return
  if (!window.google?.accounts?.oauth2) {
    throw new Error('Google Identity Services not loaded')
  }
  tokenClient = window.google.accounts.oauth2.initTokenClient({
    client_id: CLIENT_ID,
    scope: SCOPES,
    callback: () => {}, // overridden per-call in requestAccessToken
  })
}

function requestAccessToken() {
  return new Promise((resolve, reject) => {
    try {
      initTokenClient()
    } catch (e) {
      return reject(e)
    }
    tokenClient.callback = (response) => {
      if (response.error) {
        return reject(new Error(response.error))
      }
      accessToken.value = response.access_token
      resolve(response.access_token)
    }
    tokenClient.error_callback = (err) => {
      reject(new Error(err.type || 'Auth popup closed'))
    }
    tokenClient.requestAccessToken()
  })
}

export function useGoogleAuth() {
  return { accessToken, requestAccessToken }
}
