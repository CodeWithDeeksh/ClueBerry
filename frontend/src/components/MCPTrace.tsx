import { MCPToolCall } from "../services/api";
import { Terminal, ChevronDown, ChevronRight, Zap } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

const TOOL_META: Record<string, { icon: string; color: string; label: string }> = {
  search_evidence:    { icon: "🔍", color: "text-blue-400",   label: "Search Evidence" },
  read_source:        { icon: "📖", color: "text-violet-400", label: "Read Source" },
  find_payment_match: { icon: "⚖️",  color: "text-amber-400",  label: "Match Payment" },
};

interface Props {
  calls: MCPToolCall[];
  isRunning?: boolean;
}

function ToolCallCard({ call, index }: { call: MCPToolCall; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const meta = TOOL_META[call.tool_name] || { icon: "🔧", color: "text-ink-300", label: call.tool_name };

  return (
    <div
      className="rounded-xl border border-white/5 bg-ink-900/60 overflow-hidden"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 hover:bg-white/3 transition-colors text-left"
      >
        {/* Connector line */}
        <div className="flex flex-col items-center gap-1 shrink-0">
          <div className="w-6 h-6 rounded-lg bg-berry-600/20 border border-berry-500/30 flex items-center justify-center">
            <span className="text-xs">{meta.icon}</span>
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={clsx("text-xs font-mono font-medium", meta.color)}>
              {call.tool_name}()
            </span>
            {call.evidence_ids.length > 0 && (
              <span className="text-xs bg-berry-500/10 text-berry-400 border border-berry-500/20 px-1.5 py-0.5 rounded-full">
                {call.evidence_ids.length} record{call.evidence_ids.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          <p className="text-xs text-ink-400 mt-0.5 truncate">{call.result_summary}</p>
        </div>

        <span className="text-ink-500 shrink-0">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
      </button>

      {expanded && (
        <div className="border-t border-white/5 p-3 space-y-3">
          {/* Parameters */}
          <div>
            <p className="text-xs text-ink-500 uppercase tracking-widest mb-1.5">Parameters</p>
            <pre className="text-xs text-berry-300 font-mono bg-black/30 rounded-lg p-2.5 overflow-x-auto">
              {JSON.stringify(call.parameters, null, 2)}
            </pre>
          </div>

          {/* Evidence IDs */}
          {call.evidence_ids.length > 0 && (
            <div>
              <p className="text-xs text-ink-500 uppercase tracking-widest mb-1.5">Retrieved evidence</p>
              <div className="flex flex-wrap gap-1.5">
                {call.evidence_ids.map((id) => (
                  <span key={id} className="font-mono text-xs text-emerald-400 bg-emerald-400/5 border border-emerald-400/15 px-2 py-0.5 rounded-lg">
                    {id}
                  </span>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-ink-400 font-mono">
            ⏱ {new Date(call.timestamp).toLocaleTimeString()}
          </p>
        </div>
      )}
    </div>
  );
}

export default function MCPTrace({ calls, isRunning }: Props) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <Terminal size={14} className="text-berry-400" />
        <span className="text-xs font-medium text-ink-300 uppercase tracking-widest">MCP Tool Calls</span>
        {isRunning && (
          <span className="flex items-center gap-1 text-xs text-berry-400 ml-auto">
            <Zap size={12} className="animate-pulse" />
            live
          </span>
        )}
      </div>

      {/* Connecting line */}
      <div className="relative pl-3 space-y-2">
        {calls.length > 0 && (
          <div className="absolute left-3 top-3 bottom-3 w-px bg-gradient-to-b from-berry-500/40 via-berry-500/20 to-transparent" />
        )}
        {calls.map((call, i) => (
          <ToolCallCard key={i} call={call} index={i} />
        ))}
        {isRunning && (
          <div className="flex items-center gap-2 pl-3 py-2">
            <div className="flex gap-1">
              {[0,1,2].map(i => (
                <div key={i} className="w-1.5 h-1.5 rounded-full bg-berry-500 animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }} />
              ))}
            </div>
            <span className="text-xs text-ink-500 font-mono">awaiting tool response…</span>
          </div>
        )}
        {calls.length === 0 && !isRunning && (
          <div className="text-center py-8 text-ink-500 text-sm">
            MCP tool calls will appear here during investigation
          </div>
        )}
      </div>
    </div>
  );
}
