const api = require('../../utils/api')

Page({
  data: {
    hcpId: '',
    hcpName: '',
    visitType: '学术拜访',
    content: '',
    visitTime: '',
    submitting: false,
    visitTypes: ['学术拜访', '产品沟通', '术后随访', '科室会议'],
    insights: [],
    insightsLoaded: false
  },

  onLoad(query) {
    const now = new Date()
    const visitTime = now.toISOString().slice(0, 16).replace('T', ' ')
    this.setData({
      hcpId: query.hcp_id || '',
      hcpName: query.hcp_name ? decodeURIComponent(query.hcp_name) : '',
      visitTime
    })
    api.getAgentInsights('visit').then((insights) => {
      this.setData({ insights, insightsLoaded: true })
    })
  },

  bindTypeChange(event) {
    this.setData({ visitType: this.data.visitTypes[event.detail.value] })
  },

  onHcpInput(event) {
    this.setData({ hcpName: event.detail.value })
  },

  onContentInput(event) {
    this.setData({ content: event.detail.value })
  },

  onTimeInput(event) {
    this.setData({ visitTime: event.detail.value })
  },

  submitVisit() {
    if (!this.data.hcpName || !this.data.content) {
      wx.showToast({ title: '请补充 HCP 和内容', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    api.createSchedule({
      title: `${this.data.visitType} - ${this.data.hcpName}`,
      description: this.data.content,
      event_type: 'visit',
      start_time: this.data.visitTime,
      location: this.data.hcpName
    })
      .then(() => {
        wx.showToast({ title: '已保存', icon: 'success' })
      })
      .catch(() => {
        wx.showToast({ title: '保存失败', icon: 'none' })
      })
      .finally(() => {
        this.setData({ submitting: false })
      })
  }
})
