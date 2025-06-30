import React from "react";
import LoginPage from "./LoginPage";
import SignUpPage from "./SignUpPage";
import MainLayout from "./MainLayout";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SignUpPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/main" element={<MainLayout />} />
        {/* Add more routes as needed */}
      </Routes>
    </Router>
  );
}
export default App;
