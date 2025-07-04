import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  const [showFeedback, setShowFeedback] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const feedbackRef = useRef(null);
  const dropdownRef = useRef(null);
  const logoutRef = useRef(null);
  const navigate = useNavigate();

  // Close feedback, dropdown, and logout on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (feedbackRef.current && !feedbackRef.current.contains(event.target)) {
        setShowFeedback(false);
      }
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
      if (logoutRef.current && !logoutRef.current.contains(event.target)) {
        setShowLogoutConfirm(false);
      }
    };

    if (showFeedback || showDropdown || showLogoutConfirm) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showFeedback, showDropdown, showLogoutConfirm]);

  // Logout handler: calls backend and clears cookies
  const handleLogout = async () => {
    setShowLogoutConfirm(false);
    try {
      const res = await fetch("http://localhost:8000/logout", {
        method: "DELETE",
        credentials: "include",
      });
      if (res.ok) {
        navigate("/login");
      } else {
        alert("Logout failed");
      }
    } catch (err) {
      alert("Error connecting to backend");
    }
  };

  return (
    <div className="navbar-container">
      {/* === Top Nav Icons === */}
      <div className="navbar-icons">
        <button onClick={() => setShowFeedback(true)}>💬</button>
        <div className="profile-dropdown" ref={dropdownRef}>
          <button onClick={() => setShowDropdown((prev) => !prev)}>👤</button>
          {showDropdown && (
            <div className="dropdown-menu">
              <button>👁️ Profile</button>
              <button>⚙️ Settings</button>
              <button
                onClick={() => setShowLogoutConfirm(true)}
                className="danger"
              >
                🚪 Logout
              </button>
            </div>
          )}
        </div>
      </div>

      {/* === Feedback Component === */}
      {showFeedback && (
        <div className="feedback-box" ref={feedbackRef}>
          <h3>
            <strong>FeedBack</strong>
          </h3>
          <p>Your feedback would help us improve the App</p>
          <textarea placeholder="Description..." rows="5" />
          <button className="submit-btn">Submit</button>
        </div>
      )}

      {/* === Logout Confirmation === */}
      {showLogoutConfirm && (
        <div className="logout-box" ref={logoutRef}>
          <h3>
            <strong>Log out</strong>
          </h3>
          <p>Are you sure you wanna Log out!!!</p>
          <div className="logout-actions">
            <button onClick={() => setShowLogoutConfirm(false)}>Cancel</button>
            <button className="danger" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
