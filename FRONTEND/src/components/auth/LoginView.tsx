"use client";

import Image from "next/image";

import React, { useState } from "react";
import {
  ShieldCheck,
  Bot,
  Sparkles,
  ArrowRight,
  Lock,
  User,
  CheckCircle2,
  Fingerprint,
} from "lucide-react";
import { CURRENT_STUDENT } from "@/data/student";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageSelector } from "@/components/common/LanguageSelector";
import { apiClient } from "@/lib/api-client";
import { useStudent } from "@/context/StudentContext";

interface LoginViewProps {
  onLogin: () => void;
  onBack?: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLogin, onBack }) => {
  const { t } = useLanguage();
  const { loginAsStudent } = useStudent();
  const [studentId, setStudentId] = useState(CURRENT_STUDENT.id);
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId.trim()) {
      setError(t.enterStudentId || "Please enter your Student Roll Number.");
      return;
    }
    if (!password.trim()) {
      setError("Please enter your password in format: firstname@regdnumber (e.g. aman@251FA04E13)");
      return;
    }
    setError(null);
    setIsLoading(true);
    const regd = studentId.trim().toUpperCase();
    const pwd = password.trim();
    try {
      await loginAsStudent(regd, pwd);
      setIsLoading(false);
      onLogin();
    } catch (err: any) {
      console.warn("Login error:", err);
      setError(err?.message || "Authentication failed. Please check your credentials.");
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    const demoPwd = "aman@" + CURRENT_STUDENT.id;
    setStudentId(CURRENT_STUDENT.id);
    setPassword(demoPwd);
    setError(null);
    setIsLoading(true);
    try {
      await loginAsStudent(CURRENT_STUDENT.id, demoPwd);
      setIsLoading(false);
      onLogin();
    } catch (err: any) {
      console.warn("Backend demo login error:", err);
      setError(err?.message || "Demo login failed.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-dvh w-full flex flex-col justify-between bg-muted/50 text-foreground relative overflow-hidden">
      {/* Ambient background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute inset-0 opacity-[0.4]"
          style={{
            backgroundImage: "radial-gradient(#c7d2fe 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-blue-200/30 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-indigo-200/30 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Top Bar */}
      <header className="relative z-10 w-full border-b border-slate-200 bg-card/80 backdrop-blur-md px-4 sm:px-6 py-3.5">
        <div className="mx-auto max-w-7xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Vignan University Official Logo */}
            <Image
              src="/vignan-logo.png"
              alt="Vignan Foundation"
              width={160}
              height={48}
              className="h-10 sm:h-12 w-auto object-contain"
            />
            <div className="h-8 w-px bg-slate-200 hidden sm:block" />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm tracking-tight text-foreground whitespace-nowrap">
                  {t.appName || "VIGBOT"}
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200">
                  <Sparkles className="h-2.5 w-2.5" />
                  AI
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {t.loginSubtitle || "Autonomous University System"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <LanguageSelector />
            <div className="hidden md:flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span className="font-medium">
                {t.loginRlsActive || "RLS Guardrails Active"}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Login Card Section */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-lg">
          {/* Card Container */}
          <div className="rounded-lg border border-slate-200 bg-card p-7 sm:p-8 shadow-sm space-y-6">
            {/* Header / Avatar */}
            <div className="text-center space-y-2">
              <div className="inline-flex h-14 w-14 items-center justify-center rounded-lg bg-blue-600 text-white mb-1 shadow-sm">
                <Bot className="h-7 w-7" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                {t.loginTitle || "Student Single Sign-On"}
              </h1>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                {t.loginBannerNote ||
                  "Sign in with your University Roll Number to connect with your personalized VIGBOT AI Assistant."}
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 text-center">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                  <span>{t.rollNoLabel || "Student Roll Number"}</span>
                  <span className="text-xs text-blue-600 font-normal">
                    {t.loginRollFormat || "Format: 251FA04E13"}
                  </span>
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    placeholder={t.enterStudentId || "Enter Student ID"}
                    className="w-full rounded-md border border-slate-200 bg-muted/50 py-2.5 pl-10 pr-4 text-sm text-foreground placeholder-slate-400 focus:border-blue-500 focus:bg-card focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-mono"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                  <span>{t.loginPasswordPin || "Institutional Password"}</span>
                  <span className="text-xs text-blue-600 font-normal">
                    Format: firstname@regdno
                  </span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="e.g. aman@251FA04E13"
                    className="w-full rounded-md border border-slate-200 bg-muted/50 py-2.5 pl-10 pr-4 text-sm text-foreground placeholder-slate-400 focus:border-blue-500 focus:bg-card focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-mono"
                    required
                  />
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Password format: <span className="font-semibold text-foreground">firstname@regdnumber</span> (e.g. <span className="font-mono text-blue-600 font-semibold">aman@251FA04E13</span>)
                </p>
              </div>

              <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-white"
                  />
                  <span>{t.loginKeepAuth || "Keep me authenticated"}</span>
                </label>
                <span className="flex items-center gap-1 text-muted-foreground text-xs">
                  <Fingerprint className="h-3.5 w-3.5 text-blue-500" />
                  {t.loginBiometricReady || "Biometric ready"}
                </span>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 rounded-md bg-blue-600 py-3 px-4 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:ring-offset-2 transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    {t.loginAuthenticating || "Authenticating Student..."}
                  </span>
                ) : (
                  <>
                    <span>{t.signIn || t.loginTitle || "Sign In"}</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>

            {/* Quick Demo Access Divider */}
            <div className="relative flex items-center justify-center pt-1">
              <div className="border-t border-slate-200 w-full" />
              <span className="bg-card px-3 text-xs uppercase tracking-wider text-slate-400 font-semibold absolute">
                {t.loginInstantDemo || "Instant Demo Access"}
              </span>
            </div>

            {/* Quick 1-Click Demo Login */}
            <button
              onClick={handleDemoLogin}
              type="button"
              className="w-full flex items-center justify-between rounded-md border border-slate-200 bg-card hover:bg-slate-50 p-3 text-left transition-all group cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-600 text-white font-bold text-xs shadow-sm">
                  {CURRENT_STUDENT.name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-foreground group-hover:text-blue-700 transition-colors">
                      {t.loginDemoLabel || "Demo"}: {CURRENT_STUDENT.name}
                    </span>
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  </div>
                  <p className="text-xs font-mono text-muted-foreground">
                    {CURRENT_STUDENT.id} • {CURRENT_STUDENT.programme}
                  </p>
                </div>
              </div>
              <span className="rounded-md bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 border border-blue-100 group-hover:bg-blue-600 group-hover:text-white transition-all">
                {t.signIn || "Sign In"}
              </span>
            </button>

            {/* Security Guarantee Badges */}
            <div className="pt-2 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                <span>{t.loginRowLevelAuth || "Row-Level Authorization"}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                <span>{t.loginTwelveFederated || "12 Domain Modules & 18 ML Intents"}</span>
              </div>
            </div>

            {/* Admin Portal Link */}
            <div className="pt-4 border-t border-slate-200 text-center">
              <a
                href="/admin/login"
                className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors"
              >
                <ShieldCheck className="h-4 w-4" />
                Nodal Officer / Admin Login
              </a>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full border-t border-slate-200 bg-card/80 backdrop-blur-md px-6 py-4 text-center text-xs text-muted-foreground">
        <p>
          {t.loginFooterPolicy ||
            "VIGBOT • Group 13 Autonomous Context Engine • Protected by University Privacy Policies"}
        </p>
      </footer>
    </div>
  );
};
