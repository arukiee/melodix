import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Music, Check, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { motion } from 'framer-motion';
import { GoogleLogin } from '@react-oauth/google';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useUser } from '../context/UserContext';
import { apiClient } from '../api/client';
import styles from './Signup.module.css';

export function Signup() {
  const navigate = useNavigate();
  const { profile, isAuthenticated, login } = useUser();
  
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // If already logged in, redirect away from signup
  useEffect(() => {
    if (isAuthenticated) {
      if (profile.isOnboardingComplete) {
        navigate(profile.role === 'TEACHER' ? '/teacher' : '/dashboard');
      } else {
        navigate('/onboarding');
      }
    }
  }, [isAuthenticated, profile, navigate]);

  // Password validation checks
  const isLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSymbol = /[^A-Za-z0-9]/.test(password);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!isLength || !hasUpper || !hasNumber || !hasSymbol) {
      setError('Please ensure your password meets all requirements.');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    
    if (!agreeTerms) {
      setError('You must agree to the Terms of Service.');
      return;
    }

    setLoading(true);
    try {
      // 1. Register the user
      await apiClient.post('/auth/register', {
        email,
        password,
        full_name: fullName
      });
      
      // 2. Login to get tokens
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const { data } = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      await login(data.access_token, data.refresh_token);
      // login will trigger the useEffect to navigate based on onboarding
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create account.');
    } finally {
      setLoading(false);
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
    <div className={styles.signupContainer}>
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
            <h1 className={styles.title}>Create an account</h1>
            <p className={styles.subtitle}>Start your piano journey with Melodix.</p>
          </div>

          {error && (
            <div style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: '#ef4444', padding: '12px', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}>
              <AlertCircle size={18} /> {error}
            </div>
          )}

          <form className={styles.form} onSubmit={handleSignup}>
            <Input 
              label="Full Name" 
              type="text" 
              placeholder="Sarah Jenkins" 
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required 
            />
            <Input 
              label="Email" 
              type="email" 
              placeholder="sarah@example.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
            
            <div style={{ position: 'relative' }}>
              <Input 
                label="Password" 
                type={showPassword ? 'text' : 'password'} 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: 'absolute', right: '12px', top: '34px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            
            {password.length > 0 && (
              <div style={{ fontSize: '0.8rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginBottom: '16px' }}>
                <span style={{ color: isLength ? '#10b981' : 'var(--text-secondary)' }}>{isLength ? '✓' : '○'} 8+ characters</span>
                <span style={{ color: hasUpper ? '#10b981' : 'var(--text-secondary)' }}>{hasUpper ? '✓' : '○'} One uppercase</span>
                <span style={{ color: hasNumber ? '#10b981' : 'var(--text-secondary)' }}>{hasNumber ? '✓' : '○'} One number</span>
                <span style={{ color: hasSymbol ? '#10b981' : 'var(--text-secondary)' }}>{hasSymbol ? '✓' : '○'} One symbol</span>
              </div>
            )}

            <Input 
              label="Confirm Password" 
              type={showPassword ? 'text' : 'password'} 
              placeholder="••••••••" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required 
            />

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
              <input 
                type="checkbox" 
                id="terms" 
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                style={{ width: '16px', height: '16px', cursor: 'pointer' }}
              />
              <label htmlFor="terms" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                I agree to the <a href="#" style={{ color: 'var(--accent-primary)' }}>Terms of Service</a>
              </label>
            </div>

            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? 'Creating account...' : 'Sign Up'}
            </Button>
          </form>

          <div className={styles.divider}>Or continue with</div>

          <div className={styles.oauthGroup} style={{ display: 'flex', justifyContent: 'center' }}>
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Google sign-in failed.')}
              useOneTap
              shape="pill"
            />
          </div>

          <div className={styles.footer}>
            Already have an account? <Link to="/login" className={styles.footerLink}>Log in</Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
