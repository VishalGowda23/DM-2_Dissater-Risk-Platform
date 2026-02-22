import { useState } from 'react';
import { AlertTriangle, LogIn, UserPlus, Shield, Eye, EyeOff, ArrowRight } from 'lucide-react';
import { useAuth, type User } from '@/lib/auth';
import { useLang, LangToggle } from '@/lib/i18n';

export default function AuthPage() {
  const { login, signup } = useAuth();
  const { t } = useLang();
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<User['role']>('viewer');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'login') {
        const ok = await login(email, password);
        if (!ok) setError('Invalid credentials. Try admin@prakalp.in / admin123');
      } else {
        if (!name.trim()) { setError('Name is required'); setLoading(false); return; }
        const ok = await signup(name, email, password, role);
        if (!ok) setError('An account with this email already exists');
      }
    } catch {
      setError('Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f0] flex flex-col">
      {/* Top bar */}
      <div className="bg-white border-b-4 border-black">
        <div className="max-w-[1920px] mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-black text-white p-2">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-black tracking-tight uppercase">
                {t('appName')}
              </h1>
              <p className="text-[10px] sm:text-xs font-bold text-gray-500 uppercase tracking-wider">
                {t('appSubtitle')}
              </p>
            </div>
          </div>
          <LangToggle />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-md">
          {/* Auth card */}
          <div className="bg-white border-2 border-black shadow-[6px_6px_0_0_rgba(0,0,0,1)]">
            {/* Card header */}
            <div className="bg-white p-4 sm:p-6 border-b-2 border-black">
              <div className="flex items-center gap-3 mb-2">
                <Shield className="w-7 h-7 text-black" />
                <h2 className="text-xl sm:text-2xl font-black uppercase tracking-wider text-black">
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                </h2>
              </div>
              <p className="text-sm text-gray-500 font-medium">
                {mode === 'login'
                  ? 'Access the disaster intelligence dashboard'
                  : 'Register for platform access'}
              </p>
            </div>

            {/* Mode toggle */}
            <div className="grid grid-cols-2 border-b-2 border-black">
              <button
                onClick={() => { setMode('login'); setError(''); }}
                className={`py-3 font-black uppercase text-sm tracking-wider transition-colors flex items-center justify-center gap-2 ${
                  mode === 'login'
                    ? 'bg-black text-white'
                    : 'bg-white text-gray-500 hover:bg-gray-100'
                }`}
              >
                <LogIn className="w-4 h-4" />
                Sign In
              </button>
              <button
                onClick={() => { setMode('signup'); setError(''); }}
                className={`py-3 font-black uppercase text-sm tracking-wider transition-colors flex items-center justify-center gap-2 border-l-2 border-black ${
                  mode === 'signup'
                    ? 'bg-black text-white'
                    : 'bg-white text-gray-500 hover:bg-gray-100'
                }`}
              >
                <UserPlus className="w-4 h-4" />
                Sign Up
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4">
              {/* Name (signup only) */}
              {mode === 'signup' && (
                <div className="space-y-1.5">
                  <label className="text-xs font-black uppercase tracking-wider text-gray-500">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full px-4 py-3 border-2 border-black bg-white font-medium text-sm placeholder:text-gray-400 focus:outline-none focus:ring-0 focus:bg-gray-50 transition-colors"
                    required
                  />
                </div>
              )}

              {/* Email */}
              <div className="space-y-1.5">
                <label className="text-xs font-black uppercase tracking-wider text-gray-500">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="admin@prakalp.in"
                  className="w-full px-4 py-3 border-2 border-black bg-white font-medium text-sm placeholder:text-gray-400 focus:outline-none focus:ring-0 focus:bg-gray-50 transition-colors"
                  required
                />
              </div>

              {/* Password */}
              <div className="space-y-1.5">
                <label className="text-xs font-black uppercase tracking-wider text-gray-500">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 border-2 border-black bg-white font-medium text-sm placeholder:text-gray-400 focus:outline-none focus:ring-0 focus:bg-gray-50 transition-colors pr-12"
                    required
                    minLength={4}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-black transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Role (signup only) */}
              {mode === 'signup' && (
                <div className="space-y-1.5">
                  <label className="text-xs font-black uppercase tracking-wider text-gray-500">
                    Role
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['admin', 'operator', 'viewer'] as const).map(r => (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setRole(r)}
                        className={`py-2.5 text-xs font-black uppercase border-2 transition-all ${
                          role === r
                            ? 'bg-black text-white border-black'
                            : 'bg-white text-gray-600 border-gray-300 hover:border-black'
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="bg-red-50 border-2 border-red-500 p-3 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
                  <span className="text-sm font-bold text-red-700">{error}</span>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-black text-white py-3.5 font-black uppercase tracking-wider text-sm flex items-center justify-center gap-2 hover:bg-gray-800 transition-colors active:translate-x-[2px] active:translate-y-[2px] disabled:opacity-50 disabled:cursor-not-allowed border-2 border-black"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    {mode === 'login' ? 'Sign In' : 'Create Account'}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Demo hint */}
            <div className="border-t-2 border-black px-4 sm:px-6 py-4 bg-gray-50">
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-1.5 shrink-0 animate-pulse" />
                <div className="text-xs text-gray-500">
                  <span className="font-black uppercase">Demo Access</span>
                  <br />
                  <span className="font-mono">admin@prakalp.in</span> / <span className="font-mono">admin123</span>
                </div>
              </div>
            </div>
          </div>

          {/* Footer info */}
          <div className="mt-6 text-center">
            <div className="inline-flex items-center gap-2 bg-white border-2 border-black px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
              <Shield className="w-3.5 h-3.5" />
              Pune Disaster Intelligence Platform
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
