import React, { useState } from "react";
import "./Sidebar.css"; // Import your custom CSS

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  const items = [
    { icon: "💬", label: "New Chat" },
    { icon: "🔍", label: "Search Chat" },
    { icon: "🕓", label: "History" },
  ];

  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        <button className="toggle-btn" onClick={() => setCollapsed(!collapsed)}>
          ☰
        </button>
        {!collapsed}
      </div>
      <div className="sidebar-items">
        {items.map((item, index) => (
          <button key={index} className="sidebar-item">
            <span className="icon">{item.icon}</span>
            {!collapsed && <span className="label">{item.label}</span>}
          </button>
        ))}
      </div>
    </div>
  );
}
