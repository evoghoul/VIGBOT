"use client";

import React, { useState, useEffect } from 'react';
import { adminLogin } from '@/actions/admin';
import { useRouter } from 'next/navigation';
import { 
  Lock, 
  ShieldAlert, 
  Key, 
  User, 
  ShieldCheck, 
  Eye, 
  EyeOff, 
  Clock, 
  Sparkles, 
  CheckCircle2, 
  Cpu, 
  Database,
  ArrowRight
} from 'lucide-react';

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');
  const router = useRouter();

  // Clock effect for Indian Standard Time
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true
        }) + ' IST'
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await adminLogin(username, password);
      if (res.success) {
        localStorage.setItem('adminSession', JSON.stringify(res.admin));
        router.push('/admin');
      } else {
        setError(res.error || 'Invalid administrator credentials. Access denied.');
      }
    } catch (err) {
      setError('A secure connection error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = () => {
    setUsername('admin');
    setPassword('admin123');
    setError('');
  };

  return (
    <div className="min-h-dvh flex flex-col items-center justify-center bg-slate-950 text-slate-100 p-4 relative overflow-hidden font-sans selection:bg-blue-500/30 selection:text-white">
      {/* Formal Ambient Grid Background & Subtle Radial Glow */}
      <div className="absolute inset-0 [background-image:radial-gradient(rgba(59,130,246,0.08)_1px,transparent_1px)] [background-size:28px_28px] pointer-events-none opacity-60" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-blue-600/10 rounded-full blur-[130px] pointer-events-none" />
      <div className="absolute -bottom-24 right-10 w-96 h-96 bg-purple-600/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Institutional Top Crest & Regulatory Badge */}
      <div className="mb-6 text-center space-y-2 relative z-10 animate-in fade-in-50 slide-in-from-top-3 duration-300">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[11px] font-semibold text-blue-300 tracking-wide uppercase">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>VFSTR Institutional Governance Gateway</span>
        </div>
        <p className="text-xs text-slate-400 font-medium">Statutory University Nodal Officer Portal • Clause 2.1 RLAC Protected</p>
      </div>

      {/* Main Secure Login Card */}
      <div className="max-w-md w-full bg-slate-900/90 backdrop-blur-xl rounded-2xl shadow-2xl shadow-black/60 overflow-hidden border border-slate-700/80 relative z-10 animate-in fade-in-50 zoom-in-95 duration-300">
        {/* Card Header Strip */}
        <div className="bg-slate-900 px-6 pt-8 pb-6 text-center border-b border-slate-700/80 relative">
          <div className="mx-auto w-14 h-14 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-center justify-center mb-3 relative group shadow-inner shadow-blue-500/10">
            <span className="absolute -inset-1 rounded-2xl bg-blue-500/20 blur-sm animate-pulse pointer-events-none" />
            <Lock className="w-7 h-7 text-blue-400 relative z-10" />
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">Nodal Officer Portal</h1>
          <p className="text-slate-400 text-xs mt-1.5 font-medium">Secure Access for University Administrators & Ombudsmen</p>

          {/* Institutional Trust Pills */}
          <div className="mt-4 flex flex-wrap justify-center items-center gap-2 text-[10px] font-mono">
            <span className="px-2 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-emerald-400 flex items-center gap-1 font-semibold">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" /> TLS 1.3
            </span>
            <span className="px-2 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-blue-400 flex items-center gap-1 font-semibold">
              <ShieldCheck className="w-3 h-3 text-blue-400" /> RLS 2.1 Active
            </span>
            <span className="px-2 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-purple-400 flex items-center gap-1 font-semibold">
              <Database className="w-3 h-3 text-purple-400" /> Neon DB
            </span>
          </div>
        </div>

        {/* Card Form Body */}
        <div className="p-6 sm:p-7 space-y-5 bg-slate-900/60">
          <form onSubmit={handleLogin} className="space-y-5">
            {error && (
              <div className="bg-rose-500/10 border border-rose-500/25 text-rose-300 px-4 py-3 rounded-xl flex items-center gap-3 text-xs animate-in fade-in-50">
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                <p className="font-medium">{error}</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5" htmlFor="username">
                  Administrative Roll / Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <User className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    id="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    placeholder="Enter admin ID (e.g. admin)"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300" htmlFor="password">
                    Security Key / Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-[11px] text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    <span>{showPassword ? 'Hide' : 'Show'}</span>
                  </button>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Key className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-10 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all font-mono"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>

            {/* Quick Demo Credentials Assistant */}
            <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <span className="text-[11px] text-slate-400 font-medium">Testing Command Center?</span>
                <div className="text-[10px] font-mono text-slate-500">ID: admin • Key: admin123</div>
              </div>
              <button
                type="button"
                onClick={fillDemoCredentials}
                className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 transition-colors cursor-pointer"
              >
                Auto-fill Demo
              </button>
            </div>

            {/* Secure Login Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-lg shadow-blue-600/30 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-blue-500 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Authenticating via Neon PostgreSQL...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4 text-blue-200 group-hover:scale-110 transition-transform" />
                  <span>Secure Command Center Login</span>
                  <ArrowRight className="w-3.5 h-3.5 text-blue-200 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Card Footer: Real-time Clock & Legal Notice */}
        <div className="px-6 py-3.5 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>SESSION GATEWAY</span>
          </div>
          {currentTime && (
            <div className="flex items-center gap-1 text-slate-400 font-medium">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>{currentTime}</span>
            </div>
          )}
        </div>
      </div>

      {/* University Regulatory Footer */}
      <div className="mt-6 text-center max-w-sm text-[11px] text-slate-500 leading-relaxed relative z-10">
        Authorized University Personnel Only. All authentication attempts are logged and monitored under UGC & AICTE Higher Education Regulations.
      </div>
    </div>
  );
}
