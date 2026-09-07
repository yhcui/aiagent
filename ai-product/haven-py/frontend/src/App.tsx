import { Navigate, Route, Routes } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import IdeasPage from './pages/IdeasPage';
import Sidebar from './components/layout/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/ideas"
        element={
          <ProtectedRoute>
            <div className="app-shell">
              <Sidebar />
              <main className="app-main">
                <IdeasPage />
              </main>
            </div>
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/ideas" replace />} />
    </Routes>
  );
}
