// BioPulse · 冒烟测试 (Smoke Test)
// 1 VU, 持续 30s, 验证功能正常
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
    vus: 1,
    duration: '30s',
    thresholds: {
        failed_requests: ['rate<0.01'],
        http_req_duration: ['p(95)<2000'],
    },
};

export default function () {
    // 健康检查
    group('GET /health', () => {
        const res = http.get(`${BASE_URL}/health`);
        const passed = check(res, {
            'status is 200': (r) => r.status === 200,
            'response time < 100ms': (r) => r.timings.duration < 100,
        });
        failRate.add(!passed);
        healthTrend.add(res.timings.duration);
    });

    // 登录
    group('POST /auth/login', () => {
        const payload = JSON.stringify({
            username: 'test_user',
            password: 'test_pass',
        });
        const params = { headers: { 'Content-Type': 'application/json' } };
        const res = http.post(`${BASE_URL}/auth/login`, payload, params);
        const passed = check(res, {
            'status is 200': (r) => r.status === 200,
            'response time < 500ms': (r) => r.timings.duration < 500,
        });
        failRate.add(!passed);
        loginTrend.add(res.timings.duration);
    });

    // 合规看板
    group('GET /compliance/dashboard/summary', () => {
        const res = http.get(`${BASE_URL}/compliance/dashboard/summary`, {
            headers: { Authorization: 'Bearer test_token' },
        });
        const passed = check(res, {
            'status is 200': (r) => r.status === 200,
            'response time < 1s': (r) => r.timings.duration < 1000,
        });
        failRate.add(!passed);
        dashboardTrend.add(res.timings.duration);
    });

    // AI Chat
    group('POST /ai/chat', () => {
        const payload = JSON.stringify({
            message: 'Hello, how can you help me today?',
            context: {},
        });
        const params = { headers: { 'Content-Type': 'application/json', Authorization: 'Bearer test_token' } };
        const res = http.post(`${BASE_URL}/ai/chat`, payload, params);
        const passed = check(res, {
            'status is 200': (r) => r.status === 200,
            'response time < 5s': (r) => r.timings.duration < 5000,
        });
        failRate.add(!passed);
        chatTrend.add(res.timings.duration);
    });

    // Agent 轨迹
    group('GET /agent/traces', () => {
        const res = http.get(`${BASE_URL}/agent/traces`, {
            headers: { Authorization: 'Bearer test_token' },
        });
        const passed = check(res, {
            'status is 200': (r) => r.status === 200,
            'response time < 1s': (r) => r.timings.duration < 1000,
        });
        failRate.add(!passed);
        tracesTrend.add(res.timings.duration);
    });

    sleep(1);
}
