import { InvestigationReport } from "../services/api";
import { CheckCircle2, AlertTriangle, XCircle, Clock, FileText, Copy, ChevronRight } from "lucide-react";
import clsx from "clsx";
import { useState } from "react";

const MATCH_CONFIG: Record<string, { icon: React.ReactNode; color: string; bg: string; border: string; label: string }> = {
  strong_match:              { icon: <CheckCircle2 size={18} />, color: "text-emerald-400", bg: "bg-emerald-500/8",  border: "border-emerald-500/20", label: "Strong Match — Payment Evidence Found" },
  possible_match:            { icon: <CheckCircle2 size={18} />, color: "text-blue-400",    bg: "bg-blue-500/8",    border: "border-blue-500/20",    label: "Possible Match — Verify to Confirm" },
  amount_mismatch:           { icon: <AlertTriangle size={18} />, color: "text-amber-400",  bg: "bg-amber-500/8",   border: "border-amber-500/20",   label: "Amount Mismatch — Partial or Incorrect Payment" },
  partial_payment_possible:  { icon: <AlertTriangle size={18} />, color: "text-amber-400",  bg: "bg-amber-500/8",   border: "border-amber-500/20",   label: "Partial Payment Possible" },
  no_payment_evidence_found: { icon: <XCircle size={18} />,       color: "text-red-400",    bg: "bg-red-500/8",     border: "border-red-500/20",     label: "No Payment Evidence Found" },
  conflicting_records:       { icon: <XCircle size={18} />,       color: "text-red-400",    bg: "bg-red-500/8",     border: "border-red-500/20",     label: "Conflicting Records Detected" },
};

export default function ReportPanel({ report }: { report: InvestigationReport }) {
  const [copied, setCopied] = useState(false);
  const cfg = MATCH_CONFIG[report.match_status] || MATCH_CONFIG.possible_match;

  const copyDraft = () => {
    navigator.clipboard.writeText(report.draft_response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4 animate-fade-up">
      {/* Finding banner */}
      <div className={clsx("rounded-2xl border p-5", cfg.bg, cfg.border)}>
        <div className={clsx("flex items-center gap-3 mb-3", cfg.color)}>
          {cfg.icon}
          <span className="font-semibold text-sm">{cfg.label}</span>
        </div>
        <p className="text-white font-medium leading-snug">{report.finding}</p>
      </div>

      {/* Summary */}
      <div className="card p-5">
        <h3 className="text-xs font-medium text-ink-400 uppercase tracking-widest mb-3">Investigation Summary</h3>
        <p className="text-sm text-ink-200 leading-relaxed">{report.summary}</p>
      </div>

      {/* Evidence cards */}
      {report.evidence_list.length > 0 && (
        <div className="card p-5 space-y-3">
          <h3 className="text-xs font-medium text-ink-400 uppercase tracking-widest">Evidence Sources</h3>
          <div className="space-y-2">
            {report.evidence_list.map((ev, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/3 border border-white/5">
                <FileText size={14} className="text-berry-400 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs text-berry-300">[{ev.evidence_id}]</span>
                    <span className="text-xs text-ink-400">{ev.source_filename}</span>
                  </div>
                  <p className="text-sm text-white mt-0.5">{ev.value}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline */}
      {report.timeline.length > 0 && (
        <div className="card p-5 space-y-3">
          <h3 className="text-xs font-medium text-ink-400 uppercase tracking-widest flex items-center gap-2">
            <Clock size={12} />
            Timeline
          </h3>
          <div className="relative pl-4 space-y-3">
            <div className="absolute left-4 top-1.5 bottom-1.5 w-px bg-gradient-to-b from-berry-500/40 to-transparent" />
            {report.timeline.map((entry, i) => (
              <div key={i} className="flex gap-4 group">
                <div className="relative shrink-0">
                  <div className="w-2 h-2 rounded-full bg-berry-500 mt-1.5 ring-2 ring-ink-900" />
                </div>
                <div className="pb-2">
                  {entry.date && (
                    <span className="font-mono text-xs text-berry-400">{entry.date}</span>
                  )}
                  <p className="text-sm text-ink-200 mt-0.5">{entry.event}</p>
                  <p className="text-xs text-ink-500 font-mono mt-0.5">{entry.source_filename}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contradictions */}
      {report.contradictions.length > 0 && (
        <div className="card p-5 border-amber-500/15 space-y-2">
          <h3 className="text-xs font-medium text-amber-400 uppercase tracking-widest flex items-center gap-2">
            <AlertTriangle size={12} />
            Contradictions Detected
          </h3>
          <ul className="space-y-1.5">
            {report.contradictions.map((c, i) => (
              <li key={i} className="flex gap-2 text-sm text-ink-200">
                <ChevronRight size={14} className="text-amber-400 mt-0.5 shrink-0" />
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Confidence note */}
      {report.confidence_note && (
        <div className="rounded-xl bg-white/3 border border-white/5 p-4">
          <p className="text-xs text-ink-400 leading-relaxed">
            <span className="text-ink-300 font-medium">Limitations: </span>
            {report.confidence_note}
          </p>
        </div>
      )}

      {/* Draft response */}
      {report.draft_response && (
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-medium text-ink-400 uppercase tracking-widest">Draft Response</h3>
            <button
              onClick={copyDraft}
              className={clsx(
                "flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-all",
                copied
                  ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/20"
                  : "text-ink-400 hover:text-white border-white/10 hover:border-white/20 bg-white/3"
              )}
            >
              <Copy size={12} />
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <p className="text-sm text-ink-200 leading-relaxed whitespace-pre-wrap font-sans">
            {report.draft_response}
          </p>
        </div>
      )}
    </div>
  );
}
