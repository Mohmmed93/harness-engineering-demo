import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Status = "Open" | "In progress" | "Resolved";
type Ticket = {
  id: number;
  title: string;
  customer: string;
  initials: string;
  status: Status;
  priority: "High" | "Medium" | "Low";
  description: string;
  notes: string[];
};
const seed: Ticket[] = [
  {
    id: 1042,
    title: "Unable to download monthly report",
    customer: "Amelia Stone",
    initials: "AS",
    status: "Open",
    priority: "High",
    description:
      "The export button shows a loading indicator, but the monthly report never downloads. Reproduced with the October report.",
    notes: [],
  },
  {
    id: 1041,
    title: "Search results reset the status filter",
    customer: "Oliver Chen",
    initials: "OC",
    status: "In progress",
    priority: "High",
    description:
      "Please verify that searching tickets preserves the selected status and priority filters.",
    notes: [],
  },
  {
    id: 1040,
    title: "Update billing contact details",
    customer: "Maya Patel",
    initials: "MP",
    status: "Open",
    priority: "Medium",
    description:
      "The team needs to change the contact receiving billing notifications.",
    notes: [],
  },
  {
    id: 1039,
    title: "Confirmation email arrived twice",
    customer: "Leo Martin",
    initials: "LM",
    status: "Resolved",
    priority: "Low",
    description:
      "Two confirmation emails were received after a single invitation.",
    notes: [],
  },
  {
    id: 1038,
    title: "Keyboard focus missing on ticket actions",
    customer: "Sofia Reed",
    initials: "SR",
    status: "Open",
    priority: "Medium",
    description:
      "Check that all ticket actions are reachable and visible when navigating by keyboard.",
    notes: [],
  },
  {
    id: 1037,
    title: "Workspace invitation expired",
    customer: "Noah Williams",
    initials: "NW",
    status: "Resolved",
    priority: "Low",
    description:
      "A replacement invitation was requested for a new team member.",
    notes: [],
  },
];
function App() {
  const [tickets, setTickets] = useState<Ticket[]>(structuredClone(seed));
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All statuses");
  const [priority, setPriority] = useState("All priorities");
  const [selected, setSelected] = useState(1042);
  const [note, setNote] = useState("");
  const [failure, setFailure] = useState(false);
  const [message, setMessage] = useState("");
  const ticket = tickets.find((t) => t.id === selected)!;
  const normalizedQuery = query.trim();
  const visible = tickets.filter(
    (t) =>
      (status === "All statuses" || t.status === status) &&
      (priority === "All priorities" || t.priority === priority) &&
      `${t.title} ${t.customer} ${t.id}`
        .toLowerCase()
        .includes(normalizedQuery.toLowerCase()),
  );
  function update(next: Status) {
    if (failure) {
      setMessage("Save failed. Your ticket status has not changed. Try again.");
      return;
    }
    setTickets((ts) =>
      ts.map((t) => (t.id === selected ? { ...t, status: next } : t)),
    );
    setMessage("Ticket status saved.");
  }
  function reset() {
    setTickets(structuredClone(seed));
    setQuery("");
    setStatus("All statuses");
    setPriority("All priorities");
    setSelected(1042);
    setNote("");
    setFailure(false);
    setMessage("Demo data reset.");
  }
  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="./">
          <span className="logo">S</span>signal<span className="dot">●</span>
        </a>
        <div className="workspace">DEMO WORKSPACE</div>
        <div className="nav active">
          ▤ <span>Support inbox</span>
          <b>{tickets.length}</b>
        </div>
        <div className="sidebar-bottom">
          <span className="avatar">HE</span>
          <div>
            Harness engineering<small>Practice environment</small>
          </div>
        </div>
      </aside>
      <main>
        <header>
          <span>
            Workspace <span className="slash">/</span> Support inbox
          </span>
          <span className="demo-tag">● Synthetic data</span>
        </header>
        <div className="heading">
          <div>
            <div className="eyebrow">CUSTOMER OPERATIONS</div>
            <h1>Support inbox</h1>
            <p>A clear view of every issue. A better next step.</p>
          </div>
          <button onClick={reset}>↻ Reset demo</button>
        </div>
        <section className="stats" aria-label="Ticket summary">
          {[
            ["Total tickets", tickets.length],
            ["Open", tickets.filter((t) => t.status === "Open").length],
            [
              "In progress",
              tickets.filter((t) => t.status === "In progress").length,
            ],
            ["Resolved", tickets.filter((t) => t.status === "Resolved").length],
          ].map(([label, count]) => (
            <div className="stat" key={label}>
              <span>{label}</span>
              <strong>
                {count}
                <span className="stat-dot">●</span>
              </strong>
            </div>
          ))}
        </section>
        <div className="content">
          <section className="inbox">
            <div className="section-title">
              <h2>All tickets</h2>
              <span>{visible.length} results</span>
            </div>
            <div className="filters">
              <input
                aria-label="Search tickets"
                placeholder="Search tickets or customers…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <select
                aria-label="Filter by status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {["All statuses", "Open", "In progress", "Resolved"].map(
                  (s) => (
                    <option key={s}>{s}</option>
                  ),
                )}
              </select>
              <select
                aria-label="Filter by priority"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                {["All priorities", "High", "Medium", "Low"].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="tickets">
              {visible.map((t) => (
                <button
                  className={`ticket ${t.id === selected ? "selected" : ""}`}
                  key={t.id}
                  onClick={() => {
                    setSelected(t.id);
                    setNote("");
                    setMessage("");
                  }}
                  aria-pressed={t.id === selected}
                >
                  <div className="ticket-top">
                    <span>#{t.id}</span>
                    <span className={`priority ${t.priority.toLowerCase()}`}>
                      ● {t.priority}
                    </span>
                  </div>
                  <h3>{t.title}</h3>
                  <div className="ticket-bottom">
                    <span>{t.customer}</span>
                    <span
                      className={`badge ${t.status.toLowerCase().replace(" ", "-")}`}
                    >
                      {t.status}
                    </span>
                  </div>
                </button>
              ))}
              {!visible.length && (
                <div className="empty">
                  <h3>No matching tickets</h3>
                  <p>Try another search or adjust your filters.</p>
                </div>
              )}
            </div>
          </section>
          <section className="detail" aria-label="Ticket details">
            <div className="section-title">
              <span>TICKET DETAILS</span>
              <span>#{ticket.id}</span>
            </div>
            <h2>{ticket.title}</h2>
            <div className="customer">
              <span className="avatar">{ticket.initials}</span>
              <div>
                {ticket.customer}
                <small>Demo customer</small>
              </div>
            </div>
            <label className="field">
              Status
              <select
                aria-label="Ticket status"
                value={ticket.status}
                onChange={(e) => update(e.target.value as Status)}
              >
                {["Open", "In progress", "Resolved"].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
            <h4>Description</h4>
            <p className="description">{ticket.description}</p>
            <div className="notes">
              <h4>
                Internal notes <span>{ticket.notes.length}</span>
              </h4>
              {ticket.notes.map((n, i) => (
                <p className="note" key={i}>
                  {n}
                </p>
              ))}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!note.trim()) return;
                  setTickets((ts) =>
                    ts.map((t) =>
                      t.id === selected
                        ? { ...t, notes: [...t.notes, note.trim()] }
                        : t,
                    ),
                  );
                  setNote("");
                  setMessage("Note added.");
                }}
              >
                <textarea
                  aria-label="Internal note"
                  placeholder="Add context for your team…"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
                <button className="primary" disabled={!note.trim()}>
                  Add note
                </button>
              </form>
            </div>
            <p role="status" className="message">
              {message}
            </p>
          </section>
        </div>
        <footer>
          <span>Demo controls · changes reset on reload</span>
          <label>
            <input
              type="checkbox"
              checked={failure}
              onChange={(e) => setFailure(e.target.checked)}
            />{" "}
            Simulate save failure
          </label>
        </footer>
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
