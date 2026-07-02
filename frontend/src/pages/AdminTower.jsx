import { useState,useEffect } from 'react';
const API = "http://127.0.0.1:8000";

export default function AdminTower({ onLogout }) {
  const [lockdown, setLockdown] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const user = JSON.parse(localStorage.getItem("user"));
  const adminId = user?.admin?.id;
  const [currentAdmin, setCurrentAdmin] = useState(null);
  const [provTab, setProvTab] = useState('resident'); 
  const [numResidents, setNumResidents] = useState(1);
  const [flatNum, setFlatNum] = useState('');
  const [badges, setBadges] = useState(['']);
  const [numSec, setNumSec] = useState(1);
  const [directoryRoleFilter, setDirectoryRoleFilter] = useState("All");
  const [generatedCreds, setGeneratedCreds] = useState(null);
  const [broadcastTitle, setBroadcastTitle] = useState(''); 
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [broadcastSent, setBroadcastSent] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState([]);
   

  const loadDashboard = async () => {

    try {

        const alertsResponse = await fetch(
            "http://127.0.0.1:8000/alerts/admin"
        );

        const alertsData = await alertsResponse.json();

        setAlerts(alertsData);

        const profileResponse = await fetch(
            `http://127.0.0.1:8000/profile/admin/${adminId}`
        );

        const admin = await profileResponse.json();

        setCurrentAdmin({

            name: admin.full_name,

            badgeId: admin.id,

            role: "System Administrator"

        });

    }

    catch (err) {

        console.error(err);

        setError("Unable to load dashboard.");

    }

    finally {

        setLoading(false);

    }

  };
  const fetchDirectory = async () => {
    try {
        const response = await fetch(
            "http://127.0.0.1:8000/community/community-directory"
        );

        const data = await response.json();

        console.log("Community Data:", data);

        const formatted = data.map((item) => ({
            id: item.id,
            name: item.name,
            role: item.role,
            score: item.score,
            status: item.status,
            isInitialized: item.is_initialized,
            color: item.score >= 80 ? "text-emerald-400" : "text-yellow-400",
            roleColor:
                item.role === "Resident"
                    ? "bg-gray-800"
                    : "bg-blue-900/30 text-blue-400 border border-blue-800/50",
        }));

        console.log("Formatted:", formatted);

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

}, []);

  const filteredUsers = users.filter((u) => {
    const name = (u.name || "").toLowerCase();
    const id = (u.id || "").toLowerCase();
    const query = searchQuery.toLowerCase();

    const matchesSearch =
        name.includes(query) ||
        id.includes(query);

    const matchesFilter =
        directoryRoleFilter === "All" ||
        u.role === directoryRoleFilter;

    return matchesSearch && matchesFilter;
});


  const handleNumResidentsChange = (e) => {
    const num = parseInt(e.target.value) || 1;
    setNumResidents(num);
    const newBadges = [...badges];
    while(newBadges.length < num) newBadges.push('');
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
        response = await fetch(`${API}/resident/generate-identities`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            number_of_residents: numResidents,
            flat_number: flatNum,
            resident_badge_ids: badges,
          }),
        });
      } else {
       response = await fetch(
    `${API}/security/generate-security-guards`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            number_of_new_guards: numSec,
          }),
        });
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Provision failed");
      }

      const creds = data.map((item) => ({
        role: item.Resident || item.Security,
        id: item.ID,
        tempPwd: item.Password,
        flat: item.Flat || "N/A",
        badge: item.Badge || "N/A",
      }));

      setGeneratedCreds(creds);
      fetchDirectory();

    } catch (err) {
      alert(err.message);
    }
  };

  const handleBroadcast = async (e) => {
    e.preventDefault();

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/announcement/send-announcement",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    title: broadcastTitle,
                    message: broadcastMsg,
                }),
            }
        );

        if (!response.ok) {
            throw new Error("Failed to send announcement");
        }

        alert("Announcement sent successfully!");

        setBroadcastTitle("");
        setBroadcastMsg("");

    } catch (err) {
        console.error(err);
        alert("Failed to send announcement");
    }
};
const handleRemoveUserDirect = async (user) => {

    const confirmDelete = window.confirm(
        `Are you sure you want to revoke ${user.name}?`
    );

    if (!confirmDelete) return;

    try {

        const endpoint =
            user.role === "Resident"
                ? `http://127.0.0.1:8000/community/resident/${user.id}`
                : `http://127.0.0.1:8000/community/guard/${user.id}`;

        const response = await fetch(endpoint, {
            method: "DELETE",
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to revoke user");
        }

        alert(data.message);

        // Remove from UI immediately
        setUsers(prev => prev.filter(u => u.id !== user.id));

        // OR reload from backend
        // fetchDirectory();

    } catch (err) {
        console.error(err);
        alert(err.message);
    }
};
  return (
    <div className={`min-h-screen font-sans text-gray-200 transition-colors duration-500 overflow-x-hidden w-full pb-10 ${lockdown ? 'bg-red-950/90' : 'bg-gray-950'}`}>
      <nav className="bg-gray-900 border-b border-purple-900/50 px-6 py-4 flex justify-between items-center sticky top-0 z-40">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-bold tracking-widest text-white">HEIMDALL</span>
          <span className="px-2 py-0.5 bg-purple-900/40 text-purple-400 border border-purple-800 rounded text-xs font-mono font-bold hidden sm:inline-block">ADMIN PORTAL</span>
        </div>
        <div className="flex items-center space-x-3 bg-gray-950/60 border border-gray-800 rounded-lg px-3 py-1.5 hidden sm:flex">

          <div className="h-8 w-8 rounded-full bg-purple-900/40 border border-purple-800 flex items-center justify-center text-sm font-bold text-purple-400">
              {currentAdmin?.name?.charAt(0) || "A"}
          </div>

          <div>
              <p className="text-sm font-bold text-white">
                  {currentAdmin?.name || "Loading..."}
              </p>

              <p className="text-xs text-gray-500">
                  {currentAdmin?.badgeId}
              </p>
          </div>
        </div>
        <button onClick={onLogout} className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 text-red-400 px-4 py-2 rounded-lg transition">Sign Out</button>
      </nav>

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Top Analytics Metrics Cards Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

        {/* High Alerts */}

        <div className="bg-gray-900 p-5 rounded-xl border border-red-900">

          <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">
            High Alerts
          </span>

          <div className="text-3xl font-bold text-red-400 mt-2">
            {alerts.filter(a => a.severity === "High" && !a.resolved).length}
          </div>

          <p className="text-xs text-gray-500 mt-2">
            Awaiting Admin Action
          </p>

        </div>

        {/* Open Incidents */}

        <div className="bg-gray-900 p-5 rounded-xl border border-yellow-900">

          <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">
            Open Incidents
          </span>

          <div className="text-3xl font-bold text-yellow-400 mt-2">
            {alerts.filter(a => !a.resolved).length}
          </div>

          <p className="text-xs text-gray-500 mt-2">
            Across Entire Society
          </p>

        </div>

        {/* Resolved */}

        <div className="bg-gray-900 p-5 rounded-xl border border-green-900">

          <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">
            Resolved
          </span>

          <div className="text-3xl font-bold text-green-400 mt-2">
            {alerts.filter(a => a.resolved).length}
          </div>

          <p className="text-xs text-gray-500 mt-2">
            Successfully Closed
          </p>

        </div>

        {/* Administrator */}

        <div className="bg-gray-900 p-5 rounded-xl border border-purple-900">

          <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">
            Administrator
          </span>

          <div className="text-lg font-bold text-purple-400 mt-2">
            {currentAdmin?.name || "Loading..."}
          </div>

          <p className="text-xs text-gray-500 mt-2">
            {currentAdmin?.badgeId}
          </p>

        </div>

      </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-6 flex flex-col">
            <div className="bg-gray-900 rounded-xl border border-gray-800 flex-1 flex flex-col">
              <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-950/30">
                <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Pending Requests</h2>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-red-900 text-red-300">
                    {alerts.filter(a=>a.severity==="High" && !a.resolved).length}
                    High
                </span>
              </div>
              
              <div className="p-4 space-y-4 overflow-y-auto">

              {
              loading ? (

                <div className="flex justify-center items-center py-20">

                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>

                </div>

              ) : error ? (

                  <div className="text-center py-10 text-red-400">

                      {error}

                  </div>

              ) : alerts.filter(a => a.severity === "High").length === 0 ? (

                  <div className="text-center py-10">

                      <p className="text-emerald-400 font-semibold">

                          No High Priority Alerts

                      </p>

                  </div>

              ) : (

                  alerts.filter(
                          a => a.severity === "High" && !a.resolved
                      )   
                      .map(alert => (

                          <div
                              key={alert._id}
                              className="bg-gray-950 border border-red-900 rounded-xl p-4"
                          >

                              <div className="flex justify-between">

                                  <span className="text-red-400 font-bold">

                                      HIGH

                                  </span>

                                  <span className="text-xs text-gray-500">

                                      {alert.status}

                                  </span>

                              </div>

                              <h3 className="text-lg font-bold text-white mt-3">

                                  {alert.signal_type}

                              </h3>

                              <p className="text-gray-400 mt-2">

                                  {alert.summary}

                              </p>

                              <p className="text-xs text-gray-500 mt-2">
                                  Resident : {alert.resident_id}
                              </p>

                              <p className="text-xs text-gray-500">
                                  Gate : {alert.gate_id}
                              </p>

                              <p className="text-xs text-gray-500">
                                  {new Date(alert.created_at).toLocaleString()}
                              </p>

                              <div className="mt-3 bg-blue-950/20 border-l-4 border-blue-700 p-3 rounded">

                                  <p className="text-blue-300 text-sm">

                                      {alert.recommended_action}

                                  </p>

                              </div>

                              <div className="flex justify-between mt-5">

                                  <button

                                      onClick={() => handleAssignGuard(alert._id)}

                                      className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-lg font-semibold"
                                  >
                                    Assign Guard
                                  </button>

                                  <button
                                      className="bg-purple-700 hover:bg-purple-800 px-4 py-2 rounded-lg font-semibold"
                                  >
                                      Broadcast
                                  </button>

                              </div>

                          </div>

                      ))

              )

              }

              </div>
            </div>
          </div>

          {/* Alerts box panel component */}
          <div className="lg:col-span-2 bg-gray-900 rounded-xl border border-gray-800 flex flex-col h-full">
            <div className="p-4 border-b border-gray-800 flex justify-between items-center">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">System Alerts Log</h2>
              <span className="text-xs bg-green-800 text-gray-400 px-2 py-1 rounded border border-gray-700">Live</span>
            </div>
            
            <div className="p-4 space-y-3 overflow-y-auto h-[340px]" style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}>
              {alerts.map((alertItem) => (
                <div key={alertItem.id} className={`p-3 border-l-4 rounded-r-lg ${alertItem.color}`}>
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase">{alertItem.severity} SEVERITY</span>
                    <span className="text-[10px] text-gray-500">{alertItem.timestamp}</span>
                  </div>
                  <p className="text-sm mt-1">{alertItem.message}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Utility Grid Options */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg flex flex-col min-h-[250px]">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"></path></svg>
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Priority Broadcast</h2>
            </div>
            <p className="text-[10px] text-gray-500 mb-4 uppercase tracking-widest">Push notification to all residents</p>
            
            <form onSubmit={handleBroadcast} className="space-y-4 flex-1 flex flex-col">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Broadcast Title</label>
                <input 
                  type="text" 
                  required 
                  value={broadcastTitle}
                  onChange={(e) => setBroadcastTitle(e.target.value)} 
                  placeholder="Ex: Emergency Broadcast" 
                  className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition" 
                />
              </div>

              <div className="flex-1 flex flex-col">
                <label className="block text-xs font-medium text-gray-400 mb-1">Broadcast Message</label>
                <textarea 
                  required 
                  value={broadcastMsg}
                  onChange={(e) => setBroadcastMsg(e.target.value)}
                  placeholder="Enter emergency or system abnormality notification here..."
                  className="w-full flex-1 min-h-[120px] px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition mb-4 resize-none" 
                />
              </div>
              
              {broadcastSent && <div className="text-green-400 text-xs text-center p-2 bg-green-900/30 border border-green-800 rounded mb-3">Broadcast successfully transmitted!</div>}
              <button type="submit" className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2.5 rounded-lg transition shadow-lg mt-auto">Transmit to All</button>
            </form>
          </div>

          <div className="lg:col-span-2 bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Entity Provisioning Engine</h2>
            
            <div className="flex border-b border-gray-800 mb-5">
              <button onClick={() => { setProvTab('resident'); setGeneratedCreds(null); }} className={`px-4 py-2 text-sm font-medium transition-colors ${provTab === 'resident' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-500 hover:text-gray-300'}`}>Add Residents</button>
              <button onClick={() => { setProvTab('security'); setGeneratedCreds(null); }} className={`px-4 py-2 text-sm font-medium transition-colors ${provTab === 'security' ? 'text-emerald-400 border-b-2 border-emerald-400' : 'text-gray-500 hover:text-gray-300'}`}>Add Security Guards</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <form onSubmit={handleProvision} className="space-y-4">
                {provTab === 'resident' ? (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-400 mb-1">Number of Residents</label>
                        <input type="number" min="1" max="10" value={numResidents} onChange={handleNumResidentsChange} required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-400 mb-1">Flat Number</label>
                        <input type="text" placeholder="e.g. A-402" value={flatNum} onChange={(e) => setFlatNum(e.target.value)} required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                      </div>
                    </div>
                    
                    <div className="space-y-3 max-h-40 overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}>
                      {badges.map((badge, idx) => (
                        <div key={idx}>
                          <label className="block text-[10px] font-medium text-gray-500 mb-1">Resident {idx + 1} Badge ID</label>
                          <input type="text" placeholder="e.g. BDG-9981" value={badge} onChange={(e) => handleBadgeChange(idx, e.target.value)} required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Number of New Guards</label>
                    <input type="number" min="1" max="20" value={numSec} onChange={(e) => setNumSec(parseInt(e.target.value))} required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
                  </div>
                )}
                
                <button type="submit" className={`w-full text-white font-bold py-2.5 rounded-lg transition shadow-lg mt-4 ${provTab === 'resident' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-emerald-600 hover:bg-emerald-700'}`}>
                  Generate Identities
                </button>
              </form>

              <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 flex flex-col h-full min-h-[200px]">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-800 pb-2">Account Credentials</h3>
                
                {!generatedCreds ? (
                  <div className="flex-1 flex items-center justify-center text-sm text-gray-600 italic">Generate an account to view credentials...</div>
                ) : (
                  <div className="flex-1 overflow-y-auto space-y-3 pr-2" style={{ maxHeight: '200px', scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}>
                    {generatedCreds.map((cred, idx) => (
                      <div key={idx} className="bg-gray-900 border border-gray-800 p-3 rounded text-xs font-mono">
                        <div className="flex justify-between mb-1">
                          <span className={`${cred.role === 'Resident' ? 'text-blue-400' : 'text-emerald-400'} font-bold`}>{cred.role}</span>
                          <span className="text-gray-400">ID: <span className="text-white">{cred.id}</span></span>
                        </div>
                        <div className="text-gray-400 flex justify-between">
                          <span>Temp PWD: <span className="text-yellow-400">{cred.tempPwd}</span></span>
                          {cred.flat !== 'N/A' && <span>Flat: {cred.flat}</span>}
                        </div>
                        {cred.badge !== 'N/A' && <div className="text-gray-500 mt-1">Badge: {cred.badge}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Community Directory */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col mt-6">
          <div className="p-4 border-b border-gray-800 flex justify-between items-center flex-wrap gap-3">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Community Directory</h2>
            
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              <div className="flex space-x-1 p-0.5 bg-gray-950 rounded border border-gray-800">
                {['All', 'Resident', 'Security'].map(filterRole => (
                  <button
                    key={filterRole}
                    onClick={() => setDirectoryRoleFilter(filterRole)}
                    className={`px-3 py-1 text-xs rounded font-medium transition-all ${directoryRoleFilter === filterRole ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-gray-200'}`}
                  >
                    {filterRole === 'All' ? 'All' : filterRole === 'Resident' ? 'Residents' : 'Guards'}
                  </button>
                ))}
              </div>

              <div className="relative flex-1 sm:flex-initial">
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search ID or Name..." 
                  className="pl-8 pr-3 py-1.5 bg-gray-950 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-purple-500 w-full sm:w-64 transition"
                />
                <svg className="w-4 h-4 text-gray-500 absolute left-2.5 top-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto overflow-y-auto max-h-[400px]" style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}>
            <table className="w-full text-left text-sm text-gray-300 min-w-[600px]">
              <thead className="text-xs text-gray-500 uppercase border-b border-gray-800 bg-gray-950/50 sticky top-0 z-10">
                {/* 🛠️ Added "Status" to table head mapping structure */}
                <tr>
                  <th className="py-3 px-4 font-medium bg-gray-900">User Profile</th>
                  <th className="py-3 px-4 font-medium bg-gray-900">Role</th>
                  <th className="py-3 px-4 font-medium bg-gray-900">Status</th>
                  <th className="py-3 px-4 font-medium bg-gray-900">Score</th>
                  <th className="py-3 px-4 font-medium text-right bg-gray-900">Action</th>
                </tr>
              </thead>
              <tbody className="font-mono text-xs divide-y divide-gray-800">
                {filteredUsers.length > 0 ? filteredUsers.map((u) => (
                  <tr key={`${u.role}-${u.id}`} className="hover:bg-gray-800/50 transition">
                    <td className="px-6 py-4">
                      <p className="text-white font-bold font-sans">{u.name}</p>
                      <p className="text-gray-500">{u.id}</p>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-[10px] uppercase tracking-wider ${u.roleColor}`}>{u.role}</span>
                    </td>
                    {/* 🛠️ Dynamic account activation status indicator added below */}
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium uppercase ${u.isInitialized ? 'bg-emerald-950 text-emerald-400 border border-emerald-900/50' : 'bg-amber-950 text-yellow-500 border border-amber-900/50'}`}>
                        {u.isInitialized ? 'Activated' : 'Pending Activation'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`font-bold ${u.color}`}>{u.score === 0 ? '0 (BLACKLIST)' : u.score}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-3">
                        <button onClick={() => handleRemoveUserDirect(u)}>
    Revoke
</button>
                      </div>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="5" className="text-center py-8 text-gray-500 font-sans">No users found matching "{searchQuery}"</td>
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