import { useEffect, useMemo, useState } from "react";
import { Users, TrendingUp, Activity, Scale, Clock3 } from "lucide-react";
import { KPICard } from "./components/KPICard";
import { StudentCard } from "./components/StudentCard";
import { CircularProgress } from "./components/CircularProgress";
import { StatusIndicator } from "./components/StatusIndicator";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Student {
  id: number;
  participation: number;
  role: "Active" | "Moderate" | "Passive";
  detailedRole?: string;
}

interface LiveData {
  timestamp: number;
  total_students: number;
  students: Array<{
    student_id: number;
    role: "Active" | "Moderate" | "Passive";
    detailed_role?: string;
    participation_score: number;
  }>;
  metrics: {
    most_active_student: number | null;
    participation_level: number;
    discussion_balance: number;
  };
}

interface TrendPoint {
  time: string;
  participation: number;
  balance: number;
}

const ENV_API_URL = import.meta.env.VITE_API_URL as string | undefined;
const API_CANDIDATES = [
  ...(ENV_API_URL ? [ENV_API_URL] : []),
  "http://localhost:8000",
  "http://127.0.0.1:8000",
  "http://localhost:8001",
  "http://127.0.0.1:8001",
  "http://localhost:8002",
  "http://127.0.0.1:8002",
  "http://localhost:8080",
  "http://127.0.0.1:8080",
  "http://localhost:8100",
  "http://127.0.0.1:8100",
];

export default function App() {
  const [students, setStudents] = useState<Student[]>([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [participationLevel, setParticipationLevel] = useState(0);
  const [discussionBalance, setDiscussionBalance] = useState(0);
  const [mostActiveStudentId, setMostActiveStudentId] = useState<number | null>(null);
  const [lastUpdatedLabel, setLastUpdatedLabel] = useState("--:--:--");
  const [currentTime, setCurrentTime] = useState(new Date());
  const [connected, setConnected] = useState(false);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [apiBase, setApiBase] = useState<string | null>(ENV_API_URL ?? null);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineLoading, setPipelineLoading] = useState(false);

  const detectApiBase = async (): Promise<string | null> => {
    for (const candidate of API_CANDIDATES) {
      try {
        const response = await fetch(`${candidate}/health`);
        if (response.ok) {
          return candidate;
        }
      } catch {
        // Try next candidate.
      }
    }
    return null;
  };

  const fetchLiveData = async () => {
    try {
      let base = apiBase;
      if (!base) {
        base = await detectApiBase();
        setApiBase(base);
      }

      if (!base) {
        throw new Error("No reachable API endpoint");
      }

      const response = await fetch(`${base}/data`);
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: LiveData = await response.json();

      const mappedStudents = data.students.map((student) => ({
        id: student.student_id,
        participation: Math.round(student.participation_score * 100),
        role: student.role,
        detailedRole: student.detailed_role,
      }));

      const pLevel = Math.round(data.metrics.participation_level * 100);
      const dBalance = Math.round(data.metrics.discussion_balance * 100);

      setStudents(mappedStudents);
      setTotalStudents(data.total_students);
      setParticipationLevel(pLevel);
      setDiscussionBalance(dBalance);
      setMostActiveStudentId(data.metrics.most_active_student);
      setConnected(true);

      const ts = data.timestamp ? new Date(data.timestamp * 1000) : new Date();
      setLastUpdatedLabel(
        ts.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      );

      setTrend((prev) => {
        const next = [
          ...prev,
          {
            time: ts.toLocaleTimeString("en-US", { minute: "2-digit", second: "2-digit" }),
            participation: pLevel,
            balance: dBalance,
          },
        ];
        return next.slice(-18);
      });
    } catch {
      setApiBase(null);
      setConnected(false);
    }
  };

  const checkPipelineStatus = async () => {
    try {
      let base = apiBase;
      if (!base) {
        base = await detectApiBase();
        setApiBase(base);
      }
      if (!base) return;
      
      const response = await fetch(`${base}/pipeline/status`);
      if (response.ok) {
        const data = await response.json();
        setPipelineRunning(data.running);
      }
    } catch {
      // Silently fail
    }
  };

  const handlePipelineStart = async () => {
    setPipelineLoading(true);
    try {
      let base = apiBase;
      if (!base) {
        base = await detectApiBase();
        setApiBase(base);
      }
      if (!base) throw new Error("No API endpoint");
      
      const response = await fetch(`${base}/pipeline/start`, { method: "POST" });
      if (response.ok) {
        setPipelineRunning(true);
      }
    } catch (error) {
      console.error("Error starting pipeline:", error);
    } finally {
      setPipelineLoading(false);
    }
  };

  const handlePipelineStop = async () => {
    setPipelineLoading(true);
    try {
      let base = apiBase;
      if (!base) {
        base = await detectApiBase();
        setApiBase(base);
      }
      if (!base) throw new Error("No API endpoint");
      
      const response = await fetch(`${base}/pipeline/stop`, { method: "POST" });
      if (response.ok) {
        setPipelineRunning(false);
      }
    } catch (error) {
      console.error("Error stopping pipeline:", error);
    } finally {
      setPipelineLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveData();
    checkPipelineStatus();
    const dataTimer = window.setInterval(fetchLiveData, 1000);
    const statusTimer = window.setInterval(checkPipelineStatus, 2000);
    const clockTimer = window.setInterval(() => setCurrentTime(new Date()), 1000);

    return () => {
      window.clearInterval(dataTimer);
      window.clearInterval(statusTimer);
      window.clearInterval(clockTimer);
    };
  }, []);

  const mostActiveStudent = useMemo(() => {
    if (mostActiveStudentId == null) {
      return "N/A";
    }
    return `Student ${mostActiveStudentId}`;
  }, [mostActiveStudentId]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <div className="min-h-screen w-full bg-[radial-gradient(circle_at_15%_20%,#d8f3ff_0%,transparent_35%),radial-gradient(circle_at_85%_10%,#ffe3f4_0%,transparent_34%),linear-gradient(180deg,#f7fbff_0%,#eef3ff_100%)]">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 rounded-3xl border border-white/70 bg-white/75 p-6 shadow-[0_12px_32px_rgba(86,108,255,0.12)] backdrop-blur">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-2">
            <h1 className="text-4xl bg-gradient-to-r from-[#5867ff] via-[#00bcd4] to-[#ff5ab4] bg-clip-text text-transparent">
              Classroom Discussion Analytics
            </h1>
            <div className="flex flex-col sm:flex-row items-center gap-4 text-slate-600">
              <div className="flex items-center gap-3">
                <button
                  onClick={handlePipelineStart}
                  disabled={pipelineRunning || pipelineLoading}
                  className="px-4 py-2 rounded-lg bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white font-medium transition-colors disabled:cursor-not-allowed"
                >
                  {pipelineLoading ? "Loading..." : "Start"}
                </button>
                <button
                  onClick={handlePipelineStop}
                  disabled={!pipelineRunning || pipelineLoading}
                  className="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white font-medium transition-colors disabled:cursor-not-allowed"
                >
                  {pipelineLoading ? "Loading..." : "End"}
                </button>
              </div>
              <StatusIndicator connected={connected} />
              <div className="flex items-center gap-2 rounded-xl bg-white px-3 py-1.5">
                <Clock3 className="h-4 w-4 text-[#5867ff]" />
                <span className="text-sm">{formatTime(currentTime)}</span>
              </div>
            </div>
          </div>
          <p className="text-slate-600">Real-time participation monitoring for group discussions</p>
          <p className="mt-2 text-sm text-slate-500">Last data update: {lastUpdatedLabel}</p>
        </div>

        {/* KPI Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="Total Students Detected"
            value={totalStudents}
            icon={Users}
            gradient="from-[#5867ff] to-[#8b95ff]"
          />

          <KPICard
            title="Most Active Student"
            value={mostActiveStudent}
            subtitle={connected ? "Live ranking from backend" : "Waiting for data"}
            icon={TrendingUp}
            gradient="from-[#00c9b7] to-[#00a4ff]"
            highlight={true}
          />

          <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="rounded-xl bg-gradient-to-br from-[#ffd76a] to-[#ffb347] p-3">
                <Activity className="w-6 h-6 text-white" />
              </div>
            </div>
            <h3 className="mb-4 text-sm text-gray-500">Participation Level</h3>
            <div className="flex justify-center">
              <CircularProgress value={participationLevel} />
            </div>
          </div>

          <KPICard
            title="Discussion Balance"
            value={discussionBalance}
            subtitle={discussionBalance >= 70 ? "Well balanced" : "Needs facilitation"}
            icon={Scale}
            gradient="from-[#ff7ecb] to-[#ff5ab4]"
          />
        </div>

        {/* Visual trend */}
        <div className="mb-8 rounded-3xl border border-white/70 bg-white/80 p-5 shadow-[0_10px_24px_rgba(97,123,255,0.1)] backdrop-blur">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl text-slate-800">Discussion Momentum</h2>
            <span className="rounded-full bg-[#eef2ff] px-3 py-1 text-xs text-[#5867ff]">Last 18 seconds</span>
          </div>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend}>
                <defs>
                  <linearGradient id="participationFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00bcd4" stopOpacity={0.45} />
                    <stop offset="95%" stopColor="#00bcd4" stopOpacity={0.04} />
                  </linearGradient>
                  <linearGradient id="balanceFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff5ab4" stopOpacity={0.36} />
                    <stop offset="95%" stopColor="#ff5ab4" stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e9ff" />
                <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Area type="monotone" dataKey="participation" stroke="#00bcd4" fill="url(#participationFill)" strokeWidth={2.5} />
                <Area type="monotone" dataKey="balance" stroke="#ff5ab4" fill="url(#balanceFill)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Student Participation Grid */}
        <div className="mb-6">
          <h2 className="text-2xl text-gray-800 mb-4">Student Participation</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {students.map((student, index) => (
            <StudentCard
              key={String(student.id)}
              studentId={`Student ${student.id}`}
              participation={student.participation}
              role={student.role}
              detailedRole={student.detailedRole}
              index={index}
            />
          ))}
        </div>

        {!students.length && (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white/70 p-8 text-center text-slate-600">
            Waiting for students. Start the backend camera pipeline to see live cards.
          </div>
        )}

        {/* Legend */}
        <div className="mt-8 flex flex-wrap items-center gap-6 justify-center">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#00d2d3]"></div>
            <span className="text-sm text-gray-600">Active (65%+)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#feca57]"></div>
            <span className="text-sm text-gray-600">Moderate (40-64%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#ff9ff3]"></div>
            <span className="text-sm text-gray-600">Passive (&lt;40%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}