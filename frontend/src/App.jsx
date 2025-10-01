import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import QuestionListPage from './pages/QuestionListPage';
import QuestionDetailPage from './pages/QuestionDetailPage';
import ProfilePage from './pages/ProfilePage';
import ProfileUpdatePage from './pages/ProfileUpdatePage';
import MatchingPage from './pages/MatchingPage';
import MatchingProgressPage from './pages/MatchingProgressPage';
import CollaborationPage from './pages/CollaborationPage';

import AppLayout from './components/AppLayout';

const isAuthenticated = () => {
  // dummy authentication check
  return false;
};

const ProtectedRoute = () => {
  return isAuthenticated() ? <Outlet /> : <Navigate to="/login" replace />;
};

const AuthRoute = () => {
    return isAuthenticated() ? <Navigate to="/home" replace /> : <Outlet />;
};

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AuthRoute />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route path="/home" element={<AppLayout> <HomePage/> </AppLayout>} />

          <Route path="/profile" element={<AppLayout> <ProfilePage /> </AppLayout>} />
          <Route path="/profile/edit" element={<AppLayout> <ProfileUpdatePage /> </AppLayout>} />

          <Route path="/questions" element={<AppLayout> <QuestionListPage /> </AppLayout>} />
          <Route path="/questions/:id" element={<AppLayout> <QuestionDetailPage /> </AppLayout>} />

          <Route path="/matching" element={<AppLayout> <MatchingPage /> </AppLayout>} />
          <Route path="/matching/finding" element={<AppLayout> <MatchingProgressPage /> </AppLayout>} />

          <Route path="/collaboration" element={<AppLayout> <CollaborationPage /> </AppLayout>} />
        </Route>

        <Route path="*" element={<h1>404 Not Found</h1>} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;