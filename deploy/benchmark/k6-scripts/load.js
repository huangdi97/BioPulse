// BioPulse · 负载测试 (Load Test)
// 从 10 VU 逐步上升到 50 VU, 持续 3min
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const failRate = new Rate('failed_requests');
const healthTrend = new Trend('health_duration');
const loginTrend = new Trend('login_duration');
const dashboardTrend = new Trend('dashboard_duration');
const chatTrend = new Trend('chat_duration');
const tracesTrend = new Trend('traces_duration');

export const options = {
    stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 30 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 10 },
    ],
    thresholds: {
        failed_requests: ['rate<0.01'],
        http_req_duration: ['p(95)<3000'],
        health_duration: ['p(99)<100'],
        login_duration: ['p(99)<500'],
        dashboard_duration: ['p(99)<1000'],
        chat_duration: ['p(99)<5000'],
        traces_duration: ['p(99)<1000'],
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

    const passed = check(res, {
        [`${ep.tag} status 200`]: (r) => r.status === 200,
    });
    failRate.add(!passed);

    const trendMap = { health: healthTrend, login: loginTrend, dashboard: dashboardTrend, chat: chatTrend, traces: tracesTrend };
    if (trendMap[ep.tag]) {
        trendMap[ep.tag].add(res.timings.duration);
    }

    return res;
}

export default function () {
    const ep = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
    callEndpoint(ep);
    sleep(0.5 + Math.random() * 1);
}
