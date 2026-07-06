import { useState, useEffect } from 'react';

const API = import.meta.env.VITE_MAIN_BACKEND_URL || "http://127.0.0.1:8000";

export default function GuardDashboard({ onLogout }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const user = JSON.parse(sessionStorage.getItem("user"));
  const guardId = user?.guard?.id;

  const [currentGuard, setCurrentGuard] = useState(null);
  
  const [preApprovals, setPreApprovals] = useState([]);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackType, setFeedbackType] = useState("");
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [feedback, setFeedback] = useState("");

  // --------------------------------------------
  // Load Deliveries
  // --------------------------------------------
  const loadDeliveries = async () => {
    try {
      const response = await fetch(`${API}/delivery/pending`);
      const data = await response.json();
      setPreApprovals(data);
    } catch (err) {
      console.error(err);
    }
  };

  // --------------------------------------------
  // useEffect Hooks & Auto-Refresh Lifecycle
  // --------------------------------------------
  useEffect(() => {
    const loadAlerts = async () => {
      try {
        // Guard Profile
        const profileResponse = await fetch(`${API}/profile/guard/${guardId}`);
        const guard = await profileResponse.json();

        setCurrentGuard({
          name: guard.full_name,
          badgeId: guard.id,
          station: guard.station || "Main Security"
        });

        // Guard Alerts
        const alertsResponse = await fetch(`${API}/alerts/guard/${guardId}`);
        const data = await alertsResponse.json();
        setAlerts(data);
      } catch (err) {
        console.error(err);
        setError("Unable to load alerts.");
      } finally {
        setLoading(false);
      }
    };

    // Initial Load
    loadAlerts();
    loadDeliveries();

    // Auto Refresh Queue Configuration
    const interval = setInterval(() => {
      loadAlerts();
      loadDeliveries();
    }, 3000);

    return () => clearInterval(interval);
  }, [guardId]);

  // --------------------------------------------
  // Allow Entry
  // --------------------------------------------
  const handleAllowEntry = async (deliveryId) => {
    try {
      const response = await fetch(`${API}/delivery/allow-entry`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          delivery_id: deliveryId
        })
      });

      const data = await response.json();
      console.log("Allow Entry:", data);
      await loadDeliveries();
    } catch (err) {
      console.error(err);
    }
  };

  // --------------------------------------------
  // Exit Delivery
  // --------------------------------------------
  const handleExit = async (deliveryId) => {
    try {
      const response = await fetch(`${API}/delivery/exit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          delivery_id: deliveryId
        })
      });

      const data = await response.json();
      console.log("Exit:", data);
      await loadDeliveries();
    } catch (err) {
      console.error(err);
    }
  };

  // --------------------------------------------
  // Resolve Alert Notification Workflow
  // --------------------------------------------
  const resolveAlert = async () => {
    try {
      await fetch(`${API}/alerts/${selectedAlert}/resolve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          feedback
        })
      });

      setAlerts(prev => prev.filter(a => a._id !== selectedAlert));
      setShowFeedbackModal(false);
      setFeedback("");
    } catch (err) {
      console.error(err);
    }
  };

  // --------------------------------------------
  // Dismiss Alert Notification Workflow
  // --------------------------------------------
  const dismissAlert = async () => {
    try {
      await fetch(`${API}/alerts/${selectedAlert}/dismiss`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          feedback
        })
      });

      setAlerts(prev => prev.filter(a => a._id !== selectedAlert));
      setShowFeedbackModal(false);
      setFeedback("");
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="bg-gray-950 min-h-screen font-sans text-gray-200 h-screen overflow-hidden flex flex-col w-full">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center shrink-0">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-bold tracking-widest text-white">HEIMDALL</span>
          <span className="px-2 py-0.5 bg-emerald-900/40 text-emerald-400 border border-emerald-800 rounded text-xs font-mono font-bold">GUARD PORTAL</span>
        </div>
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3 bg-gray-955/60 border border-gray-800 rounded-lg px-3 py-1.5 hidden sm:flex">
            <div className="h-7 w-7 rounded-full bg-blue-900/40 border border-blue-800 flex items-center justify-center text-xs font-bold text-blue-400 font-mono">
              {currentGuard?.name?.charAt(0) || "G"}
            </div>
            <div className="text-left">
              <p className="text-xs font-bold text-gray-200 leading-tight">{currentGuard?.name || "Loading..."}</p>
              <p className="text-[10px] text-gray-500 font-mono leading-none">{currentGuard?.badgeId} • {currentGuard?.station}</p>
            </div>
          </div>

          <div className="text-right border-r border-gray-800 pr-6 hidden sm:block">
            <p className="text-xs text-gray-500 uppercase tracking-wider font-bold">Active Queue</p>
            <p className="text-sm font-bold font-mono text-blue-400">
              {alerts.length} Pending Alert{alerts.length !== 1 ? "s" : ""}
            </p>
          </div>
          <button onClick={onLogout} className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 text-red-400 px-4 py-2 rounded-lg transition">Sign Out</button>
        </div>
      </nav>

      <main className="p-6 flex-1 overflow-hidden">
        <div className="lg:col-span-2 space-y-6 flex flex-col h-full overflow-y-auto pr-2">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-2xl shrink-0">
            {error ? (
              <div className="text-center py-20">
                <h2 className="text-red-400 text-xl font-bold">{error}</h2>
              </div>
            ) : loading ? (
              <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="py-20 text-center">
                <svg className="w-16 h-16 text-emerald-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h2 className="text-xl font-bold text-emerald-400">No Active Investigations</h2>
                <p className="text-gray-500 mt-2">Guard queue is currently empty.</p>
              </div>
            ) : (
              alerts.map(alert => (
                <div key={alert._id} className="border border-gray-800 rounded-xl p-6 mb-5 bg-gray-950">
                  <div className="flex justify-between items-center">
                    <span className={`px-3 py-1 rounded text-xs font-bold ${
                      alert.severity === "High"
                        ? "bg-red-900 text-red-300"
                        : alert.severity === "Medium"
                        ? "bg-yellow-900 text-yellow-300"
                        : "bg-green-900 text-green-300"
                    }`}>
                      {alert.severity}
                    </span>
                    <span className="text-xs text-gray-500">{alert.status}</span>
                  </div>

                  <h2 className="text-xl font-bold text-white mt-4">{alert.signal_type}</h2>
                  <p className="text-gray-300 mt-3">{alert.summary}</p>
                  <p className="text-xs text-gray-500 mt-2">{alert.created_at}</p>

                  <div className="mt-4 bg-blue-950/30 border-l-4 border-blue-600 p-3 rounded">
                    <p className="text-blue-300 text-sm">{alert.recommended_action}</p>
                  </div>

                  <div className="flex gap-3 mt-5">
                    <button
                      onClick={() => {
                        setSelectedAlert(alert._id);
                        setFeedbackType("dismiss");
                        setFeedback("");
                        setShowFeedbackModal(true);
                      }}
                      className="bg-red-600 hover:bg-red-700 px-5 py-2 rounded-lg font-semibold"
                    >
                      Dismiss
                    </button>
                    <button
                      onClick={() => {
                        setSelectedAlert(alert._id);
                        setFeedbackType("resolve");
                        setFeedback("");
                        setShowFeedbackModal(true);
                      }}
                      className="bg-green-600 hover:bg-green-700 px-5 py-2 rounded-lg font-semibold"
                    >
                      Resolve
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Gate Delivery Verification Section */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg">
            <div className="flex items-center space-x-2 mb-4 border-b border-gray-800 pb-3">
              <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Pre-approved Deliveries</h2>
            </div>

            <div className="space-y-3 max-h-60 overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}>
              {preApprovals.length === 0 ? (
                <p className="text-xs text-gray-500 italic text-center py-4">No active delivery pre-approvals listed.</p>
              ) : (
                [...preApprovals]
                  .sort((a, b) => {
                    if (a.status === "active" && b.status !== "active") return -1;
                    if (a.status !== "active" && b.status === "active") return 1;
                    return 0;
                  })
                  .map((delivery) => (
                    <div
                      key={delivery.delivery_id}
                      className={`p-4 rounded-xl border transition-all duration-300 ${
                        delivery.status === "PASSED_GATE"
                          ? "bg-gray-950/40 border-emerald-900/40 opacity-60"
                          : "bg-gray-950 border-gray-800"
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="mt-2.5 space-y-1 text-xs">
                            <p className="text-gray-400 font-sans">
                              Expected: <strong className="text-white font-mono">{delivery.arrival_window}</strong>
                            </p>
                            <p className="text-gray-400 font-sans">
                              Courier: <strong className="text-blue-400 font-sans">{delivery.delivery_service}</strong>
                            </p>
                            <p className="text-[10px] text-gray-500 font-sans">
                              Destination: {delivery.resident_flat}
                            </p>
                          </div>
                        </div>

                        <div className="flex flex-col gap-2">
                          {delivery.status === "active" ? (
                            <button
                              onClick={() => handleAllowEntry(delivery.delivery_id)}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition"
                            >
                              Allow Entry
                            </button>
                          ) : (
                            <button disabled className="bg-gray-600 text-white text-xs font-bold px-4 py-2 rounded-lg cursor-not-allowed">
                              Passed Gate
                            </button>
                          )}

                          <button
                            onClick={() => handleExit(delivery.delivery_id)}
                            disabled={delivery.status !== "PASSED_GATE"}
                            className={`text-white text-xs font-bold px-4 py-2 rounded-lg transition ${
                              delivery.status === "PASSED_GATE"
                                ? "bg-red-600 hover:bg-red-700"
                                : "bg-gray-700 cursor-not-allowed opacity-50"
                            }`}
                          >
                            Exit
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
              )}
            </div>
          </div>
        </div>
      </main>

      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-[500px] p-6">
            <h2 className="text-xl font-bold text-white mb-4">
              {feedbackType === "resolve" ? "Resolve Alert" : "Dismiss Alert"}
            </h2>

            <textarea
              rows="5"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg p-3 text-white"
              placeholder="Enter guard feedback..."
            />

            <div className="flex justify-end gap-3 mt-5">
              <button
                onClick={() => {
                  setShowFeedbackModal(false);
                  setFeedback("");
                }}
                className="px-5 py-2 bg-gray-700 rounded-lg"
              >
                Cancel
              </button>

              <button
                onClick={() => {
                  if (!feedback.trim()) {
                    alert("Please enter feedback.");
                    return;
                  }
                  if (feedbackType === "resolve") {
                    resolveAlert();
                  } else {
                    dismissAlert();
                  }
                }}
                className="px-5 py-2 bg-blue-600 rounded-lg"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}