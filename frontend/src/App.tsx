import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import UploadPage from "./pages/UploadPage";
import InvestigatePage from "./pages/InvestigatePage";

export default function App() {
  return (
    <BrowserRouter>
      {/* Noise overlay */}
      <div className="noise-overlay" />

      {/* Grid background */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-100"
        style={{
          backgroundImage: "linear-gradient(rgba(128,64,245,0.06) 1px, transparent 1px), linear-gradient(to right, rgba(128,64,245,0.06) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Gradient orbs */}
      <div className="fixed top-0 right-0 w-[600px] h-[600px] bg-berry-600/5 rounded-full blur-3xl pointer-events-none z-0" />
      <div className="fixed bottom-0 left-16 w-[400px] h-[400px] bg-blue-600/4 rounded-full blur-3xl pointer-events-none z-0" />

      <div className="relative z-10 flex min-h-screen">
        <Sidebar />

        <main className="flex-1 ml-16 lg:ml-56 p-6 lg:p-10 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/investigate" element={<InvestigatePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
