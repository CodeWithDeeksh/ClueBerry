import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, AlertCircle, CheckCircle, Loader2, X, FileCheck } from "lucide-react";
import { uploadDocument, DocumentMeta } from "../services/api";
import clsx from "clsx";

interface Props {
  onUploaded: (doc: { document_id: string; filename: string; status: string }) => void;
  uploadedDocs: DocumentMeta[];
  onRemoveDoc?: (id: string) => void;
}

interface UploadItem {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  document_id?: string;
  error?: string;
}

const ICONS: Record<string, string> = {
  invoice: "🧾",
  receipt: "💳",
  reminder: "🔔",
  email: "📧",
  unknown: "📄",
};

export default function UploadPanel({ onUploaded, uploadedDocs, onRemoveDoc }: Props) {
  const [queue, setQueue] = useState<UploadItem[]>([]);

  const processFile = async (item: UploadItem, idx: number) => {
    setQueue((q) => q.map((i, n) => n === idx ? { ...i, status: "uploading" } : i));
    try {
      const result = await uploadDocument(item.file);
      setQueue((q) => q.map((i, n) => n === idx ? { ...i, status: "done", document_id: result.document_id } : i));
      onUploaded(result);
    } catch {
      setQueue((q) => q.map((i, n) => n === idx ? { ...i, status: "error", error: "Upload failed" } : i));
    }
  };

  const onDrop = useCallback((accepted: File[]) => {
    const start = queue.length;
    const newItems: UploadItem[] = accepted.map((file) => ({ file, status: "pending" }));
    setQueue((q) => [...q, ...newItems]);
    newItems.forEach((item, i) => processFile(item, start + i));
  }, [queue]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "text/plain": [".txt"], "message/rfc822": [".eml"] },
    maxSize: 10 * 1024 * 1024,
  });

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={clsx(
          "relative rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-300",
          isDragActive
            ? "border-berry-400 bg-berry-500/10 shadow-berry"
            : "border-white/10 hover:border-berry-500/40 hover:bg-berry-500/5"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className={clsx(
            "w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300",
            isDragActive ? "bg-berry-500/20 scale-110" : "bg-white/5"
          )}>
            <Upload size={28} className={isDragActive ? "text-berry-400" : "text-ink-400"} />
          </div>
          <div>
            <p className="text-white font-medium">
              {isDragActive ? "Drop to upload" : "Drag documents here"}
            </p>
            <p className="text-ink-400 text-sm mt-1">
              PDF, TXT, EML — up to 10 MB each
            </p>
          </div>
          <button className="btn-primary text-xs px-4 py-2">
            Browse files
          </button>
        </div>

        {isDragActive && (
          <div className="absolute inset-0 rounded-2xl bg-berry-500/5 animate-pulse pointer-events-none" />
        )}
      </div>

      {/* Upload queue */}
      {queue.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-ink-400 uppercase tracking-widest px-1">Uploading</p>
          {queue.map((item, idx) => (
            <div key={idx} className="card flex items-center gap-3 p-3">
              <div className={clsx(
                "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                item.status === "done" ? "bg-emerald-500/10" :
                item.status === "error" ? "bg-red-500/10" :
                item.status === "uploading" ? "bg-berry-500/10" : "bg-white/5"
              )}>
                {item.status === "done" ? <CheckCircle size={16} className="text-emerald-400" /> :
                 item.status === "error" ? <AlertCircle size={16} className="text-red-400" /> :
                 item.status === "uploading" ? <Loader2 size={16} className="text-berry-400 animate-spin" /> :
                 <FileText size={16} className="text-ink-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{item.file.name}</p>
                <p className="text-xs text-ink-500">
                  {item.status === "done" ? "Uploaded — extracting evidence…" :
                   item.status === "error" ? item.error :
                   item.status === "uploading" ? "Uploading…" : "Queued"}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Uploaded documents list */}
      {uploadedDocs.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-ink-400 uppercase tracking-widest px-1">Documents in session</p>
          {uploadedDocs.map((doc) => (
            <div key={doc.document_id} className="card flex items-center gap-3 p-3 group">
              <span className="text-xl shrink-0">{ICONS[doc.document_type] || "📄"}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{doc.filename}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className={clsx(
                    "text-xs px-2 py-0.5 rounded-full border font-mono",
                    doc.status === "READY" ? "status-ready" :
                    doc.status === "PROCESSING" ? "status-processing" :
                    doc.status === "FAILED" ? "status-failed" : "status-uploaded"
                  )}>
                    {doc.status}
                  </span>
                  <span className="text-xs text-ink-500 font-mono">{doc.document_id.slice(0, 12)}…</span>
                </div>
              </div>
              {doc.status === "PROCESSING" && (
                <Loader2 size={14} className="text-berry-400 animate-spin shrink-0" />
              )}
              {doc.status === "READY" && (
                <FileCheck size={14} className="text-emerald-400 shrink-0" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
