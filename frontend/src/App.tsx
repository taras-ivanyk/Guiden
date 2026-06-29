import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import Layout from './components/Layout';
import StravaCallback from './auth/StravaCallback';
import HomePage from './pages/HomePage';
import AnalyzePage from './pages/AnalyzePage';
import PlanPage from './pages/PlanPage';
import ProfilePage from './pages/ProfilePage';
import './App.css';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/auth/callback" element={<StravaCallback />} />
          <Route element={<Layout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/plan" element={<PlanPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
