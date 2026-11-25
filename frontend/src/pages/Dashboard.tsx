import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, FileText, Search, Shield, Zap, TrendingUp } from "lucide-react";
import { listDocuments, DocumentMeta } from "../services/api";

const STAT_CARDS = [
  { label: "Documents", icon: FileText, color: "text-blue-400", bg: "bg-blue-500/10" },
  { label: "Investigations", icon: Search, color: "text-berry-400", bg: "bg-berry-500/10" },
  { label: "Verified", icon: Shield, color: "text-emerald-400", bg: "bg-emerald-500/10" },
];

export default function Dashboard() {
  const [docs, setDocs] = useState<DocumentMeta[]>([]);

  useEffect(() => {
    listDocuments().then(setDocs).catch(() => {});
  }, []);

  return (
    <div className="space-y-10 max-w-4xl">
      {/* Hero */}
      <div className="relative">
        {/* Background glow */}
        <div className="absolute -top-20 -left-20 w-96 h-96 bg-berry-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-berry-500/10 border border-berry-500/20 text-xs text-berry-400 font-medium mb-6">
            <Zap size={11} />
            MCP-powered evidence investigation
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Every claim,<br />
            <span className="text-berry-400">traced to source.</span>
          </h1>

          <p className="text-ink-300 text-lg leading-relaxed max-w-xl mb-8">
            Upload invoices, receipts and payment reminders. ClueBerry investigates using real evidence — not AI guesswork — and cites every finding.
          </p>

          <div className="flex items-center gap-3">
            <Link to="/investigate" className="btn-primary flex items-center gap-2">
              Start investigation
              <ArrowRight size={15} />
            </Link>
            <Link to="/upload" className="btn-ghost">
              Upload documents →
            </Link>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        {STAT_CARDS.map(({ label, icon: Icon, color, bg }, i) => (
          <div key={label} className="card p-5">
            <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-3`}>
              <Icon size={18} className={color} />
            </div>
            <p className="text-2xl font-bold text-white">
              {i === 0 ? docs.length : i === 2 ? docs.filter(d => d.status === "READY").length : 0}
            </p>
            <p className="text-xs text-ink-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div className="card p-6">
        <h2 className="text-sm font-semibold text-white mb-6">How ClueBerry investigates</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          {[
            { step: "01", title: "Upload", desc: "Drop invoices, receipts, reminders", icon: "📂" },
            { step: "02", title: "Extract", desc: "Bedrock pulls structured fields", icon: "🔬" },
            { step: "03", title: "MCP Query", desc: "Tools retrieve & match evidence", icon: "⚡" },
            { step: "04", title: "Cite & Report", desc: "Every claim traced to source", icon: "🫐" },
          ].map(({ step, title, desc, icon }, i) => (
            <div key={step} className="relative flex flex-col gap-3 p-4 rounded-xl bg-white/3 border border-white/5">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{icon}</span>
                <span className="font-mono text-xs text-ink-500">{step}</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{title}</p>
                <p className="text-xs text-ink-400 mt-0.5">{desc}</p>
              </div>
              {i < 3 && (
                <ArrowRight size={14} className="absolute -right-3 top-1/2 -translate-y-1/2 text-ink-600 hidden md:block" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent docs */}
      {docs.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Recent documents</h2>
            <Link to="/upload" className="text-xs text-berry-400 hover:text-berry-300">
              View all →
            </Link>
          </div>
          <div className="space-y-2">
            {docs.slice(0, 4).map((doc) => (
              <div key={doc.document_id} className="card flex items-center gap-3 p-4">
                <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center shrink-0">
                  <FileText size={16} className="text-ink-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{doc.filename}</p>
                  <p className="text-xs text-ink-500 font-mono">{doc.document_id.slice(0, 14)}…</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full border font-mono ${
                  doc.status === "READY" ? "status-ready" :
                  doc.status === "PROCESSING" ? "status-processing" :
                  doc.status === "FAILED" ? "status-failed" : "status-uploaded"
                }`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
