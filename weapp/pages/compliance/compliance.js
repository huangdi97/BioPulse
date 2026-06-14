const api = require('../../utils/api')

Page({
  data: {
    items: [
      { id: 'truth', text: '沟通内容真实、准确、可追溯', checked: false },
      { id: 'label', text: '未超适应症或夸大产品疗效', checked: false },
      { id: 'gift', text: '未提供不当利益、礼品或宴请承诺', checked: false },
      { id: 'privacy', text: '未记录无授权患者隐私信息', checked: false },
      { id: 'material', text: '使用资料来自已批准内容库', checked: false }
    ],
    result: '待检查',
    insights: [],
    insightsLoaded: false
  },

  onLoad() {
    api.getAgentInsights('compliance').then((insights) => {
      this.setData({ insights, insightsLoaded: true })
    })
  },

  toggleItem(event) {
    const id = event.currentTarget.dataset.id
    const items = this.data.items.map((item) => (
      item.id === id ? { ...item, checked: !item.checked } : item
    ))
    const passed = items.every((item) => item.checked)
    this.setData({
      items,
      result: passed ? '通过' : '待补充'
    })
  },

  reset() {
    this.setData({
      items: this.data.items.map((item) => ({ ...item, checked: false })),
      result: '待检查'
    })
  }
})
