const API = "http://127.0.0.1:8000";

export async function getAdminAlerts() {
    const res = await fetch(`${API}/alerts/admin`);
    return await res.json();
}

export async function getGuardAlerts() {
    const res = await fetch(`${API}/alerts/guard`);
    return await res.json();
}

export async function getResidentAlerts(id) {
    const res = await fetch(`${API}/alerts/resident/${id}`);
    return await res.json();
}

export async function verifyAlert(id) {
    await fetch(`${API}/alerts/${id}/verify`, {
        method: "POST"
    });
}

export async function resolveAlert(id) {
    await fetch(`${API}/alerts/${id}/resolve`, {
        method: "POST"
    });
}