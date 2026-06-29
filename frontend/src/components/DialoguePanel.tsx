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
  agentName?: string;
  context?: Record<string, any>;
}

const API_BASE = "/api/v1/dialogue";

export function DialoguePanel({ isOpen, onClose, sessionId: initialSessionId, agentKey, agentName, context }: Props) {
  const [sessionId, setSessionId] = useState(initialSessionId || "");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [autoSent, setAutoSent] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [displayedLen, setDisplayedLen] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, displayedLen]);

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

  useEffect(() => {
    if (isOpen && sessionId && context?.summary && !autoSent) {
      const hint: Message = {
        role: "assistant",
        content: `关于「${context.summary}」，你可以追问为什么、反馈误报等`,
        timestamp: Date.now(),
      };
      setMessages([hint]);
    }
  }, [isOpen, sessionId, context, autoSent]);

  useEffect(() => {
    if (!streamingContent || displayedLen >= streamingContent.length) return;
    const timer = window.setTimeout(() => {
      setDisplayedLen((p) => Math.min(p + 2, streamingContent.length));
    }, 25);
    return () => window.clearTimeout(timer);
  }, [streamingContent, displayedLen]);

  const startTypewriter = (text: string) => {
    setStreamingContent(text);
    setDisplayedLen(0);
  };

  const sendMessage = async (text?: string) => {
    const msg = text || input;
    if (!msg.trim() || !sessionId) return;

    const userMsg: Message = { role: "user", content: msg, timestamp: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    if (!text) setInput("");
    setLoading(true);
    if (text) setAutoSent(true);
    setStreamingContent("");
    setDisplayedLen(0);

    try {
      const res = await fetch(API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: msg, stream: true }),
      });

      if (!res.ok || !res.body) throw new Error("SSE unavailable");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      let replyText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n");
        buf = parts.pop() || "";

        let ev = "";
        let data = "";
        for (const line of parts) {
          if (line.startsWith("event: ")) {
            ev = line.slice(7);
          } else if (line.startsWith("data: ")) {
            data = line.slice(6);
          } else if (line === "" && ev && data) {
            try {
              const parsed = JSON.parse(data);
              if (ev === "dialogue.reply" && parsed.reply) {
                replyText = parsed.reply;
                startTypewriter(replyText);
              } else if (ev === "agent.llm_result" && parsed.reply_preview) {
                if (!replyText) {
                  startTypewriter(parsed.reply_preview);
                }
              } else if (ev === "dialogue.error") {
                replyText = parsed.error || "对话执行失败";
                startTypewriter(replyText);
              }
            } catch {}
            ev = "";
            data = "";
          }
        }
      }

      if (replyText) {
        setMessages((prev) => [...prev, { role: "assistant", content: replyText, timestamp: Date.now() }]);
      }
      setStreamingContent("");
      setDisplayedLen(0);
    } catch {
      try {
        const res = await fetch(`${API_BASE}/send`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, message: msg }),
        });
        const data = await res.json();
        setMessages((prev) => [...prev, { role: "assistant", content: data.reply, timestamp: Date.now() }]);
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "请求失败，请稍后重试。", timestamp: Date.now() },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (type: string) => {
    try {
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
    } catch (err) {
      console.error("Feedback failed:", err);
    }
  };

  if (!isOpen) return null;

  const title = agentName ? `${agentName} · 对话` : "对话";

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col" style={{ maxHeight: "600px" }}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ minHeight: "300px" }}>
        {messages.length === 0 && !streamingContent && (
          <p className="text-xs text-gray-400 text-center py-8">
            输入问题开始对话。支持追问"为什么"、反馈"这是误报"。
          </p>
        )}
        {messages.map((msg) => (
          <div key={msg.timestamp} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
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
        {streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg px-3 py-2 text-sm bg-gray-100 text-gray-800">
              {streamingContent.slice(0, displayedLen)}
              {displayedLen < streamingContent.length && (
                <span className="inline-block w-[2px] h-4 bg-gray-500 ml-0.5 animate-pulse" />
              )}
            </div>
          </div>
        )}
        {!streamingContent && messages.length > 0 && messages[messages.length - 1].role === "assistant" && (
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
            onClick={() => sendMessage()}
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