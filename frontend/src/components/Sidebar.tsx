import { NavLink } from "react-router-dom";
import { LayoutDashboard, Upload, Search, FileText, Activity, Grape } from "lucide-react";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/upload", icon: Upload, label: "Upload" },
  { to: "/investigate", icon: Search, label: "Investigate" },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-16 lg:w-56 flex flex-col z-40
                      bg-ink-950/80 backdrop-blur-xl border-r border-white/5">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/5">
        <div className="relative shrink-0">
          <div className="w-8 h-8 rounded-xl bg-berry-600 flex items-center justify-center shadow-berry">
            <Grape size={16} className="text-white" />
          </div>
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-ink-950" />
        </div>
        <div className="hidden lg:block">
          <p className="font-semibold text-sm text-white leading-none">ClueBerry</p>
          <p className="text-xs text-ink-400 mt-0.5">Evidence Investigator</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group
              ${isActive
                ? "bg-berry-600/15 text-berry-300 border border-berry-500/20"
                : "text-ink-400 hover:text-white hover:bg-white/5 border border-transparent"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={18} className={isActive ? "text-berry-400" : "text-ink-500 group-hover:text-ink-300"} />
                <span className="hidden lg:block">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="p-3 border-t border-white/5">
        <div className="hidden lg:flex items-center gap-2 px-3 py-2 rounded-xl bg-white/3">
          <Activity size={14} className="text-berry-400 shrink-0" />
          <span className="text-xs text-ink-400 font-mono">MCP active</span>
        </div>
      </div>
    </aside>
  );
}
