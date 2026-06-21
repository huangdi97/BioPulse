import React, { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  sessionId?: string;
  agentKey?: string;
  context?: Record<string, any>;
}

const API_BASE = "/api/v1/dialogue";

export function DialoguePanel({ isOpen, onClose, sessionId: initialSessionId, agentKey, context }: Props) {
  const [sessionId, setSessionId] = useState(initialSessionId || "");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // 自动滚到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 初始化 session
  useEffect(() => {
    if (isOpen && !sessionId) {
      fetch(`${API_BASE}/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_key: agentKey || "system",
          user_id: "current_user",
          context: context || {},
        }),
      })
        .then((r) => r.json())
        .then((data) => setSessionId(data.session_id));
    }
  }, [isOpen, sessionId, agentKey, context]);

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;

    const userMsg: Message = { role: "user", content: input, timestamp: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: input }),
      });
      const data = await res.json();
      const reply: Message = { role: "assistant", content: data.reply, timestamp: Date.now() };
      setMessages((prev) => [...prev, reply]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "请求失败，请稍后重试。", timestamp: Date.now() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (type: string) => {
    await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        feedback_type: type,
        target_id: sessionId,
        content: "",
        session_id: sessionId,
      }),
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col" style={{ maxHeight: "600px" }}>
      {/* 标题栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <h3 className="text-sm font-semibold text-gray-700">对话</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ minHeight: "300px" }}>
        {messages.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-8">
            输入问题开始对话。支持追问"为什么"、反馈"这是误报"。
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {/* 反馈按钮（在最后一条AI回复后） */}
        {messages.length > 0 && messages[messages.length - 1].role === "assistant" && (
          <div className="flex gap-2 justify-start pl-2">
            <button
              onClick={() => handleFeedback("useful")}
              className="text-xs text-gray-400 hover:text-green-500"
            >
              有用
            </button>
            <button
              onClick={() => handleFeedback("misreport")}
              className="text-xs text-gray-400 hover:text-red-500"
            >
              误报
            </button>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 输入框 */}
      <div className="border-t border-gray-200 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="输入问题..."
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-400"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
          >
            {loading ? "..." : "发送"}
          </button>
        </div>
      </div>
    </div>
  );
}
