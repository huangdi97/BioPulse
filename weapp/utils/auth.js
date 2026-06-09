const TOKEN_KEY = 'token'

function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || ''
}

function setToken(token) {
  wx.setStorageSync(TOKEN_KEY, token)
}

function clearToken() {
  wx.removeStorageSync(TOKEN_KEY)
}

function ensureLogin() {
  const token = getToken()
  if (token) {
    return Promise.resolve(token)
  }
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        if (res.code) {
          resolve(res.code)
        } else {
          reject(new Error('wx.login failed'))
        }
      },
      fail: reject
    })
  })
}

module.exports = {
  getToken,
  setToken,
  clearToken,
  ensureLogin
}
