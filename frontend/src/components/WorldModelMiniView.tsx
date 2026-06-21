import React, { useEffect, useState } from "react";

const API_BASE = "/api/v1/world-model";

interface Cognition {
  cognition_id: string;
  pattern: string;
  description: string;
  confidence: number;
}

export default function WorldModelMiniView() {
  const [cognitions, setCognitions] = useState<Cognition[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/cognitions?min_confidence=0.4&limit=3`)
      .then((r) => r.json())
      .then((data) => setCognitions(data.cognitions || []))
      .catch(() => {});
  }, []);

  if (cognitions.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-4">暂无认知发现</p>;
  }

  return (
    <div className="space-y-3">
      {cognitions.map((c) => (
        <div key={c.cognition_id} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
          <p className="text-sm font-medium text-gray-800">{c.pattern}</p>
          <p className="text-xs text-gray-500 mt-1">{c.description}</p>
          <span className="text-xs text-gray-400 mt-1 inline-block">
            置信度: {Math.round(c.confidence * 100)}%
          </span>
        </div>
      ))}
    </div>
  );
}
