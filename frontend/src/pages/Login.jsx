import { useState } from 'react';
import { Eye, EyeOff } from "lucide-react";

const API = import.meta.env.VITE_MAIN_BACKEND_URL || "http://127.0.0.1:8000";

export default function Login({ onLogin }) {
  const [view, setView] = useState('signin');
  const [role, setRole] = useState('Resident');
  const [signupRole, setSignupRole] = useState('Resident');
  const [showLoginPwd, setShowLoginPwd] = useState(false);
  const [showNewPwd, setShowNewPwd] = useState(false);
  const [showConfirmPwd, setShowConfirmPwd] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [loginId, setLoginId] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const [assignedId, setAssignedId] = useState('');
  const [tempPasscode, setTempPasscode] = useState('');
  const [fullName, setFullName] = useState('');
  const [age, setAge] = useState('');
  const [phone, setPhone] = useState('');
  const [flatNumber, setFlatNumber] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // --------------------------------------------
  // Handle Authentication Login
  // --------------------------------------------
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    let endpoint = '';
    if (role === 'Resident') {
      endpoint = '/auth/login';
    } else if (role === 'Security') {
      endpoint = '/auth/security/login';
    } else {
      endpoint = '/auth/admin/login';
    }

    try {
      const response = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id: loginId,
          password: loginPassword
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      setSuccess(data.message);
      sessionStorage.setItem("user", JSON.stringify(data));

      setTimeout(() => {
        onLogin(role);
      }, 1000);

    } catch (err) {
      setError(err.message);
    }
  };

  // --------------------------------------------
  // Handle Account Identity Initialization
  // --------------------------------------------
  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    let endpoint = '';
    let payload = {};

    if (signupRole === 'Resident') {
      endpoint = '/auth/initialize';
      payload = {
        id: assignedId,
        flat_number: flatNumber,
        temp_passcode: tempPasscode,
        full_name: fullName,
        age: Number(age),
        phone: phone,
        password: newPassword,
        confirm_password: confirmPassword
      };
    } else {
      endpoint = '/auth/security/initialize';
      payload = {
        id: assignedId,
        temp_passcode: tempPasscode,
        full_name: fullName,
        age: Number(age),
        phone: phone,
        password: newPassword,
        confirm_password: confirmPassword
      };
    }

    try {
      const response = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Activation failed');
      }

      setSuccess(data.message);

      setTimeout(() => {
        setView('signin');
        setSuccess('');
      }, 1500);

    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="bg-gray-950 flex items-center justify-center min-h-screen font-sans text-gray-200 p-4 w-full">
      <div className="w-full max-w-md bg-gray-900 rounded-2xl shadow-2xl border border-gray-800 p-8 relative overflow-hidden" style={{ boxShadow: '0 0 20px rgba(59, 130, 246, 0.15)' }}>
        <div className="text-center mb-6">
          <div className="flex justify-center mb-3">
            <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-widest">HEIMDALL</h1>
          <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider">Authentication Gateway</p>
        </div>

        {view === 'signin' ? (
          <div className="animate-fadeIn block">
            <div className="mb-6">
              <p className="text-xs text-gray-400 mb-2 text-center">Select Your Role</p>
              <div className="flex space-x-2">
                {['Resident', 'Security', 'Admin'].map(r => (
                  <button key={r} type="button" onClick={() => setRole(r)}
                    className={`flex-1 py-2 text-sm rounded-lg border transition-all ${role === r ? 'bg-blue-600 text-white border-blue-600' : 'bg-transparent text-gray-400 border-gray-600 hover:border-gray-500'}`}>
                    {r}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">User ID</label>
                <input
                  type="text"
                  value={loginId}
                  onChange={(e) => setLoginId(e.target.value)}
                  placeholder="Enter your ID"
                  required
                  className="w-full px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                />
              </div>

              <div className="relative">
                <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
                <input
                  type={showLoginPwd ? "text" : "password"}
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowLoginPwd(!showLoginPwd)}
                  className="absolute right-3 top-9 text-gray-500 hover:text-gray-300"
                >
                  {showLoginPwd ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                </button>
              </div>
              {error && (
                <div className="text-red-400 text-xs text-center p-2 bg-red-900/30 border border-red-800 rounded">
                  {error}
                </div>
              )}

              {success && (
                <div className="text-green-400 text-xs text-center p-2 bg-green-900/30 border border-green-800 rounded">
                  {success}
                </div>
              )}
              <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg mt-4 transition shadow-lg">
                Sign In
              </button>
            </form>

            <div className="mt-6 text-center text-sm">
              <span className="text-gray-500">New here? </span>
              <button onClick={() => setView('signup')} className="text-blue-400 hover:text-blue-300 font-semibold transition">Activate Account</button>
            </div>
          </div>
        ) : (
          <div className="animate-fadeIn block">
            <div className="mb-4 border-b border-gray-800 pb-3">
              <h2 className="text-lg font-bold text-white text-center">Account Activation</h2>
            </div>

            <div className="mb-4">
              <p className="text-[10px] text-gray-500 mb-2 uppercase tracking-widest text-center">Choose Your Role</p>
              <div className="flex space-x-2">
                {['Resident', 'Security'].map(r => (
                  <button key={r} type="button" onClick={() => setSignupRole(r)}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${signupRole === r ? 'bg-blue-600 text-white border-blue-400 shadow-inner' : 'bg-gray-950 text-gray-400 border-gray-700 hover:border-gray-500'}`}>
                    {r}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSignup} className="space-y-4 max-h-[55vh] overflow-y-auto pr-2 pb-2" style={{ scrollbarWidth: 'thin', scrollbarColor: '#374151 transparent' }}>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Assigned ID</label>
                  <input
                    type="text"
                    value={assignedId}
                    onChange={(e) => setAssignedId(e.target.value)}
                    placeholder="ID"
                    required
                    className="w-full px-3 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Temp Passcode</label>
                  <input
                    type="text"
                    value={tempPasscode}
                    onChange={(e) => setTempPasscode(e.target.value)}
                    placeholder="Ex: ab12cd"
                    required
                    className="w-full px-3 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Ex: Jane Doe"
                  required
                  className="w-full px-3 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Age</label>
                  <input
                    type="number"
                    min="18"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="Age"
                    required
                    className="w-full px-3 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="Phone"
                    required
                    className="w-full px-3 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition"
                  />
                </div>
              </div>

              {signupRole === 'Resident' && (
                <div className="animate-fadeIn">
                  <label className="block text-xs font-medium text-gray-400 mb-1">Flat Number</label>
                  <input
                    type="text"
                    value={flatNumber}
                    onChange={(e) => setFlatNumber(e.target.value)}
                    placeholder="Ex: 402"
                    required
                    className="w-full px-3 py-2.5 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition"
                  />
                </div>
              )}

              <div className="relative pt-2 border-t border-gray-800/50">
                <label className="block text-xs font-medium text-gray-400 mb-1">New Password</label>
                <input
                  name="newPwd"
                  type={showNewPwd ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPwd(!showNewPwd)}
                  className="absolute right-3 top-9 text-gray-500 hover:text-gray-300"
                >
                  {showNewPwd ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                </button>
              </div>

              <div className="relative">
                <label className="block text-xs font-medium text-gray-400 mb-1">Confirm Password</label>
                <input
                  name="confirmPwd"
                  type={showConfirmPwd ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none transition pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPwd(!showConfirmPwd)}
                  className="absolute right-3 top-9 text-gray-500 hover:text-gray-300"
                >
                  {showConfirmPwd ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                </button>
              </div>

              {error && <div className="text-red-400 text-xs text-center p-2 bg-red-900/30 border border-red-800 rounded">{error}</div>}
              {success && <div className="text-green-400 text-xs text-center p-2 bg-green-900/30 border border-green-800 rounded">{success}</div>}

              <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg mt-2 transition">
                Activate Account
              </button>
            </form>

            <div className="mt-4 text-center text-sm border-t border-gray-800 pt-4">
              <button onClick={() => setView('signin')} className="text-gray-500 hover:text-white transition">← Back to Sign In</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}