import React from "react";
import "./SignUpPage.css";
import { Link } from "react-router-dom";

function SignUpPage() {
  return (
    <div className="signup-page">
      <h1>Sign Up</h1>
      <form className="signup-form">
        <div className="form-block">
          <label>Username</label>
          <input type="text" placeholder="Username" />
        </div>
        <div className="form-block">
          <label>Password</label>
          <input type="password" placeholder="Password" />
        </div>
        <button>Sign Up</button>
        <span>
          Already have an account?{" "}
          <Link to="/login" className="login-link">
            Login
          </Link>
        </span>
      </form>
    </div>
  );
}
export default SignUpPage;
