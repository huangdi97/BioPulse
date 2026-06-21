import React from "react";

interface RedFlagCardProps {
  order: {
    order_id: string;
    red_flag_id: string;
    status: string;
    assigned_to: string;
    created_at: string;
    score: number | null;
    notes: string;
    history: string;
  };
  onTransition?: (orderId: string, target: string) => void;
}

const STATUS_LABELS: Record<string, string> = {
  discovered: "待确认",
  confirmed: "待分析",
  analyzing: "分析中",
  assigned: "已分配",
  remediating: "整改中",
  reviewing: "待复查",
  scored: "已评分",
  closed: "已关闭",
  archived: "已归档",
};

const SEVERITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-700 border-gray-300",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
  high: "bg-orange-100 text-orange-700 border-orange-300",
  critical: "bg-red-100 text-red-700 border-red-300",
};

const STATUS_COLORS: Record<string, string> = {
  discovered: "border-l-gray-400",
  confirmed: "border-l-blue-400",
  analyzing: "border-l-indigo-400",
  assigned: "border-l-purple-400",
  remediating: "border-l-yellow-400",
  reviewing: "border-l-orange-400",
  scored: "border-l-green-400",
  closed: "border-l-green-600",
  archived: "border-l-gray-500",
};

export function RedFlagCard({ order, onTransition }: RedFlagCardProps) {
  const statusLabel = STATUS_LABELS[order.status] || order.status;
  const borderColor = STATUS_COLORS[order.status] || "border-l-gray-400";
  const severity = "medium";

  const handleTransition = (target: string) => {
    if (onTransition) onTransition(order.order_id, target);
  };

  const progressActions = () => {
    switch (order.status) {
      case "discovered":
        return (
          <button
            onClick={() => handleTransition("confirmed")}
            className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            确认接收
          </button>
        );
      case "reviewing":
        return (
          <div className="flex gap-2">
            <button
              onClick={() => handleTransition("scored")}
              className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
            >
              复查评分
            </button>
          </div>
        );
      case "remediating":
        return (
          <button
            onClick={() => handleTransition("reviewing")}
            className="px-3 py-1 text-xs bg-orange-500 text-white rounded hover:bg-orange-600"
          >
            提交复查
          </button>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 border-l-4 ${borderColor} p-4 mb-3`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs px-2 py-0.5 rounded-full border ${SEVERITY_COLORS[severity]}`}>
          {severity.toUpperCase()}
        </span>
        <span className="text-xs text-gray-500">{order.created_at?.slice(0, 10)}</span>
      </div>
      <div className="text-sm font-medium text-gray-900 mb-1">
        红灯 #{order.red_flag_id?.slice(0, 8)}
      </div>
      <div className="text-xs text-gray-600 mb-1">
        责任人: {order.assigned_to || "未分配"} | 状态: {statusLabel}
      </div>
      <div className="flex items-center justify-between mt-3">
        {progressActions()}
      </div>
    </div>
  );
}
