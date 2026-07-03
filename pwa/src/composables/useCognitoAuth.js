import { ref, computed } from 'vue'
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from 'amazon-cognito-identity-js'

const AUTH_CONFIG_URL =
  'https://fomomon.s3.ap-south-1.amazonaws.com/auth_config.json'

let userPool = null
const idToken = ref(null)
const authError = ref(null)
const isAuthenticated = computed(() => !!idToken.value)

async function init() {
  if (userPool) return
  const res = await fetch(AUTH_CONFIG_URL)
  const config = await res.json()
  userPool = new CognitoUserPool({
    UserPoolId: config.userPoolId,
    ClientId: config.clientId,
  })
}

async function login(username, password, { onNewPasswordRequired } = {}) {
  if (!userPool) await init()
  return new Promise((resolve, reject) => {
    authError.value = null
    const user = new CognitoUser({ Username: username, Pool: userPool })
    const authDetails = new AuthenticationDetails({ Username: username, Password: password })
    user.authenticateUser(authDetails, {
      onSuccess(session) {
        idToken.value = session.getIdToken().getJwtToken()
        resolve()
      },
      onFailure(err) {
        authError.value = err.message || 'Login failed'
        reject(err)
      },
      newPasswordRequired() {
        if (onNewPasswordRequired) {
          onNewPasswordRequired(user)
          reject(new Error('newPasswordRequired'))
        } else {
          authError.value = 'A new password is required. Please contact your administrator.'
          reject(new Error('newPasswordRequired'))
        }
      },
    })
  })
}

async function refreshSession() {
  if (!userPool) await init()
  return new Promise((resolve) => {
    const user = userPool.getCurrentUser()
    if (!user) {
      idToken.value = null
      resolve(false)
      return
    }
    user.getSession((err, session) => {
      if (err || !session || !session.isValid()) {
        idToken.value = null
        resolve(false)
        return
      }
      idToken.value = session.getIdToken().getJwtToken()
      resolve(true)
    })
  })
}

function logout() {
  if (userPool) {
    const user = userPool.getCurrentUser()
    if (user) user.signOut()
  }
  idToken.value = null
  authError.value = null
}

export function useCognitoAuth() {
  return {
    init,
    login,
    refreshSession,
    logout,
    idToken,
    isAuthenticated,
    authError,
  }
}
