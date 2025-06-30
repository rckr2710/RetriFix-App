import React from "react";
import "./TicketForm.css";

const TicketForm = () => {
  return (
    <form className="ticket-form">
      <label>Issue</label>
      <input type="text" placeholder="Enter issue" />

      <label>Description</label>
      <textarea placeholder="Enter description" />

      <label>Tags</label>
      <input type="text" placeholder="Add tags" />

      <label>Upload</label>
      <input type="file" />
    </form>
  );
};

export default TicketForm;
