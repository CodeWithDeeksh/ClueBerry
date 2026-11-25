import { useEffect, useRef, useState } from "react";
import { Search, Send, Loader2, FileText, CheckSquare, Square } from "lucide-react";
import {
  listDocuments, startInvestigation, getInvestigation,
  DocumentMeta, Investigation,
} from "../services/api";
import MCPTrace from "../components/MCPTrace";
import ReportPanel from "../components/ReportPanel";
import clsx from "clsx";

const SUGGESTIONS = [
  "Did I already pay invoice INV-1042?",
  "Is there any payment evidence for this invoice?",
  "Do the amounts on the invoice and receipt match?",
  "Was the reminder sent after the payment was made?",
];

export default function InvestigatePage() {
  const [docs, setDocs] = useState<DocumentMeta[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    listDocuments().then(setDocs).catch(() => {});
  }, []);

  const toggleDoc = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const submit = async () => {
    if (!question.trim() || selectedIds.length === 0) return;
    setError("");
    setIsLoading(true);
    setInvestigation(null);

    try {
      const { investigation_id } = await startInvestigation(question, selectedIds);

      // Initial fetch
      const initial = await getInvestigation(investigation_id);
      setInvestigation(initial);

      // Poll
      pollRef.current = setInterval(async () => {
        const updated = await getInvestigation(investigation_id);
        setInvestigation(updated);
        if (updated.status === "complete" || updated.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setIsLoading(false);
        }
      }, 2000);
    } catch (e) {
      setError("Failed to start investigation. Is the backend running?");
      setIsLoading(false);
    }
  };

  const isRunning = investigation?.status === "running" || investigation?.status === "queued";

  return (
    <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 max-w-6xl">
      {/* Left — input panel */}
      <div className="xl:col-span-2 space-y-5">
        <div>
          <h1 className="text-2xl font-bold text-white">Investigate</h1>
          <p className="text-ink-400 mt-1 text-sm">Ask a question. ClueBerry retrieves and verifies evidence.</p>
        </div>

        {/* Document selector */}
        <div className="card p-4 space-y-3">
          <p className="text-xs font-medium text-ink-400 uppercase tracking-widest">Select documents</p>
          {docs.length === 0 ? (
            <p className="text-sm text-ink-500 py-2">No documents yet — upload some first.</p>
          ) : (
            <div className="space-y-1.5">
              {docs.map((doc) => (
                <button
                  key={doc.document_id}
                  onClick={() => doc.status === "READY" && toggleDoc(doc.document_id)}
                  disabled={doc.status !== "READY"}
                  className={clsx(
                    "w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-all",
                    selectedIds.includes(doc.document_id)
                      ? "border-berry-500/40 bg-berry-500/8"
                      : "border-white/5 bg-white/2 hover:bg-white/4",
                    doc.status !== "READY" && "opacity-40 cursor-not-allowed"
                  )}
                >
                  <span className="shrink-0 text-berry-400">
                    {selectedIds.includes(doc.document_id) ? <CheckSquare size={15} /> : <Square size={15} className="text-ink-500" />}
                  </span>
                  <FileText size={14} className="text-ink-400 shrink-0" />
                  <span className="text-sm text-white truncate flex-1">{doc.filename}</span>
                  <span className={clsx("text-xs px-2 py-0.5 rounded-full border font-mono shrink-0",
                    doc.status === "READY" ? "status-ready" : "status-processing"
                  )}>
                    {doc.status}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Question input */}
        <div className="card p-4 space-y-3">
          <p className="text-xs font-medium text-ink-400 uppercase tracking-widest">Your question</p>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Did I already pay invoice INV-1042?"
            className="w-full bg-transparent resize-none text-sm text-white placeholder-ink-500 outline-none min-h-[80px]"
            onKeyDown={(e) => { if (e.key === "Enter" && e.metaKey) submit(); }}
          />
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setQuestion(s)}
                className="text-xs text-ink-400 hover:text-berry-400 border border-white/8 hover:border-berry-500/30 px-2.5 py-1 rounded-full transition-all"
              >
                {s.length > 36 ? s.slice(0, 36) + "…" : s}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        {error && <p className="text-sm text-red-400 px-1">{error}</p>}
        <button
          onClick={submit}
          disabled={isLoading || !question.trim() || selectedIds.length === 0}
          className={clsx(
            "w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium text-sm transition-all",
            isLoading || !question.trim() || selectedIds.length === 0
              ? "bg-white/5 text-ink-500 cursor-not-allowed"
              : "bg-berry-600 hover:bg-berry-500 text-white shadow-berry hover:shadow-berry-lg active:scale-98"
          )}
        >
          {isLoading ? (
            <><Loader2 size={16} className="animate-spin" /> Investigating…</>
          ) : (
            <><Send size={16} /> Investigate</>
          )}
        </button>
      </div>

      {/* Right — results */}
      <div className="xl:col-span-3 space-y-5">
        {/* MCP trace */}
        <div className="card p-5">
          <MCPTrace
            calls={investigation?.mcp_tool_calls || []}
            isRunning={isRunning}
          />
        </div>

        {/* Report */}
        {investigation?.status === "complete" && investigation.report && (
          <ReportPanel report={investigation.report} />
        )}

        {investigation?.status === "failed" && (
          <div className="card p-5 border-red-500/15">
            <p className="text-red-400 text-sm font-medium">Investigation failed</p>
            <p className="text-xs text-ink-400 mt-1">{investigation.error}</p>
          </div>
        )}

        {!investigation && (
          <div className="card p-10 text-center">
            <div className="w-14 h-14 rounded-2xl bg-berry-500/10 flex items-center justify-center mx-auto mb-4">
              <Search size={24} className="text-berry-400" />
            </div>
            <p className="text-white font-medium">Ready to investigate</p>
            <p className="text-sm text-ink-400 mt-1">
              Select documents, ask your question, and ClueBerry will retrieve and verify the evidence.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
