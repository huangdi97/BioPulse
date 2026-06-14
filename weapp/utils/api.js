const auth = require('./auth')

function baseUrl() {
  const app = getApp()
  return (app.globalData && app.globalData.apiBase) || 'http://localhost:8004'
}

function request(options) {
  const token = auth.getToken()
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl()}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {})
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(new Error((res.data && res.data.message) || `HTTP ${res.statusCode}`))
        }
      },
      fail: reject
    })
  })
}

function searchHcp(keyword) {
  const normalized = (keyword || '').trim().toLowerCase()
  return request({
    url: '/hcp?page=1&page_size=100'
  }).then((res) => {
    if (!normalized || !res.data || !res.data.items) {
      return res
    }
    res.data.items = res.data.items.filter((item) => {
      return [item.name, item.department, item.hospital]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalized))
    })
    return res
  })
}

function createSchedule(payload) {
  return request({
    url: '/schedule',
    method: 'POST',
    data: payload
  })
}

function optimizeSchedule(payload) {
  return request({
    url: '/api/schedule/optimize',
    method: 'POST',
    data: payload
  })
}

function getAgentInsights(pageId) {
  return request({
    url: `/api/cloud/agent/insights?page=${pageId}`
  }).then((res) => res.insights || []).catch(() => [])
}

module.exports = {
  request,
  searchHcp,
  createSchedule,
  optimizeSchedule,
  getAgentInsights
}
