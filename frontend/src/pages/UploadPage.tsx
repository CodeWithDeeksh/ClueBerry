import { useEffect, useState } from "react";
import UploadPanel from "../components/UploadPanel";
import { listDocuments, DocumentMeta } from "../services/api";

export default function UploadPage() {
  const [docs, setDocs] = useState<DocumentMeta[]>([]);

  useEffect(() => {
    listDocuments().then(setDocs).catch(() => {});
    const interval = setInterval(() => listDocuments().then(setDocs).catch(() => {}), 4000);
    return () => clearInterval(interval);
  }, []);

  const handleUploaded = (result: { document_id: string; filename: string; status: string }) => {
    setDocs((prev) => [
      { document_id: result.document_id, filename: result.filename, status: "PROCESSING" as const, s3_key: "", document_type: "unknown", upload_timestamp: new Date().toISOString() },
      ...prev.filter(d => d.document_id !== result.document_id),
    ]);
  };

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Upload Documents</h1>
        <p className="text-ink-400 mt-1 text-sm">
          Add invoices, receipts and payment reminders. ClueBerry extracts structured evidence automatically.
        </p>
      </div>
      <UploadPanel onUploaded={handleUploaded} uploadedDocs={docs} />
    </div>
  );
}
