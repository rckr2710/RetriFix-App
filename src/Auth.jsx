import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function AuthPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const response = location.state?.response;

  if (!response) {
    return (
      <div>
        <h2>No authentication response found.</h2>
        <button onClick={() => navigate("/login")}>Back to Login</button>
      </div>
    );
  }

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
      {response.message === "New user registered" && response.MFAuri ? (
        <>
          <h2>Welcome, new user!</h2>
          <p>Scan this QR code in your Authenticator app to set up MFA:</p>
          <img
            src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(
              response.MFAuri
            )}&size=200x200`}
            alt="MFA QR"
          />
          <p style={{ wordBreak: "break-all", fontSize: 12, marginTop: 10 }}>
            {response.MFAuri}
          </p>
          <button style={{ marginTop: 20 }} onClick={() => navigate("/login")}>
            Proceed to Login
          </button>
        </>
      ) : response.message === "Existing user, proceed to MFA verification" ? (
        <>
          <h2>MFA Verification</h2>
          <p>Please enter your MFA code on the next screen.</p>
          <button style={{ marginTop: 20 }} onClick={() => navigate("/login")}>
            Go to MFA Login
          </button>
        </>
      ) : (
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
