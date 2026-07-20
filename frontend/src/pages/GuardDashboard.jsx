import { useState, useEffect } from 'react';

const API = import.meta.env.VITE_MAIN_BACKEND_URL || "http://127.0.0.1:8000";

export default function GuardDashboard({ onLogout }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const user = JSON.parse(sessionStorage.getItem("user"));
  const guardId = user?.guard?.id;

  const [currentGuard, setCurrentGuard] = useState({
    name: user?.guard?.full_name || "Security Officer",
    badgeId: guardId || "GRD-???",
    station: "Gate House Alpha"
  });
  
  const [preApprovals, setPreApprovals] = useState([]);
  const [searchQuery, setSearchQuery] = useState(""); 
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackType, setFeedbackType] = useState("");
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [feedback, setFeedback] = useState("");

  // --------------------------------------------
  // Load Deliveries
  // --------------------------------------------
  const loadDeliveries = async () => {
    try {
      const response = await fetch(`${API}/guard/delivery/pending`);
      if (!response.ok) throw new Error("Delivery fetch failed");
      const data = await response.json();
      setPreApprovals(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Delivery Load Error:", err);
    }
  };

  // --------------------------------------------
  // Lifecycle Sync Engine
  // --------------------------------------------
  useEffect(() => {
    if (!guardId) {
      setError("No valid Guard session found.");
      setLoading(false);
      return;
    }

    const loadAlerts = async () => {
      try {
        const profileResponse = await fetch(`${API}/profile/guard/${guardId}`);
        if (profileResponse.ok) {
          const guardData = await profileResponse.json();
          if (guardData) {
            setCurrentGuard({
              name: guardData.full_name || "Security Officer",
              badgeId: guardData.id || guardId,
              station: guardData.station || "Gate House Alpha"
            });
          }
        }

        const alertsResponse = await fetch(`${API}/alerts/guard/${guardId}`);
        if (!alertsResponse.ok) throw new Error("Alerts query error");
        const data = await alertsResponse.json();
        setAlerts(Array.isArray(data) ? data : []);
        setError("");
      } catch (err) {
        console.error("Alert Load Error:", err);
        setError("Unable to sync active security queue.");
      } finally {
        setLoading(false);
      }
    };

    loadAlerts();
    loadDeliveries();

    const interval = setInterval(() => {
      loadAlerts();
      loadDeliveries();
    }, 3000);

    return () => clearInterval(interval);
  }, [guardId]);

  // --------------------------------------------
  // Action Event Handlers
  // --------------------------------------------
  const handleAllowEntry = async (deliveryId) => {
    try {
      const response = await fetch(`${API}/guard/delivery/allow-entry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ delivery_id: deliveryId })
      });
      if (response.ok) {
        setPreApprovals(prev => 
          prev.map(d => d.delivery_id === deliveryId ? { ...d, status: "PASSED_GATE" } : d)
        );
      }
      await loadDeliveries();
    } catch (err) {
      console.error(err);
    }
  };

  const handleExit = async (deliveryId) => {
    try {
      const response = await fetch(`${API}/guard/delivery/exit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ delivery_id: deliveryId })
      });
      if (response.ok) {
        setPreApprovals(prev => prev.filter(d => d.delivery_id !== deliveryId));
      }
      await loadDeliveries();
    } catch (err) {
      console.error(err);
    }
  };

  // --------------------------------------------
  // Resolve Alert Workflow
  // --------------------------------------------
  const resolveAlert = async () => {
    if (!selectedAlert) return;
    try {
      const response = await fetch(`${API}/security/alert-action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          alertId: String(selectedAlert), // Explicitly cast to clean string literal token
          guardId: guardId,
          decision: "RESOLVE",
          reason: feedback 
        })
      });

      if (response.ok) {
        setAlerts(prev => prev.filter(a => (a._id || a.id) !== selectedAlert));
        setShowFeedbackModal(false);
        setFeedback("");
        setSelectedAlert(null);
      } else {
        alert("Error saving resolution to backend server.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  // --------------------------------------------
  // Dismiss Alert Workflow
  // --------------------------------------------
  const dismissAlert = async () => {
    if (!selectedAlert) return;
    try {
      const response = await fetch(`${API}/security/alert-action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          alertId: String(selectedAlert), // Explicitly cast to clean string literal token
          guardId: guardId,
          decision: "DISMISS",
          reason: feedback 
        })
      });

      if (response.ok) {
        setAlerts(prev => prev.filter(a => (a._id || a.id) !== selectedAlert));
        setShowFeedbackModal(false);
        setFeedback("");
        setSelectedAlert(null);
      } else {
        alert("Error saving dismissal to backend server.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  

  const filteredDeliveries = preApprovals.filter(delivery => 
    delivery.resident_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="bg-gray-950 min-h-screen font-sans text-gray-200 h-screen overflow-hidden flex flex-col w-full">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center shrink-0">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-bold tracking-widest text-white">HEIMDALL</span>
          <span className="px-2 py-0.5 bg-emerald-900/40 text-emerald-400 border border-emerald-800 rounded text-xs font-mono font-bold">GUARD PORTAL</span>
        </div>
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3 bg-gray-800/60 border border-gray-800 rounded-lg px-3 py-1.5 hidden sm:flex">
            <div className="h-7 w-7 rounded-full bg-blue-900/40 border border-blue-800 flex items-center justify-center text-xs font-bold text-blue-400 font-mono">
              {currentGuard?.name?.charAt(0) || "G"}
            </div>
            <div className="text-left">
              <p className="text-xs font-bold text-gray-200 leading-tight">{currentGuard?.name}</p>
              <p className="text-[10px] text-gray-500 font-mono leading-none">{currentGuard?.badgeId} • {currentGuard?.station}</p>
            </div>
          </div>
          <div className="button-group flex gap-4 items-center">
            <button onClick={onLogout} className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 text-red-400 px-4 py-2 rounded-lg transition">Sign Out</button>
          </div>
        </div>
      </nav>

      <main className="p-6 flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Core Alerts List Section */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-2xl flex flex-col h-full overflow-hidden">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-800 pb-3">Security Threats Dispatch</h2>
        <div className="flex-1 overflow-y-auto pr-2 space-y-4" style={{ scrollbarWidth: 'thin' }}>
          {error ? (
            <div className="text-center py-20"><h2 className="text-red-400 text-lg font-bold">{error}</h2></div>
          ) : loading ? (
            <div className="flex justify-center items-center py-20"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div></div>
          ) : alerts.filter(alert => alert.status !== "DISMISSED" && alert.status !== "RESOLVED").length === 0 ? (
            <div className="py-20 text-center">
              <div className="text-emerald-500 text-4xl mb-3">✓</div>
              <h2 className="text-lg font-bold text-emerald-400">No Active Investigations</h2>
              <p className="text-xs text-gray-500 mt-1">Property security perimeter is stable.</p>
            </div>
          ) : (
            alerts
              .filter(alert => alert.status !== "DISMISSED" && alert.status !== "RESOLVED")
              .map(alert => (
                <div key={alert._id || alert.id} className="border border-gray-800 rounded-xl p-5 bg-gray-950 transition hover:border-gray-700">
                  <div className="flex justify-between items-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      alert.severity === "High" ? "bg-red-950 text-red-400 border border-red-900" :
                      alert.severity === "Medium" ? "bg-yellow-950 text-yellow-400 border border-yellow-900" : "bg-green-950 text-green-400 border border-green-900"
                    }`}>{alert.severity}</span>
                  </div>
                  <h3 className="text-base font-bold text-white mt-3">{alert.signal_type || "SYSTEM ALARM"}</h3>
                  <p className="text-xs text-gray-400 mt-2 leading-relaxed">{alert.summary || alert.description}</p>
                  <div className="mt-3 bg-blue-950/20 border-l-2 border-blue-500 p-2.5 rounded text-[11px] text-blue-300">
                    <strong>Action Required:</strong> {alert.recommended_action || "Investigate root trigger immediately."}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <button onClick={() => { setSelectedAlert(alert._id || alert.id); setFeedbackType("dismiss"); setFeedback(""); setShowFeedbackModal(true); }} className="bg-red-950/60 hover:bg-red-900 border border-red-800 text-red-300 text-xs font-semibold px-4 py-1.5 rounded-lg transition">Dismiss</button>
                    <button onClick={() => { setSelectedAlert(alert._id || alert.id); setFeedbackType("resolve"); setFeedback(""); setShowFeedbackModal(true); }} className="bg-emerald-950/60 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-xs font-semibold px-4 py-1.5 rounded-lg transition">Resolve</button>
                  </div>
                </div>
              ))
          )}
        </div>
      </div>

        {/* Deliveries Dashboard Panel */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg flex flex-col h-full overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 border-b border-gray-800 pb-3 shrink-0">
            <div className="flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Pre-approved Deliveries ({filteredDeliveries.length})</h2>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Resident Name..."
              className="bg-gray-950 border border-gray-800 text-xs text-white rounded-lg px-3 py-1.5 w-full sm:w-48 focus:outline-none focus:border-emerald-500 placeholder-gray-600 font-sans"
            />
          </div>

          <div className="flex-1 overflow-y-auto pr-1 space-y-3" style={{ scrollbarWidth: 'thin' }}>
            {filteredDeliveries.length === 0 ? (
              <p className="text-xs text-gray-500 italic text-center py-10">No matching active pre-approvals monitored.</p>
            ) : (
              filteredDeliveries.map((delivery) => (
                <div key={delivery.delivery_id} className={`p-4 rounded-xl border flex justify-between items-center transition duration-200 ${
                  delivery.status === "PASSED_GATE" ? "bg-gray-900/60 border-blue-900/50" : "bg-gray-950 border-gray-800"
                }`}>
                  <div className="space-y-1">
                    <p className="text-xs text-gray-400">Expected: <strong className="text-emerald-400 font-mono">{delivery.arrival_window}</strong></p>
                    <p className="text-xs text-gray-400">Courier: <strong className="text-blue-400 font-sans">{delivery.delivery_service}</strong></p>
                    <p className="text-[10px] text-gray-400 font-mono">Destination: {delivery.resident_name} Flat {delivery.resident_flat}</p>
                  </div>
                  <div className="flex flex-col gap-2">
                    {delivery.status === "active" ? (
                      <button onClick={() => handleAllowEntry(delivery.delivery_id)} className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition shadow-md w-28">Allow Entry</button>
                    ) : (
                      <button onClick={() => handleExit(delivery.delivery_id)} className="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition shadow-md w-28">Exit</button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>

      {/* Action Dialog Overlay Modals */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-md p-6 shadow-2xl">
            <h2 className="text-base font-bold text-white mb-2">{feedbackType === "resolve" ? "Resolve Anomaly Case" : "Dismiss Event Trigger"}</h2>
            <p className="text-xs text-gray-500 mb-4">Please log your field action verification note before updating the state.</p>
            <textarea rows="4" value={feedback} onChange={(e) => setFeedback(e.target.value)} className="w-full bg-gray-950 border border-gray-800 text-sm focus:border-blue-500 focus:outline-none rounded-lg p-3 text-white placeholder-gray-600 font-sans" placeholder="Type resolution log note statement here..." />
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => { setShowFeedbackModal(false); setFeedback(""); setSelectedAlert(null); }} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-xs font-semibold rounded-lg text-gray-300 transition">Cancel</button>
              <button onClick={() => { if (!feedback.trim()) { alert("Feedback statement is required."); return; } feedbackType === "resolve" ? resolveAlert() : dismissAlert(); }} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-xs font-semibold rounded-lg text-white transition">Submit Verification</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}