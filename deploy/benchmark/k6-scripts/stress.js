// BioPulse · 压力测试 (Stress Test)
// 从 10 VU 逐步上升到 100 VU, 持续 5min, 观察熔断点
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const failRate = new Rate('failed_requests');
const errorRate = new Rate('error_rate');

const healthTrend = new Trend('health_duration');
const loginTrend = new Trend('login_duration');
const dashboardTrend = new Trend('dashboard_duration');
const chatTrend = new Trend('chat_duration');
const tracesTrend = new Trend('traces_duration');

export const options = {
    stages: [
        { duration: '1m', target: 10 },
        { duration: '1m', target: 30 },
        { duration: '1m', target: 50 },
        { duration: '1m', target: 80 },
        { duration: '1m', target: 100 },
    ],
    thresholds: {
        failed_requests: ['rate<0.05'],
        http_req_duration: ['p(95)<10000'],
    },
};

const ENDPOINTS = [
    { method: 'GET', path: '/health', tag: 'health' },
    { method: 'POST', path: '/auth/login', tag: 'login', body: { username: 'test_user', password: 'test_pass' } },
    { method: 'GET', path: '/compliance/dashboard/summary', tag: 'dashboard', auth: true },
    { method: 'POST', path: '/ai/chat', tag: 'chat', auth: true, body: { message: 'test', context: {} } },
    { method: 'GET', path: '/agent/traces', tag: 'traces', auth: true },
];

function callEndpoint(ep) {
    const params = { headers: { 'Content-Type': 'application/json' } };
    if (ep.auth) {
        params.headers['Authorization'] = 'Bearer test_token';
    }

    let res;
    if (ep.method === 'GET') {
        res = http.get(`${BASE_URL}${ep.path}`, params);
    } else {
        res = http.post(`${BASE_URL}${ep.path}`, JSON.stringify(ep.body || {}), params);
    }

    const ok = res.status === 200;
    const passed = check(res, {
        [`${ep.tag} status 200`]: (r) => r.status === 200,
    });
    failRate.add(!passed);
    if (!ok) errorRate.add(1);

    const trendMap = { health: healthTrend, login: loginTrend, dashboard: dashboardTrend, chat: chatTrend, traces: tracesTrend };
    if (trendMap[ep.tag]) {
        trendMap[ep.tag].add(res.timings.duration);
    }

    return res;
}

export default function () {
    const ep = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
    callEndpoint(ep);
    sleep(0.3 + Math.random() * 0.7);
}
