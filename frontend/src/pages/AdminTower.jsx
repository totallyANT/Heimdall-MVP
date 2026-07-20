import { useState, useEffect } from 'react';

const API = import.meta.env.VITE_MAIN_BACKEND_URL || "http://127.0.0.1:8000";

export default function AdminTower({ onLogout }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const user = JSON.parse(sessionStorage.getItem("user"));
  const adminId = user?.admin?.id;
  
  const [currentAdmin, setCurrentAdmin] = useState({
    name: user?.admin?.full_name || "System Administrator",
    badgeId: adminId || "ADM-???",
    role: "System Administrator"
  });

  const [provTab, setProvTab] = useState('resident');
  const [numResidents, setNumResidents] = useState(1);
  const [flatNum, setFlatNum] = useState('');
  const [badges, setBadges] = useState(['']);
  const [numSec, setNumSec] = useState(1);
  const [directoryRoleFilter, setDirectoryRoleFilter] = useState("All");
  const [generatedCreds, setGeneratedCreds] = useState(null);
  const [broadcastTitle, setBroadcastTitle] = useState('');
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState([]);
  
  // Guard assignment selection tracker
  const [selectedGuardForAlert, setSelectedGuardForAlert] = useState({});

  const loadDashboard = async () => {
    try {
      const alertsResponse = await fetch(`${API}/alerts/admin`);
      if (!alertsResponse.ok) throw new Error("Alerts fetch error");
      const alertsData = await alertsResponse.json();
      setAlerts(Array.isArray(alertsData) ? alertsData : []);

      const profileResponse = await fetch(`${API}/profile/admin/${adminId}`);
      if (profileResponse.ok) {
        const adminData = await profileResponse.json();
        if (adminData) {
          setCurrentAdmin({
            name: adminData.full_name || "System Administrator",
            badgeId: adminData.id || adminId,
            role: "System Administrator"
          });
        }
      }
      setError("");
    } catch (err) {
      console.error(err);
      setError("Unable to sync live dashboard alerts queue.");
    } finally {
      setLoading(false);
    }
  };

  const fetchDirectory = async () => {
    try {
      const response = await fetch(`${API}/admin/directory/community-directory`);
      if (!response.ok) throw new Error("Directory sync failure");
      const data = await response.json();

      const formatted = (Array.isArray(data) ? data : []).map((item) => ({
        id: item.id,
        name: item.name,
        role: item.role,
        score: item.score,
        status: item.status,
        isInitialized: item.status === "Active", 
        color: item.score >= 80 ? "text-emerald-400" : "text-yellow-400",
        roleColor: item.role === "Resident"
            ? "bg-gray-800 border border-gray-700 text-gray-300"
            : "bg-blue-900/30 text-blue-400 border border-blue-800/50",
      }));

      setUsers(formatted);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadDashboard();
    fetchDirectory();

    const interval = setInterval(() => {
      loadDashboard();
      fetchDirectory();
    }, 3000);

    return () => clearInterval(interval);
  }, [adminId]);

  const filteredUsers = users.filter((u) => {
    const name = (u.name || "").toLowerCase();
    const id = (u.id || "").toLowerCase();
    const query = searchQuery.toLowerCase();

    const matchesSearch = name.includes(query) || id.includes(query);
    const matchesFilter = directoryRoleFilter === "All" || u.role === directoryRoleFilter;

    return matchesSearch && matchesFilter;
  });

  const handleNumResidentsChange = (e) => {
    const num = parseInt(e.target.value) || 1;
    setNumResidents(num);
    const newBadges = [...badges];
    while (newBadges.length < num) newBadges.push('');
    setBadges(newBadges.slice(0, num));
  };

  const handleBadgeChange = (index, value) => {
    const newBadges = [...badges];
    newBadges[index] = value;
    setBadges(newBadges);
  };

  const handleProvision = async (e) => {
    e.preventDefault();
    setGeneratedCreds(null);

    try {
      let response;
      if (provTab === "resident") {
        response = await fetch(`${API}/admin/generate-identities`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            number_of_residents: numResidents,
            flat_number: flatNum,
            resident_badge_ids: badges,
          }),
        });
      } else {
        response = await fetch(`${API}/admin/generate-security-guards`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            number_of_new_guards: numSec,
          }),
        });
      }

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Provision process failed");

      const creds = data.map((item) => ({
        role: item.Resident || item.Security,
        id: item.ID,
        tempPwd: item.Password,
        flat: item.Flat || "N/A",
        badge: item.Badge || "N/A",
      }));

      setGeneratedCreds(creds);
      setFlatNum('');
      setBadges(['']);
      setNumResidents(1);
      fetchDirectory();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleBroadcast = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/announcement/send-announcement`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: broadcastTitle, message: broadcastMsg }),
      });
      if (!response.ok) throw new Error("Global notification failed");
      alert("Announcement transmitted successfully to all active portals!");
      setBroadcastTitle("");
      setBroadcastMsg("");
    } catch (err) {
      console.error(err);
      alert("Failed to deliver emergency broadcast request.");
    }
  };

  const handleRemoveUserDirect = async (targetUser) => {
    const confirmDelete = window.confirm(`Are you absolutely sure you want to completely revoke ${targetUser.name}'s system credentials?`);
    if (!confirmDelete) return;

    try {
      const endpoint = targetUser.role === "Resident"
          ? `${API}/admin/directory/resident/${targetUser.id}`
          : `${API}/admin/directory/guard/${targetUser.id}`;

      const response = await fetch(endpoint, { method: "DELETE" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Revocation request refused");

      alert(data.message || "User credentials revoked.");
      setUsers(prev => prev.filter(u => u.id !== targetUser.id));
    } catch (err) {
      console.error(err);
      alert(err.message);
    }
  };

  const handleAssignGuard = async (alertId) => {
    const guardId = selectedGuardForAlert[alertId];
    if (!guardId) {
      alert("Please select an active guard station from the picker dropdown layout first.");
      return;
    }

    try {
      const response = await fetch(`${API}/alerts/${alertId}/assign/${guardId}`, { method: "POST" });
      if (!response.ok) throw new Error("Guard deployment route execution failed");
      
      alert(`Threat case successfully dispatched to ${guardId}.`);
      await loadDashboard();
    } catch (err) {
      console.error(err);
      alert("Unable to complete security dispatch route mapping.");
    }
  };

  const availableGuards = users.filter(u => u.role === "Security" && u.status === "Active");

  return (
    <div className="min-h-screen font-sans text-gray-200 transition-colors duration-500 overflow-x-hidden w-full pb-10 bg-gray-950">
      <nav className="bg-gray-900 border-b border-purple-900/50 px-6 py-4 flex justify-between items-center sticky top-0 z-40">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-bold tracking-widest text-white animate-pulse">HEIMDALL</span>
          <span className="px-2 py-0.5 bg-purple-900/40 text-purple-400 border border-purple-800 rounded text-xs font-mono font-bold hidden sm:inline-block">ADMIN PORTAL</span>
        </div>
        <button onClick={onLogout} className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 text-red-400 px-4 py-2 rounded-lg transition">Sign Out</button>
      </nav>

      <main className="p-6 max-w-7xl mx-auto space-y-6">
 {/* Top Analytics Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-900 p-5 rounded-xl border border-red-900/60 shadow-md">
            <span className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">High Severity Alerts</span>
            <div className="text-3xl font-extrabold text-red-400 mt-2 font-mono">
              {alerts.filter(a => a.severity === "High" && a.status !== "RESOLVED" && a.status !== "DISMISSED").length}
            </div>
            <p className="text-xs text-gray-500 mt-2">Awaiting Guard Dispatch</p>
          </div>

          <div className="bg-gray-900 p-5 rounded-xl border border-yellow-900/60 shadow-md">
            <span className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Open Investigations</span>
            <div className="text-3xl font-extrabold text-yellow-400 mt-2 font-mono">
              {alerts.filter(a => a.status !== "RESOLVED" && a.status !== "DISMISSED").length}
            </div>
            <p className="text-xs text-gray-500 mt-2">Active Property Threats</p>
          </div>

          <div className="bg-gray-900 p-5 rounded-xl border border-green-900/60 shadow-md">
            <span className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Resolved Alerts</span>
            <div className="text-3xl font-extrabold text-emerald-400 mt-2 font-mono">
              {/* Fallback check: reads the total database metrics array or active registry logs count */}
              {users.filter(u => u.role === "Security" && u.status === "Active").length + alerts.filter(a => a.status === "RESOLVED" || a.status === "DISMISSED" || a.resolved === true).length}
            </div>
            <p className="text-xs text-gray-500 mt-2">Closed & Dismissed Logs</p>
          </div>

          <div className="bg-gray-900 p-5 rounded-xl border border-purple-900/60 shadow-md">
            <span className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Session Operator</span>
            <div className="text-sm font-bold text-purple-300 mt-2 font-sans truncate">
              {currentAdmin?.name}
            </div>
            <p className="text-xs text-gray-500 font-mono mt-2">{currentAdmin?.badgeId} • Active</p>
          </div>
        </div>

        {/* Threat Queue Cards Section */}
        <div className="w-full">
          <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col w-full shadow-xl">
            <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-950/20">
              <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Security Threat Queue</h2>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-red-950 text-red-400 border border-red-900/40">
                {alerts.filter(a => a.severity === "High" && a.status !== a.resolved && a.status !== a.dismissed).length} Unassigned High Alert(s)
              </span>
            </div>

            <div className="p-4 space-y-4 overflow-y-auto max-h-[650px]" style={{ scrollbarWidth: 'thin' }}>
              {loading ? (
                <div className="flex justify-center items-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div></div>
              ) : error ? (
                <div className="text-center py-10 text-red-400 font-mono text-sm">{error}</div>
              ) : alerts.filter(a => a.severity === "High" && a.status !== a.resolved && a.status !== a.dismissed).length === 0 ? (
                <div className="text-center py-16">
                  <p className="text-emerald-400 font-semibold font-sans text-sm">✓ All high-priority operational targets secure.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                  {alerts.filter(a => a.severity === "High" && a.status !== a.resolved && a.status !== a.dismissed)
                    .map((alert) => (
                      <div key={alert._id} className="bg-gray-950 border border-red-900/40 rounded-xl p-5 flex flex-col justify-between transition hover:border-red-900">
                        <div>
                          <div className="flex justify-between items-center">
                            <span className="bg-red-950 border border-red-800 text-red-400 text-[10px] font-extrabold px-2 py-0.5 rounded tracking-wide uppercase">HIGH</span>
                          </div>
                          <h3 className="text-base font-bold text-white mt-3 font-sans">{alert.signal_type}</h3>
                          <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">{alert.summary}</p>
                          <div className="mt-3 bg-blue-950/20 border-l-2 border-blue-600 p-2.5 rounded text-[11px] text-blue-300">
                            <strong>Recommended Action:</strong> {alert.recommended_action}
                          </div>
                        </div>

                        <div className="mt-5 pt-3 border-t border-gray-900 flex flex-col sm:flex-row gap-3 items-end sm:items-center">
                          <div className="w-full">
                            <label className="block text-[10px] uppercase font-bold text-gray-500 mb-1">Select Security Guard</label>
                            <select 
                              value={selectedGuardForAlert[alert._id] || ""}
                              onChange={(e) => setSelectedGuardForAlert(prev => ({ ...prev, [alert._id]: e.target.value }))}
                              className="w-full bg-gray-900 text-xs text-white border border-gray-800 rounded px-2.5 py-1.5 focus:outline-none focus:border-purple-500 font-sans"
                            >
                              <option value="">-- Choose Active Guard --</option>
                              {availableGuards.map(g => (
                                <option key={g.id} value={g.id}>{g.name} ({g.id})</option>
                              ))}
                            </select>
                          </div>
                          
                          <button 
                            onClick={() => handleAssignGuard(alert._id)} 
                            className="w-full sm:w-auto bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition h-[32px] shadow whitespace-nowrap"
                          >
                            Dispatch
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Priority Broadcast */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg flex flex-col">
            <div className="flex items-center space-x-2 mb-2 border-b border-gray-800 pb-2">
              <span className="h-2 w-2 rounded-full bg-purple-500 animate-ping" />
              <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Priority Broadcast Transmission</h2>
            </div>
            <form onSubmit={handleBroadcast} className="space-y-4 flex-1 flex flex-col mt-2">
              <div>
                <label className="block text-[10px] font-bold uppercase text-gray-500 mb-1">Broadcast Title</label>
                <input type="text" required value={broadcastTitle} onChange={(e) => setBroadcastTitle(e.target.value)} placeholder="Ex: Maintenance Shutdown Notice" className="w-full px-3 py-1.5 bg-gray-950 border border-gray-800 rounded-lg text-white text-xs focus:outline-none focus:border-purple-500 transition font-sans" />
              </div>
              <div className="flex-1 flex flex-col">
                <label className="block text-[10px] font-bold uppercase text-gray-500 mb-1">Message Content</label>
                <textarea required value={broadcastMsg} onChange={(e) => setBroadcastMsg(e.target.value)} placeholder="Type global community notification message data payload..." className="w-full flex-1 min-h-[120px] px-3 py-2 bg-gray-950 border border-gray-800 rounded-lg text-white text-xs focus:outline-none focus:border-purple-500 transition resize-none font-sans" />
              </div>
              <button type="submit" className="w-full bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold py-2 rounded-lg transition shadow-md mt-4">Transmit Global Broadcast</button>
            </form>
          </div>

          {/* Provisioning Engine */}
          <div className="lg:col-span-2 bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg flex flex-col">
            <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 border-b border-gray-800 pb-2">Identity Provisioning Engine</h2>
            <div className="flex border-b border-gray-800 mb-4 bg-gray-950/40 p-0.5 rounded-t-lg">
              <button onClick={() => { setProvTab('resident'); setGeneratedCreds(null); }} className={`flex-1 text-center py-2 text-xs font-bold transition-all ${provTab === 'resident' ? 'text-blue-400 border-b-2 border-blue-400 bg-gray-900/50' : 'text-gray-500 hover:text-gray-300'}`}>Add Resident Accounts</button>
              <button onClick={() => { setProvTab('security'); setGeneratedCreds(null); }} className={`flex-1 text-center py-2 text-xs font-bold transition-all ${provTab === 'security' ? 'text-emerald-400 border-b-2 border-emerald-400 bg-gray-900/50' : 'text-gray-500 hover:text-gray-300'}`}>Add Guard Accounts</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
              <form onSubmit={handleProvision} className="space-y-4 flex flex-col justify-between">
                {provTab === 'resident' ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[10px] uppercase font-bold text-gray-500 mb-1">Count</label>
                        <input type="number" min="1" max="10" value={numResidents} onChange={handleNumResidentsChange} required className="w-full px-2 py-1 bg-gray-950 border border-gray-800 rounded text-white text-xs focus:outline-none focus:border-blue-500 font-mono" />
                      </div>
                      <div>
                        <label className="block text-[10px] uppercase font-bold text-gray-500 mb-1">Flat Number</label>
                        <input type="text" placeholder="Ex: B-204" value={flatNum} onChange={(e) => setFlatNum(e.target.value)} required className="w-full px-2 py-1 bg-gray-950 border border-gray-800 rounded text-white text-xs focus:outline-none focus:border-blue-500 font-mono" />
                      </div>
                    </div>
                    <div className="space-y-2 max-h-36 overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin' }}>
                      {badges.map((badge, idx) => (
                        <div key={idx} className="flex gap-2 items-center">
                          <span className="text-[10px] font-mono text-gray-500 w-8">#{idx+1}:</span>
                          <input type="text" placeholder="Enter Badge ID..." value={badge} onChange={(e) => handleBadgeChange(idx, e.target.value)} required className="w-full px-2 py-1 bg-gray-950 border border-gray-800 rounded text-white text-xs focus:outline-none focus:border-blue-500 font-mono" />
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-500 mb-1">Number of Guard Access Profiles</label>
                    <input type="number" min="1" max="20" value={numSec} onChange={(e) => setNumSec(parseInt(e.target.value) || 1)} required className="w-full px-2 py-1 bg-gray-950 border border-gray-800 rounded text-white text-xs focus:outline-none focus:border-emerald-500 font-mono" />
                  </div>
                )}
                <button type="submit" className={`w-full text-white text-xs font-bold py-2 rounded-lg transition shadow-md mt-auto ${provTab === 'resident' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-emerald-600 hover:bg-emerald-700'}`}>
                  Execute Generation Sequence
                </button>
              </form>

              <div className="bg-gray-950 border border-gray-800 rounded-lg p-3 flex flex-col max-h-[220px]">
                <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 border-b border-gray-900 pb-1">Account Credentials</h3>
                {!generatedCreds ? (
                  <div className="flex-1 flex items-center justify-center text-xs text-gray-600 italic text-center">Generate to view credentials</div>
                ) : (
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1" style={{ scrollbarWidth: 'thin' }}>
                    {generatedCreds.map((cred, idx) => (
                      <div key={idx} className="bg-gray-900 border border-gray-800 p-2 rounded text-[11px] font-mono leading-tight">
                        <div className="flex justify-between text-gray-400">
                          <span className={cred.role === 'Resident' ? 'text-blue-400' : 'text-emerald-400'}>{cred.role}</span>
                          <span>UID: <strong className="text-white">{cred.id}</strong></span>
                        </div>
                        <div className="flex justify-between text-gray-500 text-[10px] mt-1">
                          <span>TempPass: <strong className="text-yellow-400">{cred.tempPwd}</strong></span>
                          {cred.flat !== 'N/A' && <span>Flat: {cred.flat}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col mt-6 shadow-xl">
          <div className="p-4 border-b border-gray-800 flex justify-between items-center flex-wrap gap-3 bg-gray-950/10">
            <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Community Directory</h2>
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              <div className="flex space-x-1 p-0.5 bg-gray-950 rounded border border-gray-800">
                {['All', 'Resident', 'Security'].map(filterRole => (
                  <button key={filterRole} onClick={() => setDirectoryRoleFilter(filterRole)} className={`px-2.5 py-1 text-[10px] rounded font-bold transition-all ${directoryRoleFilter === filterRole ? 'bg-purple-600 text-white' : 'text-gray-500 hover:text-gray-300'}`}>
                    {filterRole === 'All' ? 'ALL ENTITIES' : filterRole === 'Resident' ? 'RESIDENTS' : 'GUARDS'}
                  </button>
                ))}
              </div>
              <div className="relative flex-1 sm:flex-initial">
                <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search ID, name, flat..." className="pl-8 pr-3 py-1 bg-gray-950 border border-gray-800 rounded text-xs text-white focus:outline-none focus:border-purple-500 w-full sm:w-48 transition placeholder-gray-700 font-sans" />
                <span className="absolute left-2.5 top-1.5 text-gray-600 text-xs">🔍</span>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto overflow-y-auto max-h-[400px]" style={{ scrollbarWidth: 'thin' }}>
            <table className="w-full text-left text-xs text-gray-300 min-w-[600px]">
              <thead className="text-[10px] text-gray-500 uppercase border-b border-gray-800 bg-gray-950 sticky top-0 z-10">
                <tr>
                  <th className="py-2.5 px-4 font-bold bg-gray-900">User Profile</th>
                  <th className="py-2.5 px-4 font-bold bg-gray-900">Role</th>
                  <th className="py-2.5 px-4 font-bold bg-gray-900">Status</th>
                  <th className="py-2.5 px-4 font-bold bg-gray-900">Trust Score</th>
                  <th className="py-2.5 px-4 font-bold text-right bg-gray-900">Action</th>
                </tr>
              </thead>
              <tbody className="font-mono text-[11px] divide-y divide-gray-800">
                {filteredUsers.length > 0 ? filteredUsers.map((u) => (
                  <tr key={`${u.role}-${u.id}`} className="hover:bg-gray-800/40 transition">
                    <td className="px-4 py-3">
                      <p className="text-white font-bold font-sans text-xs">{u.name}</p>
                      <p className="text-gray-500 text-[10px]">{u.id}</p>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase ${u.roleColor}`}>{u.role}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-sans font-medium uppercase ${u.isInitialized ? 'bg-emerald-950 text-emerald-400 border border-emerald-900/40' : 'bg-amber-950 text-yellow-500 border border-amber-900/40'}`}>
                        {u.isInitialized ? 'Active' : 'Pending Activation'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`font-bold font-mono ${u.color}`}>{u.score === 0 ? '0 (BLACKLIST)' : `${u.score}`}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button onClick={() => handleRemoveUserDirect(u)} className="bg-red-950/40 hover:bg-red-900/60 border border-red-900 text-red-400 hover:text-red-300 text-[10px] font-bold px-3 py-1 rounded transition font-sans">
                        Revoke
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="5" className="text-center py-8 text-gray-600 font-sans italic">No registry matching details logged under string criteria.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}