"use client";

import { useState } from "react";

const API_URL = "http://localhost:5050";

type Lang = "en" | "ar";

const translations = {
  en: {
    loginTitle: "FRA Risk Intelligence — Login",
    emailPlaceholder: "Email",
    passwordPlaceholder: "Password",
    loginButton: "Login",
    logout: "Logout",
    brandMain: "FRA",
    brandSub: "Risk Intelligence",
    searchPlaceholder: "Search company...",
    loadingCompanies: "Loading companies...",
    noCompaniesFound: "No companies found",
    notScored: "Not scored",
    pickCompany: "Select a company from the list to view details",
    loadingDetails: "Loading company details...",
    license: "License",
    runRiskAnalysis: "Run Risk Analysis",
    analyzing: "Analyzing...",
    complaintRisk: "Complaint Risk",
    financialRisk: "Financial Risk",
    overallRisk: "Overall Risk",
    riskLevel: "Risk Level",
    riskAnalysisDetails: "Risk Analysis Details",
    complaintDrivers: "Complaint drivers:",
    complaintWarning: "Complaint warning:",
    mainFinancialFactor: "Main financial factor:",
    financialExplanation: "Financial explanation:",
    recentComplaints: "Recent Complaints",
    colDate: "Date",
    colCategory: "Category",
    colSentiment: "Sentiment",
    colSeverity: "Severity",
    colStatus: "Status",
    noComplaints: "No complaints on record",
    financialHistory: "Financial History",
    colPeriod: "Period",
    colRevenue: "Revenue",
    colNetProfit: "Net Profit",
    colTotalDebt: "Total Debt",
    colEquity: "Equity",
    noFinancialData: "No financial data on record",
    errLoginFailed: "Login failed",
    errServerUnreachable: "Could not reach the server",
    errFetchCompanies: "Could not fetch companies",
    errFetchDetails: "Could not fetch company details",
    errRiskAnalysis: "Risk analysis failed",
    langButton: "العربية",
    analysisComplete: "Analysis complete",
    updatedJustNow: "Scores updated just now",
    lastAnalyzed: "Last analyzed",
    neverAnalyzed: "Never analyzed",
    overallRiskChange: "Overall Risk",
    noChange: "No change",
    levels: {
      Critical: "Critical",
      High: "High",
      Medium: "Medium",
      Low: "Low",
    } as Record<string, string>,
  },
  ar: {
    loginTitle: "منصة تقييم المخاطر — تسجيل الدخول",
    emailPlaceholder: "البريد الإلكتروني",
    passwordPlaceholder: "كلمة المرور",
    loginButton: "تسجيل الدخول",
    logout: "تسجيل الخروج",
    brandMain: "FRA",
    brandSub: "منصة تقييم المخاطر",
    searchPlaceholder: "ابحث عن شركة...",
    loadingCompanies: "جاري تحميل الشركات...",
    noCompaniesFound: "لا توجد شركات",
    notScored: "لم يتم التقييم",
    pickCompany: "اختر شركة من القايمة لعرض التفاصيل",
    loadingDetails: "جاري تحميل تفاصيل الشركة...",
    license: "رخصة رقم",
    runRiskAnalysis: "تشغيل تحليل المخاطر",
    analyzing: "جاري التحليل...",
    complaintRisk: "مخاطر الشكاوى",
    financialRisk: "المخاطر المالية",
    overallRisk: "المخاطر الإجمالية",
    riskLevel: "مستوى الخطورة",
    riskAnalysisDetails: "تفاصيل تحليل المخاطر",
    complaintDrivers: "أسباب الشكاوى:",
    complaintWarning: "تحذير الشكاوى:",
    mainFinancialFactor: "العامل المالي الرئيسي:",
    financialExplanation: "الشرح المالي:",
    recentComplaints: "الشكاوى الأخيرة",
    colDate: "التاريخ",
    colCategory: "الفئة",
    colSentiment: "الانطباع",
    colSeverity: "الخطورة",
    colStatus: "الحالة",
    noComplaints: "لا توجد شكاوى مسجلة",
    financialHistory: "السجل المالي",
    colPeriod: "الفترة",
    colRevenue: "الإيرادات",
    colNetProfit: "صافي الربح",
    colTotalDebt: "إجمالي الديون",
    colEquity: "حقوق الملكية",
    noFinancialData: "لا توجد بيانات مالية مسجلة",
    errLoginFailed: "فشل تسجيل الدخول",
    errServerUnreachable: "تعذر الوصول إلى الخادم",
    errFetchCompanies: "تعذر جلب الشركات",
    errFetchDetails: "تعذر جلب تفاصيل الشركة",
    errRiskAnalysis: "فشل تحليل المخاطر",
    langButton: "English",
    analysisComplete: "اكتمل التحليل",
    updatedJustNow: "تم تحديث الأرقام الآن",
    lastAnalyzed: "آخر تحليل",
    neverAnalyzed: "لم يتم التحليل بعد",
    overallRiskChange: "المخاطر الإجمالية",
    noChange: "بدون تغيير",
    levels: {
      Critical: "حرج",
      High: "مرتفع",
      Medium: "متوسط",
      Low: "منخفض",
    } as Record<string, string>,
  },
};

// Translate a risk-level code (which stays in English internally for badge
// color logic) into the display language, falling back to the raw value.
const translateLevel = (t: (typeof translations)["en"], level: string | null | undefined) =>
  level ? t.levels[level] ?? level : level;

// Human-friendly "X minutes ago" style relative time, in either language.
const formatRelativeTime = (isoString: string | null | undefined, lang: Lang) => {
  if (!isoString) return null;
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return null;

  const diffSeconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  const units: [number, string, string][] = [
    [60, "second", "ثانية"],
    [60, "minute", "دقيقة"],
    [24, "hour", "ساعة"],
    [30, "day", "يوم"],
  ];

  let value = diffSeconds;
  let unitEn = "second";
  let unitAr = "ثانية";
  for (const [limit, en, ar] of units) {
    if (value < limit) {
      unitEn = en;
      unitAr = ar;
      break;
    }
    value = Math.floor(value / limit);
    unitEn = en;
    unitAr = ar;
  }

  if (lang === "ar") {
    return value <= 1 ? `منذ لحظات` : `منذ ${value} ${unitAr}`;
  }
  return value <= 1 && unitEn === "second" ? "just now" : `${value} ${unitEn}${value === 1 ? "" : "s"} ago`;
};

const riskBadgeClasses = (level: string | null | undefined) => {
  switch (level) {
    case "Critical":
      return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300";
    case "High":
      return "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300";
    case "Medium":
      return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300";
    case "Low":
      return "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300";
    default:
      return "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400";
  }
};

export default function Home() {
  const [lang, setLang] = useState<Lang>("en");
  const t = translations[lang];
  const dir = lang === "ar" ? "rtl" : "ltr";

  const toggleLang = () => setLang((prev) => (prev === "en" ? "ar" : "en"));

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState("");

  const [companies, setCompanies] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loadingList, setLoadingList] = useState(false);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<any | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const [riskResult, setRiskResult] = useState<any | null>(null);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [analysisBanner, setAnalysisBanner] = useState<{
    before: { complaint: number | null; financial: number | null; overall: number | null; level: string | null };
    after: { complaint: number; financial: number; overall: number; level: string };
  } | null>(null);
  const [justUpdated, setJustUpdated] = useState(false);

  // ---------- Login ----------
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();

      if (!data.success) {
        setError(data.error || t.errLoginFailed);
        return;
      }

      setToken(data.token);
      fetchCompanies(data.token);
    } catch (err) {
      setError(t.errServerUnreachable);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setCompanies([]);
    setSelectedId(null);
    setDetail(null);
    setRiskResult(null);
    setAnalysisBanner(null);
  };

  // ---------- Companies list ----------
  const fetchCompanies = async (activeToken?: string) => {
    const tk = activeToken || token;
    if (!tk) return;

    setLoadingList(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/companies`, {
        headers: { Authorization: `Bearer ${tk}` },
      });
      const data = await res.json();
      setCompanies(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(t.errFetchCompanies);
    } finally {
      setLoadingList(false);
    }
  };

  // ---------- Company detail ----------
  const selectCompany = async (id: number, keepRiskResult = false) => {
    if (!token) return;
    setSelectedId(id);
    setDetail(null);
    if (!keepRiskResult) {
      setRiskResult(null);
      setAnalysisBanner(null);
    }
    setLoadingDetail(true);

    try {
      const res = await fetch(`${API_URL}/api/companies/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setDetail(data);
      return data;
    } catch (err) {
      setError(t.errFetchDetails);
    } finally {
      setLoadingDetail(false);
    }
  };

  // ---------- Run risk analysis ----------
  const runRiskAnalysis = async () => {
    if (!selectedId) return;
    setLoadingRisk(true);
    setError("");

    // snapshot the scores as they were BEFORE this run, so we can show a
    // clear before -> after comparison once the new numbers come back
    const before = {
      complaint: detail?.company?.complaint_risk ?? null,
      financial: detail?.company?.financial_risk ?? null,
      overall: detail?.company?.overall_risk ?? null,
      level: detail?.company?.risk_level ?? null,
    };

    try {
      const res = await fetch(`${API_URL}/api/companies/${selectedId}/analyze?lang=${lang}`, {
        method: "POST",
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || t.errRiskAnalysis);
        return;
      }

      // refresh the detail panel + sidebar list so the new scores show everywhere,
      // but keep the analysis result on screen instead of wiping it
      await Promise.all([selectCompany(selectedId, true), fetchCompanies()]);

      setRiskResult(data);
      setAnalysisBanner({
        before,
        after: {
          complaint: data.complaint_risk_score,
          financial: data.financial_risk_score,
          overall: data.overall_risk_score,
          level: data.overall_risk_level,
        },
      });

      // briefly glow the score cards so the update is unmistakable
      setJustUpdated(true);
      setTimeout(() => setJustUpdated(false), 2500);
    } catch (err) {
      setError(t.errRiskAnalysis);
    } finally {
      setLoadingRisk(false);
    }
  };

  const filteredCompanies = companies.filter((c) =>
    c.name?.toLowerCase().includes(search.toLowerCase())
  );

  // Small reusable language toggle button
  const LangButton = ({ className = "" }: { className?: string }) => (
    <button
      type="button"
      onClick={toggleLang}
      className={`rounded border border-black/20 px-3 py-1.5 text-sm font-medium text-black hover:bg-zinc-100 dark:border-white/20 dark:text-white dark:hover:bg-zinc-800 ${className}`}
    >
      {t.langButton}
    </button>
  );

  // ========================== LOGIN SCREEN ==========================
  if (!token) {
    return (
      <div
        dir={dir}
        className="relative flex min-h-screen flex-col items-center justify-center gap-6 bg-zinc-50 p-8 font-sans dark:bg-black"
      >
        <div className="absolute top-6 end-6">
          <LangButton />
        </div>

        <h1 className="text-2xl font-semibold text-black dark:text-white">
          {t.loginTitle}
        </h1>
        <form
          onSubmit={handleLogin}
          className="flex w-full max-w-sm flex-col gap-4 rounded-lg border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-zinc-900"
        >
          <input
            type="email"
            placeholder={t.emailPlaceholder}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded border border-black/20 px-3 py-2 text-black dark:border-white/20 dark:text-white dark:bg-black"
            required
          />
          <input
            type="password"
            placeholder={t.passwordPlaceholder}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded border border-black/20 px-3 py-2 text-black dark:border-white/20 dark:text-white dark:bg-black"
            required
          />
          <button
            type="submit"
            className="rounded bg-black px-4 py-2 text-white hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
          >
            {t.loginButton}
          </button>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </form>
      </div>
    );
  }

  // ========================== MAIN DASHBOARD ==========================
  return (
    <div dir={dir} className="flex min-h-screen flex-col bg-zinc-50 font-sans dark:bg-black">
      {/* Navbar */}
      <header className="flex items-center justify-between border-b border-black/10 bg-white px-6 py-4 dark:border-white/10 dark:bg-zinc-900">
        <h1 className="text-lg font-semibold text-black dark:text-white">
          {t.brandMain} <span className="text-zinc-400 dark:text-zinc-500">{t.brandSub}</span>
        </h1>
        <div className="flex items-center gap-3">
          <LangButton />
          <button
            onClick={handleLogout}
            className="rounded border border-black/20 px-3 py-1.5 text-sm text-black hover:bg-zinc-100 dark:border-white/20 dark:text-white dark:hover:bg-zinc-800"
          >
            {t.logout}
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="flex w-72 flex-col border-r border-black/10 bg-white dark:border-white/10 dark:bg-zinc-900">
          <div className="p-4">
            <input
              type="text"
              placeholder={t.searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded border border-black/20 px-3 py-2 text-sm text-black dark:border-white/20 dark:bg-black dark:text-white"
            />
          </div>

          <div className="flex-1 overflow-y-auto px-2 pb-4">
            {loadingList && (
              <p className="px-2 py-3 text-sm text-zinc-400">{t.loadingCompanies}</p>
            )}
            {!loadingList && filteredCompanies.length === 0 && (
              <p className="px-2 py-3 text-sm text-zinc-400">{t.noCompaniesFound}</p>
            )}
            {filteredCompanies.map((c) => (
              <button
                key={c.id}
                onClick={() => selectCompany(c.id)}
                className={`mb-1 flex w-full flex-col items-start rounded px-3 py-2 text-left transition ${
                  selectedId === c.id
                    ? "bg-black text-white dark:bg-white dark:text-black"
                    : "hover:bg-zinc-100 dark:hover:bg-zinc-800"
                }`}
              >
                <span className="text-sm font-medium">{c.name}</span>
                <span className="flex items-center gap-2 text-xs opacity-70">
                  {c.sector}
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                      selectedId === c.id ? "bg-white/20" : riskBadgeClasses(c.risk_level)
                    }`}
                  >
                    {c.risk_level ? translateLevel(t, c.risk_level) : t.notScored}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </aside>

        {/* Dashboard */}
        <main className="flex-1 overflow-y-auto p-6">
          {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

          {!selectedId && (
            <div className="flex h-full items-center justify-center text-zinc-400">
              {t.pickCompany}
            </div>
          )}

          {selectedId && loadingDetail && (
            <p className="text-zinc-400">{t.loadingDetails}</p>
          )}

          {selectedId && detail && !loadingDetail && (
            <div className="flex flex-col gap-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-black dark:text-white">
                    {detail.company.name}
                  </h2>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    {detail.company.sector} · {t.license} {detail.company.license_number} · {detail.company.status}
                  </p>
                  <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">
                    {t.lastAnalyzed}:{" "}
                    {detail.company.last_scored_at
                      ? formatRelativeTime(detail.company.last_scored_at, lang)
                      : t.neverAnalyzed}
                  </p>
                </div>
                <button
                  onClick={runRiskAnalysis}
                  disabled={loadingRisk}
                  className="rounded bg-black px-4 py-2 text-sm text-white hover:bg-zinc-800 disabled:opacity-50 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
                >
                  {loadingRisk ? t.analyzing : t.runRiskAnalysis}
                </button>
              </div>

              {/* Before → after comparison banner, shown right after a run completes */}
              {analysisBanner && (
                <div className="flex flex-wrap items-center gap-3 rounded-lg border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800 dark:border-green-800 dark:bg-green-900/30 dark:text-green-300">
                  <span className="font-semibold">✅ {t.analysisComplete}</span>
                  <span className="text-green-700/80 dark:text-green-400/80">{t.updatedJustNow}</span>
                  <span className="ms-auto flex items-center gap-2 font-medium">
                    <span className="text-zinc-500 dark:text-zinc-400">{t.overallRiskChange}:</span>
                    <span className="opacity-70">{analysisBanner.before.overall ?? "—"}</span>
                    <span>→</span>
                    <span className="text-base">{analysisBanner.after.overall}</span>
                    {analysisBanner.before.overall !== null &&
                      analysisBanner.before.overall !== analysisBanner.after.overall && (
                        <span
                          className={
                            analysisBanner.after.overall > analysisBanner.before.overall
                              ? "text-red-600 dark:text-red-400"
                              : "text-green-600 dark:text-green-400"
                          }
                        >
                          ({analysisBanner.after.overall > analysisBanner.before.overall ? "+" : ""}
                          {(analysisBanner.after.overall - analysisBanner.before.overall).toFixed(2)})
                        </span>
                      )}
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${riskBadgeClasses(analysisBanner.after.level)}`}>
                      {translateLevel(t, analysisBanner.after.level)}
                    </span>
                  </span>
                </div>
              )}

              {/* Risk score cards */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: t.complaintRisk, value: detail.company.complaint_risk },
                  { label: t.financialRisk, value: detail.company.financial_risk },
                  { label: t.overallRisk, value: detail.company.overall_risk },
                ].map((item) => (
                  <div
                    key={item.label}
                    className={`rounded-lg border p-4 transition-all duration-500 ${
                      justUpdated
                        ? "border-green-400 bg-green-50 shadow-[0_0_0_3px_rgba(34,197,94,0.25)] dark:border-green-600 dark:bg-green-900/20"
                        : "border-black/10 bg-white dark:border-white/10 dark:bg-zinc-900"
                    }`}
                  >
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">{item.label}</p>
                    <p className="mt-1 text-2xl font-semibold text-black dark:text-white">
                      {item.value ?? "—"}
                    </p>
                  </div>
                ))}
                <div
                  className={`col-span-3 flex items-center justify-between rounded-lg border p-4 transition-all duration-500 ${
                    justUpdated
                      ? "border-green-400 bg-green-50 shadow-[0_0_0_3px_rgba(34,197,94,0.25)] dark:border-green-600 dark:bg-green-900/20"
                      : "border-black/10 bg-white dark:border-white/10 dark:bg-zinc-900"
                  }`}
                >
                  <span className="text-sm text-zinc-500 dark:text-zinc-400">{t.riskLevel}</span>
                  <span className={`rounded px-2 py-1 text-xs font-medium ${riskBadgeClasses(detail.company.risk_level)}`}>
                    {detail.company.risk_level ? translateLevel(t, detail.company.risk_level) : t.notScored}
                  </span>
                </div>
              </div>

              {/* Detailed risk breakdown (only after "Run Risk Analysis") */}
              {riskResult && (
                <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-zinc-900">
                  <h3 className="mb-3 text-sm font-semibold text-black dark:text-white">
                    {t.riskAnalysisDetails}
                  </h3>
                  <div className="flex flex-col gap-2 text-sm">
                    <p className="text-zinc-700 dark:text-zinc-300">
                      <span className="font-medium">{t.complaintDrivers}</span>{" "}
                      {riskResult.risk_drivers?.join(", ") || "—"}
                    </p>
                    <p className="text-zinc-700 dark:text-zinc-300">
                      <span className="font-medium">{t.complaintWarning}</span>{" "}
                      {riskResult.complaint_early_warning}
                    </p>
                    <p className="text-zinc-700 dark:text-zinc-300">
                      <span className="font-medium">{t.mainFinancialFactor}</span>{" "}
                      {riskResult.main_financial_risk_factor || "—"}
                    </p>
                    <p className="text-zinc-700 dark:text-zinc-300">
                      <span className="font-medium">{t.financialExplanation}</span>{" "}
                      {riskResult.financial_risk_explanation}
                    </p>
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">
                      {riskResult.early_warning}
                    </p>
                  </div>
                </div>
              )}

              {/* Complaints table */}
              <div>
                <h3 className="mb-2 text-sm font-semibold text-black dark:text-white">
                  {t.recentComplaints}
                </h3>
                <div className="overflow-x-auto rounded-lg border border-black/10 dark:border-white/10">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-zinc-100 dark:bg-zinc-800">
                      <tr>
                        <th className="px-3 py-2 font-medium">{t.colDate}</th>
                        <th className="px-3 py-2 font-medium">{t.colCategory}</th>
                        <th className="px-3 py-2 font-medium">{t.colSentiment}</th>
                        <th className="px-3 py-2 font-medium">{t.colSeverity}</th>
                        <th className="px-3 py-2 font-medium">{t.colStatus}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.complaints?.length ? (
                        detail.complaints.map((c: any) => (
                          <tr key={c.id} className="border-t border-black/10 dark:border-white/10">
                            <td className="px-3 py-2">{c.complaint_date?.slice(0, 10)}</td>
                            <td className="px-3 py-2">{c.category}</td>
                            <td className="px-3 py-2">{c.sentiment}</td>
                            <td className="px-3 py-2">{c.severity}</td>
                            <td className="px-3 py-2">{c.status}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="px-3 py-4 text-center text-zinc-400">
                            {t.noComplaints}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Financial data table */}
              <div>
                <h3 className="mb-2 text-sm font-semibold text-black dark:text-white">
                  {t.financialHistory}
                </h3>
                <div className="overflow-x-auto rounded-lg border border-black/10 dark:border-white/10">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-zinc-100 dark:bg-zinc-800">
                      <tr>
                        <th className="px-3 py-2 font-medium">{t.colPeriod}</th>
                        <th className="px-3 py-2 font-medium">{t.colRevenue}</th>
                        <th className="px-3 py-2 font-medium">{t.colNetProfit}</th>
                        <th className="px-3 py-2 font-medium">{t.colTotalDebt}</th>
                        <th className="px-3 py-2 font-medium">{t.colEquity}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.financial_data?.length ? (
                        detail.financial_data.map((f: any) => (
                          <tr key={f.id} className="border-t border-black/10 dark:border-white/10">
                            <td className="px-3 py-2">{f.period?.slice(0, 10)}</td>
                            <td className="px-3 py-2">{f.revenue?.toLocaleString()}</td>
                            <td className="px-3 py-2">{f.net_profit?.toLocaleString()}</td>
                            <td className="px-3 py-2">{f.total_debt?.toLocaleString()}</td>
                            <td className="px-3 py-2">{f.equity?.toLocaleString()}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="px-3 py-4 text-center text-zinc-400">
                            {t.noFinancialData}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}