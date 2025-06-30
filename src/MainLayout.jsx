import React from "react";
import Sidebar from "./sidebar";
import Navbar from "./Navbar";
import ChatBox from "./ChatBox";
import "./MainLayout.css";
import ChatWithTicket from "./ChatWithTicket";

export default function MainLayout() {
  return (
    <div className="main-layout">
      <Sidebar />
      <div className="main-content">
        <Navbar />
        <div className="page-body">
          <ChatWithTicket />
          {/* You can insert ChatArea or ChatInput here later */}
        </div>
      </div>
    </div>
  );
}
