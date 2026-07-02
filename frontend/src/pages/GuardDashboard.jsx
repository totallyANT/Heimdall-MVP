import { useState, useEffect } from 'react';

export default function GuardDashboard({ onLogout }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [flatNumber, setFlatNumber] = useState("");
  const [intercomState, setIntercomState] = useState("idle");
  const [error, setError] = useState("");

  const user = JSON.parse(sessionStorage.getItem("user"));

  const guardId = user?.guard?.id;

  // Active Security Guard Profile State
  const [currentGuard,setCurrentGuard]=useState(null);

  // Delivery Pre-Approval State
  const [preApprovals, setPreApprovals] = useState([
    { id: 1, resident: "John Doe (A-402)", courier: "Amazon", window: "2–4 PM", status: "pending" },
    { id: 2, resident: "Sarah Jenkins (B-105)", courier: "FedEx", window: "Morning (8 AM - 12 PM)", status: "pending" }
  ]);

  

  useEffect(() => {

    const loadAlerts = async () => {

    try {

        // Guard Profile
        const profileResponse = await fetch(
            `http://127.0.0.1:8000/profile/guard/${guardId}`
        );

        const guard = await profileResponse.json();

        setCurrentGuard({

            name: guard.full_name,

            badgeId: guard.id,

            station: guard.station || "Main Security"

        });

        // Guard Alerts
        const alertsResponse = await fetch(
            `http://127.0.0.1:8000/alerts/guard/${guardId}`
        );

        const data = await alertsResponse.json();

        setAlerts(data);

    }

    catch (err) {

        console.error(err);

        setError("Unable to load alerts.");

    }

    finally {

        setLoading(false);

    }

  };
        loadAlerts();
        const interval = setInterval(loadAlerts,3000);
        return ()=>clearInterval(interval);
    },[guardId]);
 

  const handleCall = async (e) => {
  console.log("handleCall fired");
  e.preventDefault();

  if (!flatNumber) return;

  try {
    const response = await fetch("http://127.0.0.1:8000/intercom/call", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        flatNo: flatNumber,
        requestedBy: currentGuard.guardId,
      }),
    });
    console.log("Response received:", response);

    const result = await response.json();
    console.log("Backend Response:", result);
    console.log("Reached after backend");

    const currentCallId = result.call_id;
    setCallId(result.call_id);

    console.log("Call created:", result);
    console.log("Changing state to calling");

    setIntercomState("calling");
    setCallDuration(0);

    setTimeout(async () => {

  await fetch("http://127.0.0.1:8000/intercom/connect", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      flatNo: flatNumber,
      requestedBy: currentGuard.guardId,
      call_id: currentCallId,
    }),
  });

  setIntercomState("connected");

}, 3000);

  } catch (error) {
    console.error(error);
  }
};

  const endCall = async () => {
  try {
    const response = await fetch("http://127.0.0.1:8000/intercom/end-call", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
    flatNo: flatNumber,
    requestedBy: currentGuard.guardId,
    call_id: callId,
}),
    });

    const result = await response.json();

    console.log("Call ended:", result);

    setIntercomState("idle");
    setCallDuration(0);
    setFlatNumber("");

  } catch (error) {
    console.error("Failed to end call:", error);
  }
};

  const handleAllowEntry = (id) => {
    setPreApprovals(prev => 
      prev.map(item => item.id === id ? { ...item, status: "verified" } : item)
    );
  };

  const verifyAlert = async(id)=>{

    await fetch(
        `http://127.0.0.1:8000/alerts/${id}/verify`,
        {
          method:"POST"
        }
    );
    setAlerts(prev =>
        prev.map(a =>
            a._id === id
                ? { ...a, verified: true }
                : a
        )
    );
    };

    const resolveAlert = async (id) => {
        await fetch(
            `http://127.0.0.1:8000/alerts/${id}/resolve`,
            {
                method: "POST"
            }
        );
        setAlerts(prev => prev.filter(a => a._id !== id));
    };

  return (
    <div className="bg-gray-950 min-h-screen font-sans text-gray-200 h-screen overflow-hidden flex flex-col w-full">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center shrink-0">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-bold tracking-widest text-white">HEIMDALL</span>
          <span className="px-2 py-0.5 bg-emerald-900/40 text-emerald-400 border border-emerald-800 rounded text-xs font-mono font-bold">GUARD PORTAL</span>
        </div>
        <div className="flex items-center space-x-6">
          
          {/* 🛠️ Active Security Profile Identifier */}
          <div className="flex items-center space-x-3 bg-gray-950/60 border border-gray-800 rounded-lg px-3 py-1.5 hidden sm:flex">
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

      <main className="p-6 flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden">
        <div className="lg:col-span-2 space-y-6 flex flex-col h-full overflow-y-auto pr-2">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-2xl shrink-0">
           {
            error ? (

                <div className="text-center py-20">

                    <h2 className="text-red-400 text-xl font-bold">

                        {error}

                    </h2>

                </div>

            ) : loading ? (

                <div className="flex justify-center items-center py-20">

                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>

                </div>

            ) : alerts.length === 0 ? (

                <div className="py-20 text-center">

                    <svg
                        className="w-16 h-16 text-emerald-600 mx-auto mb-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>

                    <h2 className="text-xl font-bold text-emerald-400">

                        No Active Investigations

                    </h2>

                    <p className="text-gray-500 mt-2">

                        Guard queue is currently empty.

                    </p>

                </div>

            ) : (

                alerts.map(alert => (
                    <div
                        key={alert._id}
                        className="border border-gray-800 rounded-xl p-6 mb-5 bg-gray-950"
                    >
                        <div className="flex justify-between items-center">
                            <span
                                className={`px-3 py-1 rounded text-xs font-bold
                                ${
                                    alert.severity==="High"
                                    ? "bg-red-900 text-red-300"
                                    : alert.severity==="Medium"
                                    ? "bg-yellow-900 text-yellow-300"
                                    : "bg-green-900 text-green-300"
                                }
                                `}
                            >
                                {alert.severity}
                            </span>
                            <span className="text-xs text-gray-500">
                              {alert.status}
                            </span>
                        </div>

                        <h2 className="text-xl font-bold text-white mt-4">
                          {alert.signal_type}
                        </h2>

                        <p className="text-gray-300 mt-3">
                          {alert.summary}
                        </p>

                        <p className="text-xs text-gray-500 mt-2">
                            {new Date(alert.created_at).toLocaleString()}
                        </p>

                        <div className="mt-4 bg-blue-950/30 border-l-4 border-blue-600 p-3 rounded">
                            <p className="text-blue-300 text-sm">
                              {alert.recommended_action}
                            </p>
                        </div>

                        <div className="mt-3 flex gap-2">

                        {
                            alert.verified
                            &&
                            <span className="bg-blue-900 text-blue-300 px-2 py-1 rounded text-xs">
                                VERIFIED
                            </span>
                        }
                        {
                            alert.resolved
                            &&
                            <span className="bg-green-900 text-green-300 px-2 py-1 rounded text-xs">
                              RESOLVED
                            </span>
                        }
                    </div>
                        <div className="flex gap-3 mt-5">
                            <button
                              disabled={alert.verified}
                              onClick={()=>verifyAlert(alert._id)}
                              className={`px-5 py-2 rounded-lg font-semibold
                                ${
                                    alert.verified
                                        ? "bg-gray-700 cursor-not-allowed"
                                        : "bg-yellow-600 hover:bg-yellow-700"
                                }
                              `}
                            >
                              Verify
                            </button>

                            <button
                                disabled={alert.resolved}
                                onClick={()=>resolveAlert(alert._id)}
                                className="bg-green-600 hover:bg-green-700 px-5 py-2 rounded-lg font-semibold"
                            >
                              Resolve
                            </button>
                        </div>
                    </div>
                ))
            )
            }
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg shrink-0">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path></svg>
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Resident Intercom</h2>
            </div>
            
            <form onSubmit={handleCall} className="flex gap-3">
              <div className="flex-1 relative">
                <input 
                  type="text" 
                  value={flatNumber}
                  onChange={(e) => setFlatNumber(e.target.value)}
                  disabled={intercomState !== 'idle'}
                  required 
                  placeholder="Enter Flat (e.g., A-402)" 
                  className="w-full px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 transition disabled:opacity-50" 
                />
              </div>
              <button 
                type="submit" 
                disabled={intercomState !== 'idle'}
                className="bg-gray-800 hover:bg-gray-700 text-white px-6 py-2.5 rounded-lg border border-gray-700 font-bold transition flex items-center space-x-2 disabled:opacity-50"
              >
                <span>Call</span>
              </button>
            </form>

            {intercomState !== 'idle' && (
              <div className={`mt-3 p-3 border rounded-lg flex items-center justify-between ${intercomState === 'calling' ? 'bg-blue-900/20 border-blue-800/50' : 'bg-emerald-900/20 border-emerald-800/50'}`}>
                <div className="flex items-center space-x-3">
                  <span className="flex h-3 w-3 relative">
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${intercomState === 'calling' ? 'bg-blue-400' : 'bg-emerald-400'}`}></span>
                    <span className={`relative inline-flex rounded-full h-3 w-3 ${intercomState === 'calling' ? 'bg-blue-500' : 'bg-emerald-500'}`}></span>
                  </span>
                  <span className={`text-sm font-mono ${intercomState === 'calling' ? 'text-blue-400' : 'text-emerald-400'}`}>
                    {intercomState === 'calling'
  ? `Dialing Flat ${flatNumber.toUpperCase()}...`
  : `Connected to ${flatNumber.toUpperCase()} (${String(
      Math.floor(callDuration / 60)
    ).padStart(2, "0")}:${String(callDuration % 60).padStart(2, "0")})`
}
                  </span>
                </div>
                <button type="button" onClick={endCall} className="text-xs bg-red-900/50 text-red-400 hover:bg-red-900 px-3 py-1 rounded border border-red-800 transition">End Call</button>
              </div>
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
                preApprovals.map((delivery) => (
  <div
    key={delivery.delivery_id}
    className={`p-4 rounded-xl border transition-all duration-300 ${
      delivery.status === "verified"
        ? "bg-gray-950/40 border-emerald-900/40 opacity-60"
        : "bg-gray-950 border-gray-800"
    }`}
  >
    <div className="flex justify-between items-start">
      <div>
        <div className="mt-2.5 space-y-1 text-xs">
          <p className="text-gray-400 font-sans">
            Expected:{" "}
            <strong className="text-white font-mono">
              {delivery.arrival_window}
            </strong>
          </p>

          <p className="text-gray-400 font-sans">
            Courier:{" "}
            <strong className="text-blue-400 font-sans">
              {delivery.delivery_service}
            </strong>
          </p>

          <p className="text-[10px] text-gray-500 font-sans">
            Destination: {delivery.resident_flat}
          </p>
        </div>
      </div>

      {delivery.status === "active" ? (
        <button
          onClick={() => handleAllowEntry(delivery.delivery_id)}
          className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition shadow-md border border-emerald-500 shrink-0 self-center"
        >
          Allow Entry
        </button>
      ) : (
        <span className="text-xs font-mono text-emerald-500 bg-emerald-950/20 px-3 py-1 rounded border border-emerald-900/50 self-center">
          PASSED_GATE
        </span>
      )}
    </div>
  </div>
))
)}
            </div>
          </div>
        </div>

        <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col h-full overflow-hidden shadow-lg shadow-blue-900/10">
          <div className="p-4 border-b border-gray-800 bg-gray-950/30 flex justify-between items-center">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Live Event Stream</h3>
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-[11px] text-gray-500 scroll-smooth">
            {alerts.map(alert=>(
              <div
              key={alert._id}
              className="border-b border-gray-800 pb-3 animate-fadeIn"
              >
              <div className="text-xs text-gray-500">
              {alert.signal_type}
              </div>
              <div className="text-white mt-1">
              {alert.summary}
              </div>
              <div className="text-blue-400 mt-1 text-xs">
              {alert.gate_id}
              </div>
              </div>
              ))}
          </div>
        </div>
      </main>
    </div>
  );
}