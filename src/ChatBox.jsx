import React, { useState } from "react";
import TicketForm from "./TicketForm";
import "./ChatBox.css";

const ChatBox = () => {
  const [showTicketForm, setShowTicketForm] = useState(false);

  const toggleForm = () => setShowTicketForm((prev) => !prev);

  return (
    <>
      {showTicketForm && (
        <div
          className="ticket-overlay"
          onClick={() => setShowTicketForm(false)}
        >
          <div className="ticket-popup" onClick={(e) => e.stopPropagation()}>
            <TicketForm />
          </div>
        </div>
      )}
      <div className="chatbox">
        <p>Ask anything ...</p>
        <button className="chatbox-btn" onClick={toggleForm}>
          +
        </button>
      </div>
    </>
  );
};

export default ChatBox;
