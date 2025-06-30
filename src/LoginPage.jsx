import React from "react";
import { useNavigate } from "react-router-dom";
import "./LoginPage.css";
import { Link } from "react-router-dom";

function LoginPage() {
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    navigate("/main");
  };
  return (
    <div className="login-page">
      <h1>Login</h1>
      <form className="login-form" onSubmit={handleSubmit}>
        <div className="form-block">
          <label>Username</label>
          <input type="text" placeholder="Username" />
        </div>
        <div className="form-block">
          <label>Password</label>
          <input type="password" placeholder="Password" />
        </div>
        <button type="submit">Login</button>
        <spam>
          Dont't you have a account?
          <Link to="/" className="sign-up">
            Sign Up
          </Link>
        </spam>
      </form>
    </div>
  );
}
export default LoginPage;
