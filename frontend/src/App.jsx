import { useState } from 'react';
import GlobalStyles from './components/GlobalStyles';
import Login from './pages/Login';
import ResidentPortal from './pages/ResidentPortal';
import GuardDashboard from './pages/GuardDashboard';
import AdminTower from './pages/AdminTower';

export default function App() {

  const storedUser = JSON.parse(sessionStorage.getItem("user"));

  const initialView = storedUser
    ? (
        storedUser.resident
          ? "Resident"
          : storedUser.guard
          ? "Security"
          : storedUser.admin
          ? "Admin"
          : "login"
      )
    : "login";

  const [currentView, setCurrentView] = useState(initialView);

  const handleLogin = (role) => {

    setCurrentView(role);

  };

  const handleLogout = () => {

    sessionStorage.removeItem("user");

    setCurrentView("login");

  };

  return (
    <>
      <GlobalStyles />

      {currentView === "login" && (
        <Login onLogin={handleLogin} />
      )}

      {currentView === "Resident" && (
        <ResidentPortal onLogout={handleLogout} />
      )}

      {currentView === "Security" && (
        <GuardDashboard onLogout={handleLogout} />
      )}

      {currentView === "Admin" && (
        <AdminTower onLogout={handleLogout} />
      )}

    </>
  );
}