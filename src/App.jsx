import React from "react";
import LoginPage from "./LoginPage";
import MainLayout from "./MainLayout";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import AuthPage from "./Auth";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/main" element={<MainLayout />} />
        <Route path="/auth" element={<AuthPage />} />
        {/* Add more routes as needed */}
      </Routes>
    </Router>
  );
}
export default App;
