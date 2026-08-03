import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Login } from './views/Login';
import { Dashboard } from './views/Dashboard';
import { Studio } from './views/Studio';
import { Library } from './views/Library';
import { SongDetails } from './views/SongDetails';
import { PracticeSummary } from './views/PracticeSummary';
import { TeacherDashboard } from './views/TeacherDashboard';
import { AIProcessing } from './views/AIProcessing';
import { Learn } from './views/Learn';
import { Splash } from './views/Splash';
import { Profile } from './views/Profile';
import { Progress } from './views/Progress';
import { Upload } from './views/Upload';
import { Signup } from './views/Signup';
import { UserProvider, useUser } from './context/UserContext';
import { Onboarding } from './views/Onboarding';

// New V3 Components
import { Classes } from './views/Classes';
import { ClassDetail } from './views/ClassDetail';
import { Students } from './views/Students';
import { StudentDetail } from './views/StudentDetail';
import { Lessons } from './views/Lessons';
import { UploadLesson } from './views/UploadLesson';
import { Assignments } from './views/Assignments';
import { CreateAssignment } from './views/CreateAssignment';
import { Friends } from './views/Friends';
import { Leaderboards } from './views/Leaderboards';

function AppRoutes() {
  const { profile, isAuthenticated, isLoading } = useUser();
  const { activeRole, isOnboardingComplete } = profile;

  // Show nothing while restoring session
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: 'var(--bg-primary, #0a0a0a)', 
        color: 'var(--text-secondary, #888)', fontSize: '16px'
      }}>
        Loading...
      </div>
    );
  }

  // Route guard for authenticated users
  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (!isAuthenticated) return <Navigate to="/login" />;
    if (!isOnboardingComplete) return <Navigate to="/onboarding" />;
    return children;
  };

  return (
    <Routes>
      <Route path="/" element={<Splash />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/onboarding" element={isAuthenticated ? <Onboarding /> : <Navigate to="/login" />} />
      
      {/* Student Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><Layout role="student"><Dashboard /></Layout></ProtectedRoute>} />
      <Route path="/library" element={<ProtectedRoute><Layout role="student"><Library /></Layout></ProtectedRoute>} />
      <Route path="/learn" element={<ProtectedRoute><Layout role="student"><Learn /></Layout></ProtectedRoute>} />
      <Route path="/progress" element={<ProtectedRoute><Layout role="student"><Progress /></Layout></ProtectedRoute>} />
      <Route path="/friends" element={<ProtectedRoute><Layout role="student"><Friends /></Layout></ProtectedRoute>} />
      <Route path="/leaderboards" element={<ProtectedRoute><Layout role="student"><Leaderboards /></Layout></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Layout role={activeRole === 'teacher' ? 'teacher' : 'student'}><Profile /></Layout></ProtectedRoute>} />
      <Route path="/song/:songId" element={<ProtectedRoute><Layout role="student"><SongDetails /></Layout></ProtectedRoute>} />
      <Route path="/upload" element={<ProtectedRoute><Layout role="student"><Upload /></Layout></ProtectedRoute>} />
      
      {/* Teacher Routes */}
      <Route path="/teacher" element={<ProtectedRoute><Layout role="teacher"><TeacherDashboard /></Layout></ProtectedRoute>} />
      <Route path="/teacher/students" element={<ProtectedRoute><Layout role="teacher"><Students /></Layout></ProtectedRoute>} />
      <Route path="/teacher/students/:id" element={<ProtectedRoute><Layout role="teacher"><StudentDetail /></Layout></ProtectedRoute>} />
      <Route path="/teacher/classes" element={<ProtectedRoute><Layout role="teacher"><Classes /></Layout></ProtectedRoute>} />
      <Route path="/teacher/classes/:id" element={<ProtectedRoute><Layout role="teacher"><ClassDetail /></Layout></ProtectedRoute>} />
      <Route path="/teacher/lessons" element={<ProtectedRoute><Layout role="teacher"><Lessons /></Layout></ProtectedRoute>} />
      <Route path="/teacher/lessons/upload" element={<ProtectedRoute><Layout role="teacher"><UploadLesson /></Layout></ProtectedRoute>} />
      <Route path="/teacher/assignments" element={<ProtectedRoute><Layout role="teacher"><Assignments /></Layout></ProtectedRoute>} />
      <Route path="/teacher/assignments/create" element={<ProtectedRoute><Layout role="teacher"><CreateAssignment /></Layout></ProtectedRoute>} />
      <Route path="/teacher/analytics" element={<ProtectedRoute><Layout role="teacher"><TeacherDashboard /></Layout></ProtectedRoute>} />
      
      {/* Full Screen Routes */}
      <Route path="/studio/:songId" element={<Studio />} />
      <Route path="/summary/:songId" element={<PracticeSummary />} />
      <Route path="/processing" element={<AIProcessing />} />
      
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

function App() {
  return (
    <UserProvider>
      <Router>
        <AppRoutes />
      </Router>
    </UserProvider>
  );
}

export default App;
