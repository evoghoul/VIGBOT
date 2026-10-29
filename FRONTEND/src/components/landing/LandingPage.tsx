"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import {
  Bot,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  UserCheck,
  GraduationCap,
  CreditCard,
  Calendar,
  LifeBuoy,
  MessageSquareText,
  Zap,
  Lock,
  HeartHandshake,
  ChevronRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageSelector } from "@/components/common/LanguageSelector";
import { InteractiveLivePreview } from "./InteractiveLivePreview";

interface LandingPageProps {
  onGetStarted: () => void;
}

function useTypewriter(text: string, speed = 32, startDelay = 400) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    let i = 0;
    const timeout = setTimeout(() => {
      setDisplayed("");
      setDone(false);
      const interval = setInterval(() => {
        if (i < text.length) {
          setDisplayed(text.slice(0, i + 1));
          i++;
        } else {
          setDone(true);
          clearInterval(interval);
        }
      }, speed);
    }, startDelay);

    return () => {
      clearTimeout(timeout);
    };
  }, [text, speed, startDelay]);

  return { displayed, done };
}

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  const { t } = useLanguage();

  const typewriterText =
    t.landingTypewriter ||
    "Ask about your attendance, exams, fees, or policies — get a real answer from your real record.";

  const { displayed, done } = useTypewriter(typewriterText, 28, 400);

  const [pillsVisible, setPillsVisible] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setPillsVisible(true), 400);
    return () => clearTimeout(timer);
  }, []);

  const navLinks = [
    { label: t.navFeatures || "Features", href: "#features" },
    { label: t.navHowItWorks || "How it works", href: "#how-it-works" },
    { label: t.navTrustSecurity || "Trust & Security", href: "#trust-&-security" },
  ];

  const featureCards = [
    {
      icon: MessageSquareText,
      tone: "primary" as const,
      title: t.feat1Title || "One AI agent, every answer",
      description:
        t.feat1Desc ||
        "Ask about attendance, exams, fees, or policies in plain language. VIGBOT pulls the real record and answers instantly — no forms, no tickets, no waiting on email.",
    },
    {
      icon: UserCheck,
      tone: "warning" as const,
      title: t.feat2Title || "Attendance that warns you early",
      description:
        t.feat2Desc ||
        "See per-subject attendance against the 75% rule, with a consecutive-classes calculator that tells you exactly what it takes to stay clear.",
    },
    {
      icon: GraduationCap,
      tone: "success" as const,
      title: t.feat3Title || "Marks, CGPA & degree progress",
      description:
        t.feat3Desc ||
        "Continuous assessment scores, semester CGPA, and a live credit-completion tracker against your full degree requirement — always in view.",
    },
    {
      icon: CreditCard,
      tone: "info" as const,
      title: t.feat4Title || "Fees, receipts & due dates",
      description:
        t.feat4Desc ||
        "A single ledger for tuition, hostel and exam fees, with downloadable receipts and clear reminders before anything falls due.",
    },
    {
      icon: Calendar,
      tone: "primary" as const,
      title: t.feat5Title || "Timetable & exam schedule",
      description:
        t.feat5Desc ||
        "Today's classes, room numbers, and faculty at a glance, plus hall tickets and seating details for every upcoming examination.",
    },
    {
      icon: LifeBuoy,
      tone: "info" as const,
      title: t.feat6Title || "Services, without the paperwork",
      description:
        t.feat6Desc ||
        "Request certificates, book a mentor meeting, or raise a grievance conversationally — every request becomes a tracked ticket automatically.",
    },
  ];

  const steps = [
    {
      step: "01",
      title: t.step1Title || "Sign in with your roll number",
      description:
        t.step1Desc ||
        "Single sign-on authenticates you against the university's own student records — no separate account to create.",
    },
    {
      step: "02",
      title: t.step2Title || "Ask VIGBOT anything",
      description:
        t.step2Desc ||
        "Type a question the way you'd ask a senior — the assistant classifies it, checks your access, and answers from the real data.",
    },
    {
      step: "03",
      title: t.step3Title || "Act on what it finds",
      description:
        t.step3Desc ||
        "Jump straight into the relevant screen, download a hall ticket, pay a fee, or escalate to a human — all from the same place.",
    },
  ];

  const trustPoints = [
    {
      icon: ShieldCheck,
      title: t.trust1Title || "Row-Level Security",
      description:
        t.trust1Desc ||
        "Every query is scoped to your own student ID before it ever reaches a data source — cross-student access is rejected at the guardrail, not the UI.",
    },
    {
      icon: Lock,
      title: t.trust2Title || "Federated, not siloed",
      description:
        t.trust2Desc ||
        "18 specialized domain topics (attendance, exams, fees, hostel, transport, and more) sit behind VIGBOT, each authorized independently.",
    },
    {
      icon: HeartHandshake,
      title: t.trust3Title || "Distress-aware by design",
      description:
        t.trust3Desc ||
        "Conversations are monitored for signs of serious stress, with an immediate handoff to campus counseling — never left to a chatbot alone.",
    },
  ];

  return (
    <div className="min-h-dvh bg-card text-foreground selection:bg-blue-100 selection:text-blue-900">
      {/* Top Navbar */}
      <nav className="sticky top-0 z-40 border-b border-slate-200/80 bg-card/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 py-3.5">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <Image
              src="/vignan-logo.png"
              alt="Vignan Foundation"
              width={140}
              height={44}
              className="h-9 sm:h-11 w-auto object-contain"
            />
            <div className="h-7 w-px bg-slate-200 hidden sm:block" />
            <div className="hidden sm:block">
              <span className="text-sm sm:text-base font-bold tracking-tight text-foreground leading-tight block">
                {t.appName || "VIGBOT"}
              </span>
              <p className="text-sm text-muted-foreground leading-none mt-1">
                {t.autonomousSystem || "Autonomous University System"}
              </p>
            </div>
          </div>

          {/* Nav links (desktop) */}
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="hover:text-blue-600 transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Right: Language Selector + Sign In Button */}
          <div className="flex items-center gap-2.5">
            <LanguageSelector />
            <button
              onClick={onGetStarted}
              className="flex items-center gap-1.5 rounded-full bg-blue-600 px-4 py-2 text-xs sm:text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors cursor-pointer"
            >
              <span>{t.signIn || "Sign in"}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section
        ref={heroRef}
        className="relative overflow-hidden bg-gradient-to-b from-slate-50 via-white to-white py-16 sm:py-24 lg:py-28"
      >
        <div className="absolute inset-0 pointer-events-none opacity-40">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: "radial-gradient(#93c5fd 1px, transparent 1px)",
              backgroundSize: "32px 32px",
            }}
          />
        </div>

        <div className="relative mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.05fr_0.95fr]">
          {/* Left Column: Copy & CTAs */}
          <div className="max-w-2xl">
            <div className="mb-6 flex flex-wrap items-center gap-2">
              <Badge variant="primary">
                <Sparkles className="h-3 w-3" />
                {t.vigbotCoreActive || "VIGBOT Core"}
              </Badge>
              <Badge variant="success">
                <ShieldCheck className="h-3 w-3" />
                {t.loginRowLevelAuth || "Row-Level Security"}
              </Badge>
            </div>

            <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              {t.landingTagline || "The AI helpdesk that actually knows"}{" "}
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                {t.landingRecord || "your record"}
              </span>
              .
            </h1>

            <p
              className="mt-6 text-lg leading-relaxed text-muted-foreground sm:text-xl"
              style={{ minHeight: "3.5rem" }}
            >
              {displayed}
              {!done && (
                <span className="ml-0.5 inline-block h-[1.1em] w-[2px] translate-y-0.5 animate-[blink_1s_step-end_infinite] bg-blue-600 align-middle" />
              )}
            </p>

            <div
              className={`mt-8 flex flex-wrap items-center gap-3 transition-all duration-500 ${
                pillsVisible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
              }`}
            >
              <button
                onClick={onGetStarted}
                className="flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-colors cursor-pointer"
              >
                <span>{t.landingSignInDashboard || "Sign in to your dashboard"}</span>
                <ArrowRight className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => {
                  const previewEl = document.getElementById("hero-live-preview-card");
                  if (previewEl) {
                    previewEl.scrollIntoView({ behavior: "smooth", block: "center" });
                    previewEl.classList.add("ring-4", "ring-blue-500/50");
                    setTimeout(() => {
                      previewEl.classList.remove("ring-4", "ring-blue-500/50");
                    }, 1500);
                  }
                }}
                className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-card px-6 py-3 text-sm font-semibold text-foreground hover:bg-muted/50 transition-colors cursor-pointer"
              >
                <span>{t.landingSeeWhatItCanDo || "See what it can do"}</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Zap className="h-4 w-4 text-blue-500" />
                {t.landingTwelveAgents || "12 Domain Modules & 18 ML Intents"}
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                {t.landingVerifiedAccess || "Verified per-student access"}
              </span>
              <span className="flex items-center gap-1.5">
                <HeartHandshake className="h-4 w-4 text-rose-500" />
                {t.landingDistressSupport || "Distress-aware support"}
              </span>
            </div>
          </div>

          {/* Right Column: Floating Interactive Live Preview Card */}
          <div className="relative mt-8 lg:mt-0">
            <InteractiveLivePreview onExploreMore={onGetStarted} />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="scroll-mt-20 border-t border-slate-100 bg-card py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <Badge variant="primary">{t.landingFeatBadge || "Everything in one place"}</Badge>
            <h2 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              {t.landingFeatHeading || "One assistant, your whole academic life"}
            </h2>
            <p className="mt-4 text-base text-muted-foreground sm:text-lg">
              {t.landingFeatSub ||
                "No more chasing five different portals. VIGBOT connects to every record that matters and answers from the source of truth."}
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featureCards.map((f) => {
              const Icon = f.icon;
              const toneClasses: Record<string, string> = {
                primary: "bg-blue-50 text-blue-600",
                warning: "bg-amber-50 text-amber-600",
                success: "bg-emerald-50 text-emerald-600",
                info: "bg-indigo-50 text-indigo-600",
              };
              return (
                <div
                  key={f.title}
                  className="rounded-xl border border-slate-200/90 bg-card p-7 shadow-xs hover:border-blue-300 hover:shadow-md transition-all group"
                >
                  <div
                    className={`inline-flex h-12 w-12 items-center justify-center rounded-lg ${toneClasses[f.tone] || "bg-blue-50 text-blue-600"}`}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-4 text-base font-bold text-foreground group-hover:text-blue-600 transition-colors">
                    {f.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {f.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section id="how-it-works" className="scroll-mt-20 border-t border-slate-100 bg-muted/50/60 py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <Badge variant="info">{t.navHowItWorks || "How it works"}</Badge>
            <h2 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              {t.howItWorksHeading || "From sign-in to answer in seconds"}
            </h2>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-8 md:grid-cols-3">
            {steps.map((s, i) => (
              <div key={s.step} className="relative">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-sm font-bold text-white">
                    {s.step}
                  </span>
                  {i < steps.length - 1 && (
                    <div className="hidden h-px flex-1 bg-gradient-to-r from-blue-200 to-transparent md:block" />
                  )}
                </div>
                <h3 className="mt-4 text-lg font-bold text-foreground">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust & Security Section */}
      <div id="trust-security" className="scroll-mt-20" />
      <section id="trust-&-security" className="relative scroll-mt-20 border-t border-slate-100 bg-card py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <Badge variant="success">{t.navTrustSecurity || "Trust & security"}</Badge>
              <h2 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                {t.trustHeading || "Built on the same guardrails a bank would use"}
              </h2>
              <p className="mt-4 text-base leading-relaxed text-muted-foreground sm:text-lg">
                {t.trustSub ||
                  "VIGBOT never touches another student's data, even by accident. Every request is authenticated, scoped, and logged before it reaches an institutional agent."}
              </p>
              <button
                onClick={onGetStarted}
                className="mt-8 flex items-center gap-2 rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <span>{t.tryWithLogin || "Try it with your own login"}</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-4">
              {trustPoints.map((tp) => {
                const Icon = tp.icon;
                return (
                  <div
                    key={tp.title}
                    className="flex gap-4 rounded-lg border border-slate-200 bg-muted/50/60 p-5"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-card text-blue-600 shadow-xs">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-foreground">{tp.title}</h3>
                      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                        {tp.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="bg-gradient-to-br from-blue-600 via-indigo-600 to-blue-700 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {t.ctaHeading || "Your record is already connected. Go ask it something."}
          </h2>
          <p className="mt-4 text-base text-blue-100 sm:text-lg">
            {t.ctaSub || "Sign in with your university roll number to talk to VIGBOT."}
          </p>
          <button
            onClick={onGetStarted}
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-card px-7 py-3.5 text-sm font-semibold text-blue-700 shadow-lg hover:bg-blue-50 transition-colors cursor-pointer"
          >
            <span>{t.ctaButton || "Sign in to VIGBOT"}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </section>

      {/* Institutional Footer */}
      <footer className="border-t border-slate-200 bg-card py-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs">
              <Bot className="h-4 w-4" />
            </div>
            <span className="text-sm font-bold text-foreground">
              {t.appName || "VIGBOT"}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            {t.footerLayer || "Autonomous Student Support Layer · Group 13"}
          </p>
        </div>
      </footer>
    </div>
  );
};
