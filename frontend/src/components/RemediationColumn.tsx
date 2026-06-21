import React from "react";
import { RedFlagCard } from "./RedFlagCard";

interface Props {
  title: string;
  count: number;
  orders: any[];
  onTransition?: (id: string, target: string) => void;
  color: string;
}

export function RemediationColumn({ title, count, orders, onTransition, color }: Props) {
  return (
    <div className="flex-1 min-w-[250px] bg-gray-50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-3 h-3 rounded-full ${color}`} />
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        <span className="text-xs text-gray-400 bg-white rounded-full px-2 py-0.5">{count}</span>
      </div>
      <div className="space-y-1">
        {orders.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-6">暂无工单</p>
        ) : (
          orders.map((o) => (
            <RedFlagCard key={o.order_id} order={o} onTransition={onTransition} />
          ))
        )}
      </div>
    </div>
  );
}
