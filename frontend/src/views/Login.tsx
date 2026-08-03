import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Music, Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { GoogleLogin } from '@react-oauth/google';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useUser } from '../context/UserContext';
import { apiClient } from '../api/client';
import styles from './Login.module.css';



export function Login() {
  const navigate = useNavigate();
  const { profile, isAuthenticated, login } = useUser();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // If already logged in, redirect away from login
  useEffect(() => {
    if (isAuthenticated) {
      if (profile.isOnboardingComplete) {
        navigate(profile.role === 'TEACHER' ? '/teacher' : '/dashboard');
      } else {
        navigate('/onboarding');
      }
    }
  }, [isAuthenticated, profile, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const { data } = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      await login(data.access_token, data.refresh_token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to login');
    }
  };

  const handleGoogleSuccess = async (credentialResponse: any) => {
    setError('');
    try {
      const { data } = await apiClient.post('/auth/google', {
        credential: credentialResponse.credential
      });
      await login(data.access_token, data.refresh_token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Google authentication failed');
    }
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.visualSide}>
        <motion.div 
          className={styles.brandContent}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className={styles.brandLogo}>
            <Music size={32} color="var(--text-primary)" />
            Melodix
          </div>
          <h2 className={styles.brandTagline}>Learn piano with AI.</h2>
          
          <div className={styles.brandFeatures}>
            <div className={styles.featureItem}>
              <Check size={20} className={styles.featureIcon} />
              <span>Personalized lessons</span>
            </div>
            <div className={styles.featureItem}>
              <Check size={20} className={styles.featureIcon} />
              <span>Real-time AI feedback</span>
            </div>
            <div className={styles.featureItem}>
              <Check size={20} className={styles.featureIcon} />
              <span>Learn any song</span>
            </div>
            <div className={styles.featureItem}>
              <Check size={20} className={styles.featureIcon} />
              <span>Track your progress</span>
            </div>
          </div>
        </motion.div>
      </div>
      
      <div className={styles.formSide}>
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className={styles.header}>
            <h1 className={styles.title}>Welcome back</h1>
            <p className={styles.subtitle}>Log in to continue your piano journey.</p>
          </div>

          <form className={styles.form} onSubmit={handleLogin}>
            {error && <div className={styles.error}>{error}</div>}
            <Input 
              label="Email" 
              type="email" 
              placeholder="sarah@example.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
            <Input 
              label="Password" 
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
            
            <Link to="/forgot-password" className={styles.forgotPassword}>
              Forgot password?
            </Link>

            <Button type="submit" variant="primary">
              Log In
            </Button>
          </form>

          <div className={styles.divider}>Or continue with</div>

          <div className={styles.oauthGroup}>
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Google authentication failed')}
              theme="filled_black"
              size="large"
              width="100%"
              text="continue_with"
            />
          </div>

          <div className={styles.footer}>
            Don't have an account? <Link to="/signup" className={styles.footerLink}>Sign up</Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
