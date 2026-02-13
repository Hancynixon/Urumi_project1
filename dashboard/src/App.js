import React, { useEffect, useState } from "react";

function App() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(false);

  const API_BASE = "http://127.0.0.1:8000";

  const fetchStores = async () => {
    const res = await fetch(`${API_BASE}/stores`);
    const data = await res.json();
    setStores(data.stores || []);
  };

  const createStore = async () => {
    setLoading(true);
    await fetch(`${API_BASE}/stores`, { method: "POST" });
    await fetchStores();
    setLoading(false);
  };

  const deleteStore = async (id) => {
    await fetch(`${API_BASE}/stores/${id}`, { method: "DELETE" });
    await fetchStores();
  };

  useEffect(() => {
    fetchStores();
  }, []);

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Store Provisioning Dashboard</h1>

      <button onClick={createStore} disabled={loading}>
        {loading ? "Provisioning..." : "Create New Store"}
      </button>

      <h2 style={{ marginTop: "30px" }}>Existing Stores</h2>

      <table border="1" cellPadding="10" style={{ marginTop: "10px" }}>
        <thead>
          <tr>
            <th>Store ID</th>
            <th>Status</th>
            <th>URL</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {stores.map((store) => (
            <tr key={store.store_id}>
              <td>{store.store_id}</td>
              <td>{store.status}</td>
              <td>
                <a href={store.url} target="_blank" rel="noreferrer">
                  Open Store
                </a>
              </td>
              <td>
                <button onClick={() => deleteStore(store.store_id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
