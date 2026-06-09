App({
  globalData: {
    apiBase: 'http://localhost:8004',
    userInfo: null
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
  }
})
