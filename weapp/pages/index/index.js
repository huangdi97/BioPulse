const api = require('../../utils/api')

Page({
  data: {
    keyword: '',
    loading: false,
    hcps: []
  },

  onLoad() {
    this.search()
  },

  onInput(event) {
    this.setData({ keyword: event.detail.value })
  },

  search() {
    this.setData({ loading: true })
    api.searchHcp(this.data.keyword)
      .then((res) => {
        const items = res.data && res.data.items ? res.data.items : []
        this.setData({ hcps: items })
      })
      .catch(() => {
        wx.showToast({ title: '查询失败', icon: 'none' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  selectHcp(event) {
    const hcp = event.currentTarget.dataset.hcp
    wx.navigateTo({
      url: `/pages/visit/visit?hcp_id=${hcp.id}&hcp_name=${encodeURIComponent(hcp.name)}`
    })
  }
})
