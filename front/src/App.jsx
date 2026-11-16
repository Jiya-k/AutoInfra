import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  Cloud,
  Database,
  Server,
  Play,
  Square,
  RefreshCw,
  Search,
  Plus,
  Trash2,
  X,
  CheckCircle2,
  AlertCircle,
  Menu,
  LayoutDashboard,
  Settings,
  Globe,
  Cpu,
} from "lucide-react";
import "./App.css";

const API = "/api";

function App() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [backendHealth, setBackendHealth] = useState("checking");
  const [databaseHealth, setDatabaseHealth] = useState("checking");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [discoveryResult, setDiscoveryResult] = useState(null);

  const [form, setForm] = useState({
    name: "",
    instance_id: "",
    region: "ap-south-1",
    private_ip: "",
    public_ip: "",
    status: "running",
    operating_system: "Linux/Unix",
  });

  const fetchServers = useCallback(async () => {
    try {
      const response = await fetch(`${API}/servers/`);
      if (!response.ok) throw new Error("Unable to fetch server inventory");

      const data = await response.json();
      setServers(Array.isArray(data) ? data : data.servers || []);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const [backend, database] = await Promise.all([
        fetch(`${API}/health`),
        fetch(`${API}/health/db`),
      ]);

      setBackendHealth(backend.ok ? "healthy" : "unhealthy");
      setDatabaseHealth(database.ok ? "healthy" : "unhealthy");
    } catch {
      setBackendHealth("unhealthy");
      setDatabaseHealth("unhealthy");
    }
  }, []);

  useEffect(() => {
    fetchServers();
    checkHealth();
  }, [fetchServers, checkHealth]);

  const runningCount = servers.filter(
    (server) => server.status?.toLowerCase() === "running"
  ).length;

  const stoppedCount = servers.filter(
    (server) => server.status?.toLowerCase() === "stopped"
  ).length;

  const regionsCount = new Set(
    servers.map((server) => server.region).filter(Boolean)
  ).size;

  const filteredServers = useMemo(() => {
    return servers.filter((server) => {
      const matchesSearch = [
        server.name,
        server.instance_id,
        server.region,
        server.private_ip,
        server.public_ip,
      ]
        .filter(Boolean)
        .some((value) =>
          String(value).toLowerCase().includes(search.toLowerCase())
        );

      const matchesStatus =
        statusFilter === "all" ||
        server.status?.toLowerCase() === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [servers, search, statusFilter]);

  const discoverAWS = async () => {
    setDiscovering(true);
    setError("");
    setNotice("");

    try {
      const response = await fetch(
        `${API}/servers/discover/aws/all-regions`,
        { method: "POST" }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "AWS discovery failed");
      }

      setDiscoveryResult(result);
      setNotice(
        `Discovery completed: ${result.discovered} EC2 instances found across ${result.successful_regions?.length || 0} regions.`
      );

      await fetchServers();
    } catch (err) {
      setError(err.message);
    } finally {
      setDiscovering(false);
    }
  };

  const addServer = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");

    try {
      const response = await fetch(`${API}/servers/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          provider: "AWS",
          instance_id: form.instance_id || null,
          private_ip: form.private_ip || null,
          public_ip: form.public_ip || null,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Unable to add server");
      }

      setShowAddForm(false);
      setForm({
        name: "",
        instance_id: "",
        region: "ap-south-1",
        private_ip: "",
        public_ip: "",
        status: "running",
        operating_system: "Linux/Unix",
      });

      setNotice("Server added successfully.");
      await fetchServers();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteServer = async (id) => {
    if (!window.confirm("Are you sure you want to delete this server?")) {
      return;
    }

    try {
      const response = await fetch(`${API}/servers/${id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.detail || "Unable to delete server");
      }

      setNotice("Server removed from inventory.");
      await fetchServers();
    } catch (err) {
      setError(err.message);
    }
  };

  const healthLabel = (health) => {
    if (health === "healthy") return "Connected";
    if (health === "checking") return "Checking...";
    return "Unavailable";
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Cloud size={23} /></div>
          <div>
            <h2>AutoInfra</h2>
            <span>INFRASTRUCTURE CONTROL</span>
          </div>
        </div>

        <div className="nav-heading">WORKSPACE</div>
        <div className="nav-item active">
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </div>
        <div className="nav-item">
          <Server size={18} />
          <span>Server Inventory</span>
        </div>
        <div className="nav-item">
          <Globe size={18} />
          <span>AWS Discovery</span>
        </div>

        <div className="sidebar-bottom">
          <div className="nav-item">
            <Settings size={18} />
            <span>Settings</span>
          </div>
          <div className="profile">
            <div className="profile-avatar">AI</div>
            <div>
              <strong>AutoInfra Admin</strong>
              <span>AWS Workspace</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="mobile-brand">
            <Menu size={21} />
            <strong>AutoInfra</strong>
          </div>
          <div className="breadcrumb">Workspace <span>/</span> Dashboard</div>
          <div className="topbar-right">
            <span className="environment"><span /> AWS ENVIRONMENT</span>
            <div className="avatar">AI</div>
          </div>
        </header>

        <section className="dashboard">
          <div className="page-heading">
            <div>
              <div className="eyebrow">CLOUD INFRASTRUCTURE</div>
              <h1>Dashboard</h1>
              <p>Monitor and manage your AWS infrastructure from one place.</p>
            </div>
            <div className="heading-actions">
              <button className="button secondary" onClick={() => {
                fetchServers();
                checkHealth();
              }}>
                <RefreshCw size={16} /> Refresh
              </button>
              <button
                className="button primary"
                onClick={discoverAWS}
                disabled={discovering}
              >
                <Cloud size={17} />
                {discovering ? "Discovering..." : "Discover AWS"}
              </button>
            </div>
          </div>

          {error && (
            <div className="alert error">
              <AlertCircle size={18} /> {error}
              <button onClick={() => setError("")}><X size={16} /></button>
            </div>
          )}

          {notice && (
            <div className="alert success">
              <CheckCircle2 size={18} /> {notice}
              <button onClick={() => setNotice("")}><X size={16} /></button>
            </div>
          )}

          <div className="section-title">
            <h3>Infrastructure Overview</h3>
            <span>LIVE INVENTORY</span>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-top">
                <span>Total Servers</span>
                <div className="stat-icon purple"><Server size={19} /></div>
              </div>
              <strong>{servers.length}</strong>
              <small>Registered AWS instances</small>
            </div>

            <div className="stat-card">
              <div className="stat-top">
                <span>Running</span>
                <div className="stat-icon green"><Play size={19} /></div>
              </div>
              <strong>{runningCount}</strong>
              <small>Currently running</small>
            </div>

            <div className="stat-card">
              <div className="stat-top">
                <span>Stopped</span>
                <div className="stat-icon orange"><Square size={19} /></div>
              </div>
              <strong>{stoppedCount}</strong>
              <small>Currently stopped</small>
            </div>

            <div className="stat-card">
              <div className="stat-top">
                <span>Regions Used</span>
                <div className="stat-icon blue"><Globe size={19} /></div>
              </div>
              <strong>{regionsCount}</strong>
              <small>Regions in your inventory</small>
            </div>
          </div>

          <div className="section-title service-heading">
            <h3>Platform Services</h3>
            <span>CONNECTION STATUS</span>
          </div>

          <div className="health-grid">
            <div className="health-card">
              <div className="health-icon"><Activity size={19} /></div>
              <div>
                <strong>Backend API</strong>
                <span className={backendHealth}>{healthLabel(backendHealth)}</span>
              </div>
              <div className={`health-dot ${backendHealth}`} />
            </div>
            <div className="health-card">
              <div className="health-icon"><Database size={19} /></div>
              <div>
                <strong>PostgreSQL Database</strong>
                <span className={databaseHealth}>{healthLabel(databaseHealth)}</span>
              </div>
              <div className={`health-dot ${databaseHealth}`} />
            </div>
            <div className="health-card">
              <div className="health-icon"><Cloud size={19} /></div>
              <div>
                <strong>AWS Discovery</strong>
                <span>EC2 integration</span>
              </div>
              <div className="health-dot healthy" />
            </div>
          </div>

          <section className="inventory-section">
            <div className="inventory-header">
              <div>
                <h3>EC2 Instance Inventory</h3>
                <p>Review and manage your discovered infrastructure.</p>
              </div>
              <button className="button primary" onClick={() => setShowAddForm(true)}>
                <Plus size={17} /> Add Server
              </button>
            </div>

            {discoveryResult && (
              <div className="discovery-summary">
                <Cpu size={18} />
                Last discovery: {discoveryResult.regions_checked} regions checked,
                {" "}{discoveryResult.discovered} instances found,
                {" "}{discoveryResult.failed_regions?.length || 0} region failures.
              </div>
            )}

            <div className="table-toolbar">
              <div className="search-box">
                <Search size={17} />
                <input
                  placeholder="Search by name, ID, IP or region..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All statuses</option>
                <option value="running">Running</option>
                <option value="stopped">Stopped</option>
                <option value="pending">Pending</option>
                <option value="terminated">Terminated</option>
              </select>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>INSTANCE</th>
                    <th>REGION</th>
                    <th>PRIVATE IP</th>
                    <th>PUBLIC IP</th>
                    <th>STATUS</th>
                    <th>OPERATING SYSTEM</th>
                    <th>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan="7" className="empty-state">Loading inventory...</td></tr>
                  ) : filteredServers.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="empty-state">
                        <Cloud size={30} />
                        <strong>No servers found</strong>
                        <span>Run AWS discovery or add a server to populate your inventory.</span>
                      </td>
                    </tr>
                  ) : (
                    filteredServers.map((server) => (
                      <tr key={server.id}>
                        <td>
                          <div className="instance-name">{server.name}</div>
                          <small>{server.instance_id || "No instance ID"}</small>
                        </td>
                        <td>{server.region || "—"}</td>
                        <td>{server.private_ip || "—"}</td>
                        <td>{server.public_ip || "—"}</td>
                        <td>
                          <span className={`status-badge ${server.status?.toLowerCase()}`}>
                            <span /> {server.status}
                          </span>
                        </td>
                        <td>{server.operating_system || "—"}</td>
                        <td>
                          <button
                            className="icon-button danger"
                            title="Delete server"
                            onClick={() => deleteServer(server.id)}
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="table-footer">
              Showing {filteredServers.length} of {servers.length} servers
              <span>AWS EC2 INVENTORY</span>
            </div>
          </section>

          <footer className="footer">
            AutoInfra · AWS Infrastructure Management Platform
            <span>Built for infrastructure visibility and automation</span>
          </footer>
        </section>
      </main>

      {showAddForm && (
        <div className="modal-backdrop" onClick={() => setShowAddForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Add AWS Server</h2>
                <p>Register an instance in your inventory.</p>
              </div>
              <button className="icon-button" onClick={() => setShowAddForm(false)}>
                <X size={19} />
              </button>
            </div>

            <form onSubmit={addServer}>
              <label>Server Name *</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. production-web-server"
              />

              <label>EC2 Instance ID</label>
              <input
                value={form.instance_id}
                onChange={(e) => setForm({ ...form, instance_id: e.target.value })}
                placeholder="i-xxxxxxxxxxxxxxxxx"
              />

              <label>AWS Region *</label>
              <input
                required
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
              />

              <div className="form-row">
                <div>
                  <label>Private IP</label>
                  <input
                    value={form.private_ip}
                    onChange={(e) => setForm({ ...form, private_ip: e.target.value })}
                    placeholder="10.0.0.1"
                  />
                </div>
                <div>
                  <label>Public IP</label>
                  <input
                    value={form.public_ip}
                    onChange={(e) => setForm({ ...form, public_ip: e.target.value })}
                    placeholder="Optional"
                  />
                </div>
              </div>

              <label>Instance Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                <option value="running">Running</option>
                <option value="stopped">Stopped</option>
                <option value="pending">Pending</option>
                <option value="unknown">Unknown</option>
              </select>

              <label>Operating System</label>
              <input
                value={form.operating_system}
                onChange={(e) => setForm({ ...form, operating_system: e.target.value })}
              />

              <div className="modal-actions">
                <button type="button" className="button secondary" onClick={() => setShowAddForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="button primary">
                  <Plus size={16} /> Add to Inventory
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
