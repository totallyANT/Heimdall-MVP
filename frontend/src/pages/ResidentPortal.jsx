
import React, { useState, useEffect } from "react";
import { getResidentAlerts } from "../services/alerts";
import ResidentBot from '../components/ResidentBot';

export default function ResidentPortal({ onLogout }) {
  const [, setToast] = useState(false);
  const [guestSuccess, setGuestSuccess] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [groupSuccess, setGroupSuccess] = useState(false);
  const [workerSuccess, setWorkerSuccess] = useState(false);
  const [deliverySuccess, setDeliverySuccess] = useState(false);
  const [cardReported, setCardReported] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [vehicles, setVehicles] = useState([]);
  const [profile, setProfile] = useState(null);
  const [vehicleInput, setVehicleInput] = useState("");
  const [qrPassId, setQrPassId] = useState(null);
  const [showQrModal, setShowQrModal] = useState(false);
  const [announcements, setAnnouncements] = useState([]);
  const [currentAnnouncement, setCurrentAnnouncement] = useState(0);
  const user = JSON.parse(sessionStorage.getItem("user"));
  const residentId = user?.resident?.id;
  const today = new Date().toISOString().split("T")[0];
  const [pendingPopup, setPendingPopup] = useState(false);
  const [pendingRequests, setPendingRequests] = useState({
    pending_deliveries: [],
    pending_visitors: []
  });

  const triggerAlert = () => {
    setToast(true);
    setTimeout(() => setToast(false), 5000);
  };

  const handleFormSubmit = (e, setSuccessFlag) => {
    e.preventDefault();
    setSuccessFlag(true);
    setTimeout(() => setSuccessFlag(false), 3000);
    e.target.reset();
  };

  const handleGuestSubmit = async (e) => {
    e.preventDefault();

    const guestName = e.target.guestName.value;
    const entryDate = e.target.entryDate.value;
    const duration = Number(e.target.duration.value);

    if (entryDate < today) {
      alert("Entry date cannot be in the past.");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/visitor/guest",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            resident_id: residentId,
            guest_name: guestName,
            entry_date: entryDate,
            duration_days: duration
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail);
      }

      setQrPassId(data.passId);
      setShowQrModal(true);
      setGuestSuccess(true);

      setTimeout(() => setGuestSuccess(false), 3000);
      e.target.reset();

    } catch (err) {
      alert(err.message);
    }
  };

  {/* Group Submission */ }
  const handleGroupSubmit = async (e) => {
    e.preventDefault();

    const groupName = e.target.groupName.value;
    const entryDate = e.target.entryDate.value;
    const duration = Number(e.target.duration.value);
    const limit = Number(e.target.limit.value);

    if (entryDate < today) {
      alert("Entry date cannot be in the past.");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/visitor/group",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            resident_id: residentId,
            group_name: groupName,
            entry_date: entryDate,
            duration_days: duration,
            visitor_limit: limit
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail);
      }

      setQrPassId(data.passId);
      setShowQrModal(true);
      setGroupSuccess(true);

      setTimeout(() => setGroupSuccess(false), 3000);
      e.target.reset();

    } catch (err) {
      alert(err.message);
    }
  };

  const handleWorkerSubmit = async (e) => {
    e.preventDefault();

    const workerName = e.target.workerName.value;
    const start = e.target.startTime.value;
    const end = e.target.endTime.value;

    if (start >= end) {
      alert("End time must be after start time.");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/visitor/worker",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            resident_id: residentId,
            worker_name: workerName,
            start_time: start,
            end_time: end
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail);
      }

      setQrPassId(data.worker_id);
      setShowQrModal(true);
      setWorkerSuccess(true);

      setTimeout(() => setWorkerSuccess(false), 3000);
      e.target.reset();

    } catch (err) {
      alert(err.message);
    }
  };

  const downloadQr = async () => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/qr/${qrPassId}`
      );

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `${qrPassId}.png`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Download failed");
    }
  };

  const handleDeliverySubmit = async (e) => {
    e.preventDefault();

    const deliveryService = e.target.deliveryService.value;
    const arrivalWindow = e.target.arrivalWindow.value;

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/visitor/delivery",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            resident_id: residentId,
            delivery_service: deliveryService || null,
            arrival_window: arrivalWindow
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail);
      }

      setDeliverySuccess(true);
      setTimeout(() => setDeliverySuccess(false), 3000);

      e.target.reset();

    } catch (err) {
      alert(err.message);
    }
  };

  const addVehicle = async (e) => {
    e.preventDefault();

    const vehicle = vehicleInput.trim().toUpperCase();

    if (!vehicle) return;

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/resident/add-vehicle",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            resident_id: residentId,
            plate_number: vehicle
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail);
      }

      setVehicles([...vehicles, data.plate_number]);
      setVehicleInput("");

    } catch (err) {
      alert(err.message);
    }
  };

  const handleLostCard = async () => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/resident/report-lost-card/${residentId}`,
        {
          method: "POST"
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail);
      }

      setCardReported(true);
      alert(data.message);

    } catch (err) {
      alert(err.message);
    }
  };

  const fetchPendingRequests = async () => {
    const response = await fetch(
      `http://127.0.0.1:8000/resident/pending-requests/${residentId}`
    );

    const data = await response.json();
    console.log(data);

    setPendingRequests(data);

    if (
      data.pending_deliveries.length > 0 ||
      data.pending_visitors.length > 0
    ) {
      setPendingPopup(true);
    } else {
      setPendingPopup(false);   // IMPORTANT
    }
  };

  const approveRequest = async (requestType, requestId) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/resident/approve-request/${residentId}/${requestType}/${requestId}`,
        {
          method: "POST"
        }
      );

      const data = await response.json();

      alert(data.message);

      await fetchPendingRequests();

      if (
        pendingRequests.pending_deliveries.length === 0 &&
        pendingRequests.pending_visitors.length === 0
      ) {
        setPendingPopup(false);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const rejectRequest = async (requestType, requestId) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/resident/reject-request/${requestType}/${requestId}`,
        {
          method: "POST"
        }
      );

      const data = await response.json();

      alert(data.message);

      await fetchPendingRequests();

      if (
        pendingRequests.pending_deliveries.length === 0 &&
        pendingRequests.pending_visitors.length === 0
      ) {
        setPendingPopup(false);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const nextAnnouncement = () => {
    setCurrentAnnouncement((prev) =>
      prev === announcements.length - 1 ? 0 : prev + 1
    );
  };

  const prevAnnouncement = () => {
    setCurrentAnnouncement((prev) =>
      prev === 0 ? announcements.length - 1 : prev - 1
    );
  };

  const removeVehicle = async (vehicle) => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/resident/remove-vehicle",
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            resident_id: residentId,
            plate_number: vehicle
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail);
      }

      setVehicles(vehicles.filter(v => v !== vehicle));

    } catch (err) {
      alert(err.message);
    }
  };

  useEffect(() => {
    fetchPendingRequests();
  }, []);

  useEffect(() => {
    const fetchAnnouncements = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/resident/announcements"
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error("Failed to fetch announcements");
        }

        setAnnouncements(data.announcements || []);
      } catch (err) {
        console.error(err);
      }
    };

    fetchAnnouncements();
  }, []);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/resident/profile/${residentId}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail);
        }

        setProfile(data);
        setVehicles(data.vehicles || []);
      } catch (err) {
        console.error("Profile fetch failed:", err);
      }
    };

    if (residentId) {
      fetchProfile();
    }
  }, [residentId]);

  useEffect(() => {

    if (!residentId) return;

    const loadAlerts = async () => {

      try {
        const data = await getResidentAlerts(residentId);
        setAlerts(data);
      } catch (err) {
        console.error(err);
      }
    };
    loadAlerts();
    const interval = setInterval(loadAlerts, 5000);
    return () => clearInterval(interval);
  }, [residentId]);

  return (
    <div className="bg-gray-950 min-h-screen font-sans text-gray-200 overflow-x-hidden w-full pb-10">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center sticky top-0 z-40">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-bold tracking-widest text-white">HEIMDALL</span>
          <span className="px-2 py-0.5 bg-blue-900/30 text-blue-400 border border-blue-800 rounded text-xs font-mono font-bold hidden sm:inline-block">RESIDENT PORTAL</span>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={() => setShowProfile(true)} className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 px-4 py-2 rounded-lg transition flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            <span className="hidden sm:inline">My Profile</span>
          </button>
          <button onClick={onLogout} className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 text-red-400 px-4 py-2 rounded-lg transition">Sign Out</button>
        </div>
      </nav>

      {pendingPopup && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-gray-900 p-6 rounded-xl border border-gray-700 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4 text-white">
              Pending Approval Requests
            </h2>

            {/* Deliveries */}
            {pendingRequests?.pending_deliveries?.map((delivery) => (
              <div
                key={delivery.request_id}
                className="mb-4 p-4 border border-gray-700 rounded"
              >
                <p className="text-white">
                  Delivery from <b>{delivery.delivery_service}</b>
                </p>
                <p className="text-gray-400 text-sm">
                  Window: {delivery.arrival_window}
                </p>

                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() =>
                      approveRequest("delivery", delivery.request_id)
                    }
                    className="bg-green-600 px-4 py-2 rounded"
                  >
                    Allow
                  </button>

                  <button
                    onClick={() =>
                      rejectRequest("delivery", delivery.request_id)
                    }
                    className="bg-red-600 px-4 py-2 rounded"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}

            {/* Visitors */}
            {pendingRequests?.pending_visitors?.map((visitor) => (
              <div
                key={visitor.request_id}
                className="mb-4 p-4 border border-gray-700 rounded"
              >
                <p className="text-white">
                  Visitor <b>{visitor.guest_name}</b> is here for <b>{visitor.duration_days} days</b>
                </p>

                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() =>
                      approveRequest("visitor", visitor.request_id)
                    }
                    className="bg-green-600 px-4 py-2 rounded"
                  >
                    Allow
                  </button>

                  <button
                    onClick={() =>
                      rejectRequest("visitor", visitor.request_id)
                    }
                    className="bg-red-600 px-4 py-2 rounded"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showProfile && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-center items-center p-4 animate-fadeIn">
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md p-6 shadow-2xl relative">
            <button onClick={() => setShowProfile(false)} className="absolute top-4 right-4 text-gray-400 hover:text-white transition">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            <h2 className="text-xl font-bold text-white mb-6 flex items-center space-x-2">
              <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <span>Resident Profile</span>
            </h2>

            <div className="space-y-4 text-sm text-gray-300">
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Full Name</span>
                <span className="font-bold text-white">
                  {profile?.full_name || "Loading..."}
                </span>
              </div>

              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Resident ID</span>
                <span className="font-mono text-gray-400">
                  {profile?.id || "Loading..."}
                </span>
              </div>

              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Flat Number</span>
                <span className="font-bold text-blue-400">
                  {profile?.flat_number || "Loading..."}
                </span>
              </div>

              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Phone Number</span>
                <span>
                  {profile?.phone || "Loading..."}
                </span>
              </div>

              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Badge ID</span>
                <span className="font-mono text-cyan-400">
                  {profile?.badge || "Loading..."}
                </span>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-800">
              <div className="mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Registered Vehicles</div>
              <form onSubmit={addVehicle} className="flex gap-2 mb-4">
                <input
                  value={vehicleInput}
                  onChange={(e) => setVehicleInput(e.target.value)}
                  placeholder="Enter your vehicle number"
                  className="flex-1 px-3 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white"
                />
                <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-5 rounded-lg">Add</button>
              </form>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {vehicles.length === 0 ? (
                  <p className="text-gray-500 text-sm">No vehicles registered.</p>
                ) : (
                  vehicles.map(vehicle => (
                    <div key={vehicle} className="flex justify-between items-center bg-gray-950 p-3 rounded-lg border border-gray-800">
                      <span className="font-mono text-blue-400">{vehicle}</span>
                      <button onClick={() => removeVehicle(vehicle)} className="text-red-400 hover:text-red-300 text-xs">Remove</button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <main className="p-6 max-w-7xl mx-auto">
        <div className="bg-blue-900/30 border border-blue-800/60 text-blue-200 px-4 py-3 rounded-lg flex items-start sm:items-center space-x-3 mb-6 shadow-lg animate-fadeIn">
          <svg className="w-5 h-5 text-blue-400 shrink-0 mt-0.5 sm:mt-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          {announcements.length === 0 ? (
            <span className="text-sm font-medium text-gray-400">
              No recent announcements
            </span>
          ) : (
            <div className="flex items-center justify-between w-full gap-4">
              <span className="text-sm font-medium flex-1">
                <strong className="text-blue-300">
                  {announcements[currentAnnouncement]?.title}:
                </strong>{" "}
                {announcements[currentAnnouncement]?.message}
              </span>

              <div className="flex flex-col gap-1">
                <button
                  onClick={prevAnnouncement}
                  className="text-blue-400 hover:text-white text-xs px-2"
                >
                  ↑
                </button>

                <button
                  onClick={nextAnnouncement}
                  className="text-blue-400 hover:text-white text-xs px-2"
                >
                  ↓
                </button>
              </div>
            </div>
          )}
        </div>


        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-6">
            {/* Guest Pass */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Guest Pass</h2>
              <form className="space-y-4" onSubmit={handleGuestSubmit}>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Guest Full Name</label>
                  <input type="text" name="guestName" placeholder="Ex: Jane Smith" required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Entry Date</label>
                    <input type="date" name="entryDate" required min={today} className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Duration (Days)</label>
                    <input type="number" name="duration" min="1" placeholder="Ex: 1" required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                  </div>
                </div>
                {guestSuccess && <div className="text-green-400 text-xs text-center p-2 bg-green-900/30 border border-green-800 rounded">Single QR Pass Generated!</div>}
                <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg transition shadow-lg mt-2">Generate Guest QR</button>
              </form>
            </div>

            {/* Group Pass */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Group Pass</h2>
              <form className="space-y-4" onSubmit={handleGroupSubmit}>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Event / Group Name</label>
                  <input type="text" name="groupName" placeholder="Ex: Birthday Party" required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Entry Date</label>
                    <input type="date" name="entryDate" required min={today} className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Duration (Days)</label>
                    <input type="number" name="duration" min="1" placeholder="Ex: 1" required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition" />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Number of Visitors</label>
                  <input
                    type="number"
                    name="limit"
                    min="2"
                    placeholder="Ex: 15"
                    required
                    className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                  />
                </div>
                {groupSuccess && <div className="text-green-400 text-xs text-center p-2 bg-green-900/30 border border-green-800 rounded">Group QR Master Pass Generated!</div>}
                <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg transition shadow-lg mt-2">Generate Group QR</button>
              </form>
            </div>
          </div>

          <div className="space-y-6">
            {/* Worker Pass */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Worker Pass</h2>
              <form className="space-y-4" onSubmit={handleWorkerSubmit}>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Worker Name / Role</label>
                  <input
                    type="text"
                    name="workerName"
                    placeholder="Ex: Plumber, Electrician"
                    required
                    className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-yellow-500 transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Valid Timeslot (Today)</label>
                  <div className="flex items-center space-x-2">
                    <input type="time" name="startTime" required className="flex-1 px-2 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500" />
                    <span className="text-gray-500 text-xs font-bold">TO</span>
                    <input type="time" name="endTime" required className="flex-1 px-2 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500" />
                  </div>
                </div>
                {workerSuccess && <div className="text-green-400 text-xs text-center p-2 bg-green-900/30 border border-green-800 rounded">Worker Timeslot QR Generated!</div>}
                <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg transition shadow-lg mt-2">Generate Worker QR</button>
              </form>
            </div>

            {/* Delivery Approval */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Delivery Approval</h2>
              <form className="space-y-4" onSubmit={handleDeliverySubmit}>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Delivery Service / Name <span className="text-gray-600">(Optional)</span></label>
                  <input type="text" name="deliveryService" placeholder="Ex: Amazon, FedEx" className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Expected Arrival Window</label>
                  <select name="arrivalWindow" required className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition appearance-none">
                    <option value="" disabled selected>Select estimated time...</option>
                    <option value="1hour">Within the next 1 Hour</option>
                    <option value="morning">Today Morning (8 AM - 12 PM)</option>
                    <option value="afternoon">Today Afternoon (12 PM - 4 PM)</option>
                    <option value="evening">Today Evening (4 PM - 8 PM)</option>
                  </select>
                </div>
                {deliverySuccess && <div className="text-green-400 text-xs text-center p-2 bg-green-900/30 border border-green-800 rounded">Security Notified of Expected Delivery!</div>}
                <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-lg transition shadow-lg mt-2">Notify Gate Security</button>
              </form>
            </div>
          </div>

          <div className="flex flex-col space-y-6 h-full">
            <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col flex-1 shadow-lg">
              <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-950/30 rounded-t-xl">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Alerts Inbox</h2>
                <span className="flex h-3 w-3 relative"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span></span>
              </div>

              {/* 🛠️ Capped height and custom dark scrollbars applied below */}
              <div
                className="p-4 space-y-3 overflow-y-auto h-[500px]"
                style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}
              >
                {
                  alerts.length === 0 ? (

                    <div className="text-green-400 text-sm">
                      No active security alerts.
                    </div>

                  ) : (

                    alerts.map(alert => (

                      <div
                        key={alert._id}
                        className="border border-red-700 rounded-lg p-4 mb-3 bg-red-950/20"
                      >

                        <div className="flex justify-between">

                          <span className="font-bold text-red-400">
                            {alert.severity}
                          </span>

                          <span className="text-xs text-gray-400">
                            {alert.status}
                          </span>

                        </div>

                        <h3 className="font-semibold text-white mt-2">
                          {alert.signal_type}
                        </h3>

                        <p className="mt-2 text-gray-300">
                          {alert.summary}
                        </p>

                        <p className="mt-2 text-sm text-blue-300">
                          {alert.recommended_action}
                        </p>

                      </div>

                    ))

                  )
                }

              </div>

            </div>

            <button
              onClick={handleLostCard}
              disabled={cardReported}
              className={`w-full font-bold py-4 px-4 rounded-xl transition shadow-lg ${cardReported ? 'bg-gray-800 text-gray-500 border-gray-700' : 'bg-red-900/80 hover:bg-red-800 text-red-100 border border-red-700'}`}>
              {cardReported ? 'Card Locked & Security Notified' : 'Report Lost Card'}
            </button>
          </div>
        </div>

        <div className="mt-6 bg-gray-900 rounded-xl p-6 border border-gray-800 shadow-lg overflow-hidden">
          <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-3">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Recent Activity</h2>
            <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded border border-gray-700">Last 7 Days</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300 min-w-[600px]">
              <thead className="text-xs text-gray-500 uppercase bg-gray-950/50 border-y border-gray-800">
                <tr>
                  <th className="px-4 py-3 font-medium">Timestamp</th>
                  <th className="px-4 py-3 font-medium">Entity / Guest Name</th>
                  <th className="px-4 py-3 font-medium">Location</th>
                  <th className="px-4 py-3 font-medium">Clearance Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800 font-mono text-xs">
                <tr className="hover:bg-gray-800/50 transition">
                  <td className="px-4 py-3 text-gray-500">Today, 14:32:01</td>
                  <td className="px-4 py-3"><span className="text-white font-sans font-bold">John Doe</span> <span className="text-[10px] text-gray-500 ml-1 uppercase">Resident</span></td>
                  <td className="px-4 py-3">North Gate</td>
                  <td className="px-4 py-3"><span className="text-emerald-400 bg-emerald-900/30 px-2 py-1 rounded border border-emerald-800/50">ACCESS_GRANTED</span></td>
                </tr>
                <tr className="hover:bg-gray-800/50 transition">
                  <td className="px-4 py-3 text-gray-500">Today, 10:15:44</td>
                  <td className="px-4 py-3"><span className="text-blue-400 font-sans font-bold">Jane Smith</span> <span className="text-[10px] text-blue-500 ml-1 uppercase">Guest QR</span></td>
                  <td className="px-4 py-3">Lobby Turnstile</td>
                  <td className="px-4 py-3"><span className="text-emerald-400 bg-emerald-900/30 px-2 py-1 rounded border border-emerald-800/50">ACCESS_GRANTED</span></td>
                </tr>
                <tr className="hover:bg-gray-800/50 transition">
                  <td className="px-4 py-3 text-gray-500">Today, 09:00:15</td>
                  <td className="px-4 py-3"><span className="text-yellow-400 font-sans font-bold">Maid</span> <span className="text-[10px] text-yellow-500 ml-1 uppercase">Worker QR</span></td>
                  <td className="px-4 py-3">Service Gate</td>
                  <td className="px-4 py-3"><span className="text-emerald-400 bg-emerald-900/30 px-2 py-1 rounded border border-emerald-800/50">ACCESS_GRANTED (Scale Valid)</span></td>
                </tr>
                <tr className="hover:bg-gray-800/50 transition">
                  <td className="px-4 py-3 text-gray-500">Yesterday, 19:05:12</td>
                  <td className="px-4 py-3"><span className="text-purple-400 font-sans font-bold">Birthday Party</span> <span className="text-[10px] text-purple-500 ml-1 uppercase">Group QR</span></td>
                  <td className="px-4 py-3">South Gate</td>
                  <td className="px-4 py-3"><span className="text-emerald-400 bg-emerald-900/30 px-2 py-1 rounded border border-emerald-800/50">ACCESS_GRANTED (4/15)</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
      <ResidentBot />

      {showQrModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-900 p-6 rounded-xl border border-gray-700 text-center relative">
            <button
              onClick={() => setShowQrModal(false)}
              className="absolute top-3 right-3 text-gray-400 hover:text-white"
            >
              ✕
            </button>

            <h2 className="text-white text-xl font-bold mb-4">
              QR Pass Generated
            </h2>

            <img
              src={`http://127.0.0.1:8000/qr/${qrPassId}`}
              alt="QR Code"
              className="w-64 h-64 mx-auto rounded-lg bg-white p-2"
            />

            <p className="text-cyan-400 font-mono mt-4 text-lg">
              {qrPassId.startsWith("VIS-")
                ? `Guest ID: ${qrPassId}`
                : qrPassId.startsWith("GRP-")
                  ? `Group ID: ${qrPassId}`
                  : `Worker ID: ${qrPassId}`}
            </p>

            <button
              onClick={downloadQr}
              className="mt-4 bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-lg text-white font-semibold"
            >
              Download QR
            </button>
          </div>
        </div>
      )}

    </div>
  );
}