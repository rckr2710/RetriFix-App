import React, { useState } from "react";
import { FiPlus } from "react-icons/fi";
import "./ChatWithTicket.css";

function ChatWithTicket() {
  const [showTicketForm, setShowTicketForm] = useState(false);
  const [issue, setIssue] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [files, setFiles] = useState([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    // submission logic
    setIssue("");
    setDescription("");
    setTags("");
    setFiles([]);
    setShowTicketForm(false);
  };

  return (
    <div className="chat-ticket-wrapper">
      <div className="chatbox">
        <textarea
          className="chatbox-input"
          placeholder="Ask anything ..."
          rows={4}
        ></textarea>
        <button
          className="plus-button"
          onClick={() => setShowTicketForm(!showTicketForm)}
        >
          <FiPlus />
        </button>
      </div>

      {showTicketForm && (
        <form className="ticket-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={issue}
            onChange={(e) => setIssue(e.target.value)}
            placeholder="Issue"
            className="ticket-input"
          />

          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description"
            className="ticket-textarea"
            rows={4}
          ></textarea>

          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="Tags"
            className="ticket-input"
          />

          <input
            type="file"
            multiple
            onChange={(e) => setFiles(Array.from(e.target.files))}
            className="ticket-file"
          />

          <div className="ticket-buttons">
            <button type="submit" className="ticket-button">
              Submit
            </button>
            <button
              type="button"
              className="ticket-button"
              onClick={() => setShowTicketForm(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default ChatWithTicket;
