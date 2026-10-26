"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Flag,
  Gauge,
  LogOut,
  Menu,
  RadioTower,
  Shield,
  Timer,
  Users,
  Database,
  Building2,
  MapPinned,
  Trophy,
  X,
  type LucideIcon,
} from "lucide-react";
import { useAuth } from "./auth";
import { useEffect } from "react";
import { useNavigationDrawer } from "../lib/use-navigation-drawer";
import { useRaceControlFeed } from "../lib/use-race-control-feed";
import { raceControlItems } from "../lib/race-control-items";
import { ShellFeedStatus, ShellRaceControl } from "./shell-feed";

type NavItem = [href: string, name: string, icon: LucideIcon];
interface NavGroup {
  name: string;
  items: NavItem[];
}

const groups: NavGroup[] = [
  {
    name: "RACE CONTROL",
    items: [
      ["/dashboard", "Overview", Gauge],
      ["/live", "Live timing", RadioTower],
      ["/sessions", "Sessions", Timer],
      ["/stewards", "Steward desk", Shield],
      ["/pit-wall", "Pit wall", Activity],
    ],
  },
  {
    name: "CHAMPIONSHIP",
    items: [
      ["/championships", "Championships", Trophy],
      ["/events", "Race calendar", Flag],
      ["/circuits", "Circuits", MapPinned],
      ["/standings", "Standings", BarChart3],
    ],
  },
  {
    name: "PEOPLE & TEAMS",
    items: [
      ["/teams", "Teams", Building2],
      ["/drivers", "Drivers", Users],
      ["/users", "Users", Users],
      ["/analytics", "Driver analytics", BarChart3],
    ],
  },
  { name: "PLATFORM", items: [["/dbms", "DBMS operations", Database]] },
];
export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname(),
    router = useRouter(),
    { user, ready, logout } = useAuth(),
    {
      open,
      setOpen,
      close,
      isMobile,
      drawerRef,
      backgroundRef,
      menuButtonRef,
    } = useNavigationDrawer(Boolean(user && ready));
  const feed = useRaceControlFeed(Boolean(user && ready));
  useEffect(() => {
    if (!ready) return;
    if (!user && path !== "/" && path !== "/login") router.replace("/login");
    if (user && path === "/login") router.replace("/dashboard");
  }, [path, ready, router, user]);
  if (!ready || (user && path === "/login"))
    return (
      <main className="loading-screen" id="main-content" tabIndex={-1}>
        APEXGRID <span>Checking session…</span>
      </main>
    );
  if (!user) {
    if (path === "/" || path === "/login") return <main id="main-content" tabIndex={-1}>{children}</main>;
    return (
      <main className="loading-screen" id="main-content" tabIndex={-1}>
        APEXGRID <span>Redirecting to sign in…</span>
      </main>
    );
  }
  return (
    <div className="app-shell nb-shell">
      <aside
        ref={drawerRef}
        className={`sidebar ${open ? "show" : ""}`}
        role={isMobile ? "dialog" : "complementary"}
        aria-modal={isMobile && open ? true : undefined}
        aria-hidden={isMobile && !open ? true : undefined}
        aria-label="Main navigation"
      >
        <div className="brand">
          <span className="brand-mark">AG</span>
          <div>
            <b>APEXGRID</b>
            <small>RACE OPERATIONS</small>
          </div>
          <button className="close-nav" aria-label="Close navigation" aria-expanded={open} aria-controls="primary-navigation" onClick={close}>
            <X size={18} />
          </button>
        </div>
        <div className="season">
          <span className="status-dot" /> LIVE ENVIRONMENT{" "}
          <ChevronDown size={13} />
        </div>
        <nav id="primary-navigation" aria-label="Primary navigation">
          {groups
            .filter((g) => g.name !== "PLATFORM" || user.role === "ADMIN")
            .map((g) => (
              <div className="nav-group" key={g.name}>
                <div className="nav-label">{g.name}</div>
                {g.items
                  .filter(
                    ([href]) => href !== "/users" || user.role === "ADMIN",
                  )
                  .map(([href, name, Icon]) => (
                    <Link
                      onClick={close}
                      href={href}
                      className={`nav-item nb-plinth ${path === href ? "active" : ""}`}
                      aria-current={path === href ? "page" : undefined}
                      key={href}
                    >
                      <span className="nb-face">
                        <Icon size={16} />
                        <span>{name}</span>
                        {path === href && (
                          <ChevronRight className="nav-current" size={14} />
                        )}
                      </span>
                    </Link>
                  ))}
              </div>
            ))}
        </nav>
        <div className="side-bottom">
          <div className="user-tile">
            <div className="avatar">{user.full_name?.slice(0, 1) || "U"}</div>
            <div className="user-info">
              <b>{user.full_name}</b>
              <small>{user.role}</small>
            </div>
            <button aria-label="Sign out" onClick={logout}>
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>
      <div
        ref={backgroundRef}
        className="main-shell"
      >
        <header className="topbar">
          <button ref={menuButtonRef} className="mobile-menu" aria-label="Open navigation" aria-expanded={open} aria-controls="primary-navigation" onClick={() => setOpen(true)}>
            <Menu />
          </button>
          <div className="crumb">
            APEXGRID <span>/</span>{" "}
            {path.split("/")[1]?.replaceAll("-", " ").toUpperCase() ||
              "OVERVIEW"}
          </div>
          <div className="top-meta">
            <span className="season-sticker">2026 SEASON</span>
            <span className="system-status"><ShellFeedStatus connection={feed.connection} error={feed.error} onRefresh={feed.refresh} /></span>
            <span className="divider" />
            <span className="header-role">{user.role}</span>
          </div>
        </header>
        <ShellRaceControl items={raceControlItems(feed.data)} status={feed.status} error={feed.error} onRefresh={feed.refresh} />
        <main
          className="content"
          id="main-content"
          tabIndex={-1}
          aria-hidden={isMobile && open ? true : undefined}
          inert={isMobile && open ? true : undefined}
        >
          {children}
        </main>
        <footer className="footer">
          <span>APEXGRID MOTORSPORT OPERATIONS</span>
          <span>CONTROL SYSTEM · BUILD 1.0</span>
        </footer>
      </div>
      {open && (
        <button
          className="mobile-scrim"
          onClick={close}
          aria-label="Close navigation"
          style={{ left: "min(264px, calc(100vw - 32px))" }}
        />
      )}
    </div>
  );
}
