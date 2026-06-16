App({
  globalData: {
    apiBase: (function(){try{var e=wx.getAccountInfoSync().miniProgram.envVersion;if(e==="develop")return"http://localhost:8004";if(e==="trial")return"https://api-staging.biopulse.com";return"https://api.biopulse.com"}catch(r){return"http://localhost:8004"}})(),
    userInfo: null
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
  }
})
