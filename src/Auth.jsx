import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function AuthPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const response = location.state?.response;
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [verifying, setVerifying] = useState(false);

  if (!response) {
    return (
      <div>
        <h2>No authentication response found.</h2>
        <button onClick={() => navigate("/login")}>Back to Login</button>
      </div>
    );
  }

  // Handler for OTP verification
  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setVerifying(true);
    try {
      // Send GET request to /verify-mfa?mfa_code=...
      const res = await fetch(
        `http://localhost:8000/verify-mfa?mfa_code=${encodeURIComponent(otp)}`,
        {
          method: "GET",
          credentials: "include",
        }
      );
      const data = await res.json();
      if (res.ok) {
        navigate("/main");
      } else {
        setError(data.detail || "Verification failed");
      }
    } catch (err) {
      setError("Error connecting to backend");
    }
    setVerifying(false);
  };

  const isNewUser =
    response.message === "New user registered" && response.MFAuri;
  const isExistingUser =
    response.message === "Existing user, proceed to MFA verification";

  return (
    <div
      style={{
        margin: "40px auto",
        maxWidth: 400,
        background: "#fff",
        padding: 24,
        borderRadius: 8,
      }}
    >
      {isNewUser && (
        <>
          <h2>Welcome, new user!</h2>
          <p>Scan this QR code in your Authenticator app to set up MFA:</p>
          <img
            src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(
              response.MFAuri.trim()
            )}&size=200x200`}
            alt="MFA QR"
          />
          <form onSubmit={handleVerify} style={{ marginTop: 20 }}>
            <label>
              Enter OTP from Authenticator:
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                style={{ width: "100%", marginTop: 8, marginBottom: 8 }}
                required
              />
            </label>
            <button type="submit" disabled={verifying}>
              {verifying ? "Verifying..." : "Verify"}
            </button>
            {error && (
              <div style={{ color: "red", marginTop: 10 }}>{error}</div>
            )}
          </form>
        </>
      )}

      {isExistingUser && (
        <>
          <h2>MFA Verification</h2>
          <form onSubmit={handleVerify} style={{ marginTop: 20 }}>
            <label>
              Enter OTP from Authenticator:
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                style={{ width: "100%", marginTop: 8, marginBottom: 8 }}
                required
              />
            </label>
            <button type="submit" disabled={verifying}>
              {verifying ? "Verifying..." : "Verify"}
            </button>
            {error && (
              <div style={{ color: "red", marginTop: 10 }}>{error}</div>
            )}
          </form>
        </>
      )}

      {!isNewUser && !isExistingUser && (
        <>
          <h2>Login Response</h2>
          <pre style={{ background: "#eee", padding: 12, borderRadius: 4 }}>
            {JSON.stringify(response, null, 2)}
          </pre>
          <button style={{ marginTop: 20 }} onClick={() => navigate("/login")}>
            Back to Login
          </button>
        </>
      )}
    </div>
  );
}
