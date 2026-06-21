import React, { useEffect, useState } from "react";
import { RemediationColumn } from "../../components/RemediationColumn";

const API_BASE = "/api/v1/remediation";

const COLUMN_CONFIG = [
  { title: "待处理", statuses: ["discovered", "confirmed"], color: "bg-blue-400" },
  { title: "进行中", statuses: ["analyzing", "assigned", "remediating"], color: "bg-yellow-400" },
  { title: "待复查", statuses: ["reviewing"], color: "bg-orange-400" },
  { title: "已完成", statuses: ["scored", "closed", "archived"], color: "bg-green-400" },
];

export default function RemediationBoard() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/orders`)
      .then((r) => r.json())
      .then((data) => {
        setOrders(data.orders || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleTransition = async (orderId: string, target: string) => {
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/transition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_status: target, operator: "current_user" }),
      });
      if (res.ok) {
        const updated = await res.json();
        setOrders((prev) =>
          prev.map((o) => (o.order_id === orderId ? updated : o))
        );
      }
    } catch {
      // ignore
    }
  };

  const filterOrders = (statuses: string[]) =>
    orders.filter((o) => statuses.includes(o.status));

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>;
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">整改看板</h1>
        <p className="text-sm text-gray-500 mt-1">红灯事件→整改工单全生命周期管理</p>
      </div>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {COLUMN_CONFIG.map((col) => (
          <RemediationColumn
            key={col.title}
            title={col.title}
            count={filterOrders(col.statuses).length}
            orders={filterOrders(col.statuses)}
            onTransition={handleTransition}
            color={col.color}
          />
        ))}
      </div>
    </div>
  );
}
