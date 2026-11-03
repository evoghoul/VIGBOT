"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  fetchAllTickets, 
  updateTicketStatus, 
  deleteTicket,
  fetchCognitiveRemediations,
  updateRemediationStatus,
  deleteRemediationRule,
  fetchGeminiStatus,
  updateGeminiConfig,
  pingGeminiConnection
} from '@/actions/admin';
import { getAnalyticsData } from '@/actions/analytics';
import { getAllBroadcasts, toggleBroadcastStatus, deleteBroadcast, createBroadcast } from '@/actions/broadcasts';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area
} from 'recharts';
import { 
  LogOut, 
  ShieldCheck, 
  Search, 
  Filter, 
  MessageSquareWarning, 
  Users, 
  CheckCircle2,
  Clock,
  XCircle,
  MoreVertical,
  Activity,
  Calendar,
  PackageSearch,
  BarChart3,
  Radio,
  Plus,
  Trash2,
  AlertTriangle,
  HeartPulse,
  KanbanSquare,
  Database,
  BookOpen,
  Power,
  Terminal,
  FileText,
  Send,
  Eye,
  Settings,
  ChevronRight,
  Bot,
  RefreshCw,
  Scale,
  Headset,
  FileCheck,
  Gavel,
  Download,
  Ear,
  MessageSquareOff,
  Map,
  TrendingDown,
  ScatterChart,
  ShieldAlert,
  Mic,
  UserX,
  AlertOctagon,
  MessageCircle,
  Video,
  UserPlus,
  Bell,
  Sparkles,
  KeyRound,
  Zap,
  Check,
  ExternalLink,
  Shield,
  ThumbsDown,
  ToggleLeft,
  ToggleRight,
  Sliders,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

interface Grievance {
  id: string;
  description: string;
  status: string;
  timestamp: string;
  withdrawal_reason: string | null;
}

interface ClubApp {
  id: number;
  club_id: string;
  student_name: string;
  status: string;
  timestamp: string;
  withdrawal_reason: string | null;
}

interface BookingItem {
  id: number;
  facility_id: number;
  student_id: string;
  date: string;
  start_time: string;
  end_time: string;
  purpose: string;
  status: string;
}

interface LostFoundItem {
  id: number;
  student_id: string;
  type: string;
  title: string;
  description: string;
  tags: string;
  contact_info: string;
  status: string;
  date_posted: string;
  image_url: string;
}

interface ServiceRequestItem {
  id: number;
  request_no: string;
  student_id: string;
  category: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
  sla_due_date?: string;
  assigned_office?: string;
}

interface HostelRequestItem {
  id: number;
  student_id: string;
  type: string;
  details: string;
  status: string;
  created_at: string;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [adminUser, setAdminUser] = useState<any>(null);
  
  const [serviceRequests, setServiceRequests] = useState<ServiceRequestItem[]>([]);
  const [hostelRequests, setHostelRequests] = useState<HostelRequestItem[]>([]);
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [clubApps, setClubApps] = useState<ClubApp[]>([]);
  const [bookings, setBookings] = useState<BookingItem[]>([]);
  const [lostAndFound, setLostAndFound] = useState<LostFoundItem[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [broadcasts, setBroadcasts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'service_requests' | 'hostel_requests' | 'grievances' | 'clubs' | 'bookings' | 'lost_found' | 'analytics' | 'broadcasts' | 'distress' | 'health' | 'kanban' | 'audit' | 'knowledge' | 'compliance' | 'live_sessions' | 'verifications' | 'remediation'>('service_requests');
  const [searchQuery, setSearchQuery] = useState('');
  
  const [newBroadcastMsg, setNewBroadcastMsg] = useState('');
  const [newBroadcastType, setNewBroadcastType] = useState('info');

  useEffect(() => {
    // Check authentication
    const session = localStorage.getItem('adminSession');
    if (!session) {
      router.push('/admin/login');
      return;
    }
    try {
      setAdminUser(JSON.parse(session));
      loadData();
    } catch (e) {
      router.push('/admin/login');
    }
  }, [router]);

  const loadData = async () => {
    setLoading(true);
    const res = await fetchAllTickets();
    if (res.success) {
      setGrievances((res.grievances as Grievance[]) || []);
      setClubApps((res.clubApps as ClubApp[]) || []);
      setBookings((res.bookings as BookingItem[]) || []);
      setLostAndFound((res.lostAndFound as LostFoundItem[]) || []);
      setServiceRequests((res.serviceRequests as ServiceRequestItem[]) || []);
      setHostelRequests((res.hostelRequests as HostelRequestItem[]) || []);
    }
    
    const analyticsRes = await getAnalyticsData();
    if (analyticsRes.success) {
      setAnalytics(analyticsRes.data);
    }
    
    const broadcastsRes = await getAllBroadcasts();
    if (broadcastsRes.success) {
      setBroadcasts(broadcastsRes.broadcasts || []);
    }
    
    setLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('adminSession');
    router.push('/admin/login');
  };

  const handleStatusUpdate = async (id: string | number, type: any, newStatus: string) => {
    const res = await updateTicketStatus(id.toString(), type, newStatus);
    if (res.success) {
      loadData();
    } else {
      alert(res.error || 'Failed to update status');
    }
  };

  const handleDeleteTicket = async (id: string | number, type: any) => {
    if (!window.confirm(`Permanently delete this ${type.replace('_', ' ')} record? This action cannot be undone.`)) {
      return;
    }
    const res = await deleteTicket(id.toString(), type);
    if (res.success) {
      loadData();
    } else {
      alert(res.error || 'Failed to delete record');
    }
  };

  const handleCreateBroadcast = async () => {
    if (!newBroadcastMsg.trim()) return;
    const res = await createBroadcast(newBroadcastMsg, newBroadcastType);
    if (res.success) {
      setNewBroadcastMsg('');
      loadData();
    }
  };

  const handleToggleBroadcast = async (id: number, currentStatus: number) => {
    await toggleBroadcastStatus(id, !currentStatus);
    loadData();
  };

  const handleDeleteBroadcast = async (id: number) => {
    await deleteBroadcast(id);
    loadData();
  };

  const getStatusBadgeColor = (status: string) => {
    const s = status.toLowerCase();
    if (s.includes('resolved') || s.includes('approved') || s.includes('confirmed') || s.includes('claimed')) return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    if (s.includes('withdrawn') || s.includes('rejected') || s.includes('cancelled')) return 'bg-rose-100 text-rose-700 border-rose-200';
    if (s.includes('investigation') || s.includes('forwarded') || s.includes('open') || s.includes('pending')) return 'bg-amber-100 text-amber-700 border-amber-200';
    return 'bg-blue-100 text-blue-700 border-blue-200';
  };

  const getStatusIcon = (status: string) => {
    const s = status.toLowerCase();
    if (s.includes('resolved') || s.includes('approved')) return <CheckCircle2 className="w-3.5 h-3.5 mr-1" />;
    if (s.includes('withdrawn') || s.includes('rejected')) return <XCircle className="w-3.5 h-3.5 mr-1" />;
    if (s.includes('investigation') || s.includes('forwarded')) return <Activity className="w-3.5 h-3.5 mr-1" />;
    return <Clock className="w-3.5 h-3.5 mr-1" />;
  };

  if (!adminUser) return null; // Prevent flash of unauthorized content

  const filteredServiceRequests = serviceRequests.filter(s =>
    (s.request_no && s.request_no.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (s.student_id && s.student_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (s.title && s.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (s.category && s.category.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (s.description && s.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const filteredHostelRequests = hostelRequests.filter(h =>
    (h.student_id && h.student_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (h.type && h.type.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (h.details && h.details.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const filteredGrievances = grievances.filter(g => 
    g.id.toLowerCase().includes(searchQuery.toLowerCase()) || 
    g.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredClubApps = clubApps.filter(c => 
    c.student_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    c.club_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredBookings = bookings.filter(b => 
    b.student_id.toLowerCase().includes(searchQuery.toLowerCase()) || 
    b.purpose.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredLostAndFound = lostAndFound.filter(l => 
    l.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    l.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    l.student_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-dvh bg-slate-50 flex flex-col font-sans text-slate-900">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-slate-900 rounded-lg flex items-center justify-center shadow-sm">
                <ShieldCheck className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg leading-tight text-slate-900">Nodal Officer Portal</h1>
                <p className="text-xs text-slate-500 font-medium tracking-wide uppercase">Command Center</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="hidden sm:flex items-center gap-2 text-sm text-slate-600 font-medium">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
                  {adminUser.name.charAt(0)}
                </div>
                <div>
                  <div className="text-slate-900">{adminUser.name}</div>
                  <div className="text-xs text-slate-500">{adminUser.role}</div>
                </div>
              </div>
              <button 
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                title="Sign out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 bg-rose-100 rounded-full flex items-center justify-center shrink-0">
              <MessageSquareWarning className="w-6 h-6 text-rose-600" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-900">{grievances.length}</div>
              <div className="text-sm font-medium text-slate-500">Grievances</div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center shrink-0">
              <Users className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-900">{clubApps.length}</div>
              <div className="text-sm font-medium text-slate-500">Club Apps</div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center shrink-0">
              <Calendar className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-900">{bookings.length}</div>
              <div className="text-sm font-medium text-slate-500">Bookings</div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center shrink-0">
              <PackageSearch className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-900">{lostAndFound.length}</div>
              <div className="text-sm font-medium text-slate-500">Lost/Found</div>
            </div>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="w-full lg:w-56 shrink-0 flex flex-col gap-1 h-fit">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-3">AI & Cognitive Governance</div>
            <button
              onClick={() => setActiveTab('remediation')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center justify-between w-full text-left ${
                activeTab === 'remediation' ? 'bg-purple-100 text-purple-900 font-semibold shadow-xs' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className="flex items-center gap-2.5">
                <Sparkles className="w-4 h-4 text-purple-600" /> AI Remediation & Gemini
              </span>
              <span className="text-[10px] bg-purple-200 text-purple-900 px-1.5 py-0.5 rounded-full font-bold">
                Live
              </span>
            </button>

            <div className="w-full h-px bg-slate-200 my-2"></div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-3">Modules</div>
            <button
              onClick={() => setActiveTab('compliance')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'compliance' ? 'bg-purple-50 text-purple-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Scale className="w-4 h-4" /> Compliance
            </button>
            <button
              onClick={() => setActiveTab('live_sessions')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'live_sessions' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Headset className="w-4 h-4" /> Live Sessions
            </button>
            <button
              onClick={() => setActiveTab('verifications')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'verifications' ? 'bg-orange-50 text-orange-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <FileCheck className="w-4 h-4" /> Verifications
            </button>
            <button
              onClick={() => setActiveTab('distress')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'distress' ? 'bg-rose-50 text-rose-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <AlertTriangle className="w-4 h-4" /> Distress
            </button>
            <button
              onClick={() => setActiveTab('health')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'health' ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <HeartPulse className="w-4 h-4" /> Health
            </button>
            <button
              onClick={() => setActiveTab('kanban')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'kanban' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <KanbanSquare className="w-4 h-4" /> Kanban
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'audit' ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Database className="w-4 h-4" /> Audit
            </button>
            <button
              onClick={() => setActiveTab('knowledge')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'knowledge' ? 'bg-amber-50 text-amber-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <BookOpen className="w-4 h-4" /> Knowledge
            </button>
            
            <div className="w-full h-px bg-slate-200 my-4"></div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-3">Nodal Office & Services</div>
            
            <button
              onClick={() => setActiveTab('service_requests')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center justify-between w-full text-left ${
                activeTab === 'service_requests' ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className="flex items-center gap-2">
                <FileCheck className="w-4 h-4" /> Service Requests
              </span>
              {serviceRequests.length > 0 && (
                <span className="text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded-full font-bold">
                  {serviceRequests.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('hostel_requests')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center justify-between w-full text-left ${
                activeTab === 'hostel_requests' ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className="flex items-center gap-2">
                <Users className="w-4 h-4" /> Hostel & Mess
              </span>
              {hostelRequests.length > 0 && (
                <span className="text-[10px] bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full font-bold">
                  {hostelRequests.length}
                </span>
              )}
            </button>

            <div className="w-full h-px bg-slate-200 my-4"></div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-3">Standard Views</div>
            
            <button
              onClick={() => setActiveTab('grievances')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all w-full text-left ${
                activeTab === 'grievances' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              Grievances
            </button>
            <button
              onClick={() => setActiveTab('clubs')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all w-full text-left ${
                activeTab === 'clubs' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              Clubs
            </button>
            <button
              onClick={() => setActiveTab('bookings')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all w-full text-left ${
                activeTab === 'bookings' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              Bookings
            </button>
            <button
              onClick={() => setActiveTab('lost_found')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all w-full text-left ${
                activeTab === 'lost_found' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              Lost & Found
            </button>
            
            <div className="w-full h-px bg-slate-200 my-4"></div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-3">Reports</div>
            
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'analytics' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <BarChart3 className="w-4 h-4" /> Analytics
            </button>
            <button
              onClick={() => setActiveTab('broadcasts')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-3 w-full text-left ${
                activeTab === 'broadcasts' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Radio className="w-4 h-4" /> Broadcasts
            </button>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 min-w-0 flex flex-col gap-6">
            {['service_requests', 'hostel_requests', 'grievances', 'clubs', 'bookings', 'lost_found'].includes(activeTab) ? (
              <>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <h2 className="text-xl font-bold text-slate-800 capitalize flex items-center gap-2">
                    {activeTab === 'service_requests' ? 'Student Service Requests (Nodal Office)' : activeTab === 'hostel_requests' ? 'Hostel & Mess Requests' : activeTab === 'lost_found' ? 'Lost & Found' : activeTab}
                  </h2>
                  <div className="relative w-full sm:w-72">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input 
                      type="text" 
                      placeholder="Search by ID, name, or description..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                    />
                  </div>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                  {loading ? (
                    <div className="p-12 text-center text-slate-500">
                      <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3"></div>
                      Loading data...
                    </div>
                  ) : (
                    <div className="overflow-x-auto min-h-[500px]">
                      <table className="w-full text-left border-collapse">
<thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                    <th className="px-6 py-4">Tracking ID / User</th>
                    <th className="px-6 py-4">Details</th>
                    <th className="px-6 py-4">Date & Time</th>
                    <th className="px-6 py-4">Current Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {activeTab === 'service_requests' ? (
                    filteredServiceRequests.length > 0 ? filteredServiceRequests.map(s => (
                      <tr key={s.id || s.request_no} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 align-top">
                          <span className="font-mono font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded-md text-xs">{s.request_no}</span>
                          <div className="text-xs text-slate-500 mt-1 font-mono">{s.student_id}</div>
                        </td>
                        <td className="px-6 py-4 align-top max-w-md">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-bold uppercase">{s.category}</span>
                            <span className="font-semibold text-slate-900 text-sm">{s.title}</span>
                          </div>
                          <p className="text-xs text-slate-600 line-clamp-2">{s.description}</p>
                          {s.assigned_office && (
                            <div className="text-[11px] text-slate-400 mt-1">Office: {s.assigned_office}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 align-top text-slate-500 whitespace-nowrap text-xs">
                          <div>{new Date(s.created_at).toLocaleDateString()}</div>
                          {s.sla_due_date && <div className="text-amber-600 font-medium mt-0.5">SLA: {s.sla_due_date}</div>}
                        </td>
                        <td className="px-6 py-4 align-top whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeColor(s.status)}`}>
                            {getStatusIcon(s.status)}
                            {s.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 align-top text-right">
                          <div className="flex items-center justify-end gap-2">
                            <select 
                              className="text-xs bg-white border border-slate-200 rounded-md px-2 py-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                              value={s.status.toUpperCase()}
                              onChange={(e) => handleStatusUpdate(s.id || s.request_no, 'service_request', e.target.value)}
                            >
                              <option value="SUBMITTED">Submitted</option>
                              <option value="IN_REVIEW">In Review</option>
                              <option value="APPROVED">Approved</option>
                              <option value="REJECTED">Rejected</option>
                              <option value="RESOLVED">Resolved</option>
                              <option value="CLOSED">Closed</option>
                            </select>
                            <button
                              onClick={() => handleDeleteTicket(s.id || s.request_no, 'service_request')}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                              title="Delete Service Request Permanently"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500">No service requests found.</td></tr>
                    )
                  ) : activeTab === 'hostel_requests' ? (
                    filteredHostelRequests.length > 0 ? filteredHostelRequests.map(h => (
                      <tr key={h.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 align-top">
                          <div className="font-semibold text-slate-900">{h.student_id}</div>
                          <div className="text-xs text-slate-500 mt-1 font-mono">Req #{h.id}</div>
                        </td>
                        <td className="px-6 py-4 align-top">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-50 text-purple-700 font-medium text-xs border border-purple-100">
                            {h.type}
                          </span>
                          <div className="mt-2 text-xs text-slate-700">{h.details}</div>
                        </td>
                        <td className="px-6 py-4 align-top text-slate-500 whitespace-nowrap text-xs">
                          {h.created_at ? new Date(h.created_at).toLocaleString() : 'N/A'}
                        </td>
                        <td className="px-6 py-4 align-top whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeColor(h.status)}`}>
                            {getStatusIcon(h.status)}
                            {h.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 align-top text-right">
                          <div className="flex items-center justify-end gap-2">
                            <select 
                              className="text-xs bg-white border border-slate-200 rounded-md px-2 py-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                              value={h.status}
                              onChange={(e) => handleStatusUpdate(h.id, 'hostel', e.target.value)}
                            >
                              <option value="pending">Pending</option>
                              <option value="in_progress">In Progress</option>
                              <option value="resolved">Resolved</option>
                              <option value="rejected">Rejected</option>
                            </select>
                            <button
                              onClick={() => handleDeleteTicket(h.id, 'hostel')}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                              title="Delete Hostel Request Permanently"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500">No hostel requests found.</td></tr>
                    )
                  ) : activeTab === 'grievances' ? (
                    filteredGrievances.length > 0 ? filteredGrievances.map(g => (
                      <tr key={g.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 align-top">
                          <span className="font-mono font-medium text-slate-700 bg-slate-100 px-2 py-1 rounded-md text-xs">{g.id}</span>
                        </td>
                        <td className="px-6 py-4 align-top max-w-md">
                          <p className="text-slate-800 line-clamp-2">{g.description}</p>
                          {g.withdrawal_reason && (
                            <div className="mt-2 text-xs bg-rose-50 border border-rose-100 text-rose-700 px-2.5 py-1.5 rounded-md">
                              <strong>Withdrawal Reason:</strong> {g.withdrawal_reason}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 align-top text-slate-500 whitespace-nowrap">
                          {new Date(g.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 align-top whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeColor(g.status)}`}>
                            {getStatusIcon(g.status)}
                            {g.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 align-top text-right">
                          <div className="flex items-center justify-end gap-2">
                            <select 
                              disabled={g.status === 'Withdrawn'}
                              className="text-xs bg-white border border-slate-200 rounded-md px-2 py-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:bg-slate-50"
                              value={g.status}
                              onChange={(e) => handleStatusUpdate(g.id, 'grievance', e.target.value)}
                            >
                              <option value="Received & Secured">Received & Secured</option>
                              <option value="Under Investigation">Under Investigation</option>
                              <option value="Action Taken">Action Taken</option>
                              <option value="Resolved">Resolved</option>
                              <option value="Rejected">Rejected</option>
                              <option value="Withdrawn" disabled>Withdrawn</option>
                            </select>
                            <button
                              onClick={() => handleDeleteTicket(g.id, 'grievance')}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                              title="Delete Grievance Permanently"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500">No grievances found.</td></tr>
                    )
                  ) : activeTab === 'clubs' ? (
                    filteredClubApps.length > 0 ? filteredClubApps.map(c => (
                      <tr key={c.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 align-top">
                          <div className="font-semibold text-slate-900">{c.student_name}</div>
                          <div className="text-xs text-slate-500 mt-1 font-mono">App #{c.id}</div>
                        </td>
                        <td className="px-6 py-4 align-top">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 font-medium text-xs border border-indigo-100">
                            {c.club_id}
                          </span>
                          {c.withdrawal_reason && (
                            <div className="mt-2 text-xs bg-rose-50 border border-rose-100 text-rose-700 px-2.5 py-1.5 rounded-md">
                              <strong>Withdrawal Reason:</strong> {c.withdrawal_reason}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 align-top text-slate-500 whitespace-nowrap">
                          {new Date(c.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 align-top whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeColor(c.status)}`}>
                            {getStatusIcon(c.status)}
                            {c.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 align-top text-right">
                          <div className="flex items-center justify-end gap-2">
                            <select 
                              disabled={c.status === 'Withdrawn'}
                              className="text-xs bg-white border border-slate-200 rounded-md px-2 py-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:bg-slate-50"
                              value={c.status}
                              onChange={(e) => handleStatusUpdate(c.id, 'club', e.target.value)}
                            >
                              <option value="Application Forwarded">Application Forwarded</option>
                              <option value="Under Review">Under Review</option>
                              <option value="Approved">Approved</option>
                              <option value="Rejected">Rejected</option>
                              <option value="Waitlisted">Waitlisted</option>
                              <option value="Withdrawn" disabled>Withdrawn</option>
                            </select>
                            <button
                              onClick={() => handleDeleteTicket(c.id, 'club')}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                              title="Delete Club Application Permanently"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500">No club applications found.</td></tr>
                    )
                  ) : activeTab === 'bookings' ? (
                    filteredBookings.length > 0 ? filteredBookings.map(b => (
                      <tr key={b.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 align-top">
                          <div className="font-semibold text-slate-900">{b.student_id}</div>
                          <div className="text-xs text-slate-500 mt-1 font-mono">Booking #{b.id}</div>
                        </td>
                        <td className="px-6 py-4 align-top">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 font-medium text-xs border border-amber-100">
                            Facility #{b.facility_id}
                          </span>
                          <div className="mt-2 text-xs text-slate-700">
                            <strong>Purpose:</strong> {b.purpose}
                          </div>
                        </td>
                        <td className="px-6 py-4 align-top text-slate-500 whitespace-nowrap text-xs">
                          <div><strong>Date:</strong> {b.date}</div>
                          <div>{b.start_time} - {b.end_time}</div>
                        </td>
                        <td className="px-6 py-4 align-top whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeColor(b.status)}`}>
                            {getStatusIcon(b.status)}
                            {b.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 align-top text-right">
                          <div className="flex items-center justify-end gap-2">
                            <select 
                              className="text-xs bg-white border border-slate-200 rounded-md px-2 py-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                              value={b.status}
                              onChange={(e) => handleStatusUpdate(b.id, 'booking' as any, e.target.value)}
                            >
                              <option value="pending">Pending</option>
                              <option value="confirmed">Confirmed</option>
                              <option value="cancelled">Cancelled</option>
                            </select>
                            <button
                              onClick={() => handleDeleteTicket(b.id, 'booking')}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                              title="Delete Booking Permanently"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500">No bookings found.</td></tr>
                    )
                  ) : (
                    filteredLostAndFound.length > 0 ? filteredLostAndFound.map(l => (
                      <tr key={l.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 align-top">
                          <div className="font-semibold text-slate-900">{l.student_id}</div>
                          <div className="text-xs text-slate-500 mt-1 font-mono">Post #{l.id} ({l.type.toUpperCase()})</div>
                        </td>
                        <td className="px-6 py-4 align-top">
                          <div className="font-semibold text-slate-800 text-sm">{l.title}</div>
                          <p className="text-xs text-slate-600 line-clamp-2 mt-1">{l.description}</p>
                        </td>
                        <td className="px-6 py-4 align-top text-slate-500 whitespace-nowrap text-xs">
                          {new Date(l.date_posted).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 align-top whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeColor(l.status)}`}>
                            {getStatusIcon(l.status)}
                            {l.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 align-top text-right">
                          <div className="flex items-center justify-end gap-2">
                            <select 
                              className="text-xs bg-white border border-slate-200 rounded-md px-2 py-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                              value={l.status}
                              onChange={(e) => handleStatusUpdate(l.id, 'lost_found' as any, e.target.value)}
                            >
                              <option value="open">Open</option>
                              <option value="claimed">Claimed</option>
                              <option value="resolved">Resolved</option>
                            </select>
                            <button
                              onClick={() => handleDeleteTicket(l.id, 'lost_found')}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                              title="Delete Lost & Found Post Permanently"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500">No lost and found items.</td></tr>
                    )
                  )}
                </tbody>
                                    </table>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="w-full">
                {activeTab === 'remediation' && <CognitiveRemediationTab />}
            {activeTab === 'compliance' && <ComplianceTab />}
                {activeTab === 'live_sessions' && <LiveSessionsTab />}
                {activeTab === 'verifications' && <VerificationsTab />}
                {activeTab === 'broadcasts' && <BroadcastsTab />}
                {activeTab === 'distress' && <DistressTab />}
                {activeTab === 'health' && <AgentHealthTab />}
                {activeTab === 'kanban' && <KanbanTab grievances={grievances} handleStatusUpdate={handleStatusUpdate} />}
                {activeTab === 'audit' && <AuditTab />}
                {activeTab === 'knowledge' && <KnowledgeTab />}
                {activeTab === 'analytics' && <AnalyticsTab analytics={analytics} />}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ==========================================
// NEW FEATURE COMPONENTS
// ==========================================

function DistressTab() {
  const [mockAlerts, setMockAlerts] = useState([
    { id: 'AL-9021', student: 'Rajesh K. (22BCE)', trigger: 'Mentioned severe anxiety about fee deadline', sentiment: 'Critical', time: '2 mins ago', status: 'Unassigned', transcript: "I just can't take this anymore. The fees are due tomorrow and my loan didn't come through. I feel completely helpless and overwhelmed." },
    { id: 'AL-9020', student: 'Priya M. (21BEE)', trigger: 'Repeated phrases indicating depression', sentiment: 'High', time: '14 mins ago', status: 'Unassigned', transcript: "I haven't been able to sleep or study for weeks. Everything feels pointless right now. I don't know who to talk to." },
    { id: 'AL-9018', student: 'Anonymous', trigger: 'Keywords related to self-harm', sentiment: 'Severe', time: '45 mins ago', status: 'Routed to Counselor', transcript: "[Redacted by Safety Filter]" },
  ]);

  const handleRoute = (id: string) => {
    setMockAlerts(alerts => alerts.map(a => a.id === id ? { ...a, status: 'Routed to Counselor' } : a));
  };

  const sentimentData = [
    { name: 'Mon', stress: 12 },
    { name: 'Tue', stress: 19 },
    { name: 'Wed', stress: 15 },
    { name: 'Thu', stress: 35 },
    { name: 'Fri', stress: 42 }, // Peak around exams
    { name: 'Sat', stress: 28 },
    { name: 'Sun', stress: 18 },
  ];

  return (
    <div className="p-6 bg-slate-50 min-h-[600px] flex flex-col gap-6">
      
      {/* Top row: Alerts & Sentiment */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[320px]">
        
        {/* Real-time Distress Alerts */}
        <div className="lg:col-span-3 bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex flex-col h-full">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <AlertOctagon className="w-5 h-5 text-rose-600 animate-pulse" /> Real-time Distress Alerts
            </h3>
            <span className="text-xs bg-rose-100 text-rose-700 px-2 py-1 rounded font-bold">
              {mockAlerts.filter(a => a.status === 'Unassigned').length} Active
            </span>
          </div>
          <div className="space-y-4 flex-1 overflow-y-auto pr-2">
            {mockAlerts.map(alert => (
              <div key={alert.id} className={`p-4 border rounded-lg ${alert.status === 'Unassigned' ? 'border-rose-200 bg-rose-50' : 'border-slate-200 bg-slate-50'}`}>
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm">{alert.student}</span>
                    <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded font-bold ${
                      alert.sentiment === 'Severe' ? 'bg-rose-600 text-white' : 
                      alert.sentiment === 'Critical' ? 'bg-rose-200 text-rose-800' : 
                      'bg-amber-100 text-amber-800'
                    }`}>
                      {alert.sentiment}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500">{alert.time}</span>
                </div>
                <p className="text-xs text-slate-700 font-medium mb-1">Trigger: <span className="font-normal text-slate-600">{alert.trigger}</span></p>
                <div className="mt-3 bg-white p-3 rounded border border-slate-100 text-sm italic text-slate-600 border-l-2 border-l-rose-400">
                  "{alert.transcript}"
                </div>
                
                {/* Counseling Handoff */}
                <div className="mt-4 pt-4 border-t border-slate-200/50 flex justify-between items-center">
                  <span className="text-xs font-medium text-slate-500">Status: {alert.status}</span>
                  {alert.status === 'Unassigned' && (
                    <button 
                      onClick={() => handleRoute(alert.id)}
                      className="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm flex items-center gap-2"
                    >
                      <UserPlus className="w-3.5 h-3.5" /> Route to Counselor
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sentiment Analytics */}
        <div className="lg:col-span-2 bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex flex-col h-full">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-2">
            <Activity className="w-5 h-5 text-indigo-600" /> Campus Stress Index
          </h3>
          <p className="text-xs text-slate-500 mb-6">Aggregate student sentiment and stress levels based on conversational AI interactions.</p>
          
          <div className="flex-1 min-h-[150px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sentimentData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#e11d48" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#e11d48" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <RechartsTooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Area type="monotone" dataKey="stress" stroke="#e11d48" strokeWidth={3} fillOpacity={1} fill="url(#colorStress)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-100 flex items-start gap-2">
            <Bell className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-800">
              <span className="font-semibold block mb-0.5">High Stress Trend Detected</span>
              Mid-term examinations start next week. Stress indicators are up 42% compared to baseline.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}




function AnalyticsTab({ analytics }: { analytics: any }) {
  if (!analytics) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <h3 className="text-lg font-semibold mb-4">Grievance Status Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={analytics.grievances}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label
                >
                  {analytics.grievances.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'][index % 5]} />
                  ))}
                </Pie>
                <RechartsTooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <h3 className="text-lg font-semibold mb-4">Facility Bookings</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.bookings}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function ComplianceTab() {
  const [tickets] = React.useState([
    { id: 'TKT-8901', type: 'Anti-Ragging', student: 'Anonymous', sla: '2 Hrs', status: 'Breach Risk', assignee: 'Nodal Officer 1' },
    { id: 'TKT-8905', type: 'Harassment', student: 'Confidential', sla: '14 Hrs', status: 'Warning', assignee: 'Nodal Officer 2' },
    { id: 'TKT-8890', type: 'General Grievance', student: '24CSE001', sla: '12 Days', status: 'On Track', assignee: 'Dept Head CSE' }
  ]);

  return (
    <div className="p-6 bg-slate-50 min-h-[600px]">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6 h-[480px]">
        <div className="lg:col-span-2 bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex flex-col h-full">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-600" /> SLA Breach Warning Matrix
            </h3>
            <span className="text-xs bg-rose-100 text-rose-700 px-2 py-1 rounded font-bold">2 Critical</span>
          </div>
          <div className="overflow-x-auto overflow-y-auto flex-1">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-y border-slate-200 sticky top-0">
                <tr>
                  <th className="px-4 py-3 font-semibold">Ticket / Type</th>
                  <th className="px-4 py-3 font-semibold">SLA Countdown</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tickets.map(t => (
                  <tr key={t.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{t.id}</div>
                      <div className="text-xs text-slate-500">{t.type}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`font-mono font-medium ${t.sla.includes('Hrs') ? 'text-rose-600' : 'text-slate-600'}`}>
                        {t.sla}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        t.status === 'Breach Risk' ? 'bg-rose-100 text-rose-700' :
                        t.status === 'Warning' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                      }`}>
                        {t.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button className="text-blue-600 hover:text-blue-800 text-xs font-medium border border-blue-200 hover:bg-blue-50 px-3 py-1.5 rounded transition-colors flex items-center gap-1 ml-auto">
                        <Gavel className="w-3.5 h-3.5" /> Fwd to SGRC
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex flex-col h-full">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-indigo-600" /> ATR Generator
          </h3>
          <p className="text-sm text-slate-500 mb-6">Generate standardized Action Taken Reports for UGC, NAAC, or accreditation bodies.</p>
          
          <div className="space-y-4 flex-1">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Report Period</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option>Q3 2026 (Jul - Sep)</option>
                <option>Q2 2026 (Apr - Jun)</option>
                <option>Annual 2025-26</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Target Authority</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option>University Grants Commission (UGC)</option>
                <option>National Assessment (NAAC)</option>
                <option>Internal Management</option>
              </select>
            </div>
          </div>
          
          <button className="w-full mt-6 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm py-2.5 rounded-lg flex items-center justify-center gap-2 transition-colors">
            <Download className="w-4 h-4" /> Generate Digitally Signed PDF
          </button>
        </div>
      </div>
    </div>
  );
}

function LiveSessionsTab() {
  const [activeSession, setActiveSession] = React.useState<string | null>('SESS-102');
  
  const sessions = [
    { id: 'SESS-102', student: '24CSE001', topic: 'Fee Payment Issue', status: 'High Friction', agent: 'VIGBOT' },
    { id: 'SESS-105', student: '22BME014', topic: 'Attendance Exemption', status: 'Normal', agent: 'VIGBOT' },
    { id: 'SESS-109', student: 'Anonymous', topic: 'Hostel Complaint', status: 'Escalating', agent: 'VIGBOT' },
  ];

  const transcript = [
    { role: 'user', content: 'I tried paying my fees but the portal crashed and money was deducted!', time: '10:42 AM' },
    { role: 'agent', content: 'I understand you are facing a fee payment issue. Please check your bank statement in 3-5 working days.', time: '10:42 AM' },
    { role: 'user', content: 'I cant wait 5 days! The deadline is tomorrow and my hall ticket is blocked. Help me NOW.', time: '10:43 AM' },
    { role: 'agent', content: 'According to regulation 4.2, late fee of Rs.500 applies after the deadline.', time: '10:43 AM' },
  ];

  return (
    <div className="flex h-[600px] bg-slate-50">
      <div className="w-1/3 border-r border-slate-200 bg-white flex flex-col">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <h3 className="font-semibold text-slate-800">Active Sessions (12)</h3>
          <span className="flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
        </div>
        <div className="overflow-y-auto flex-1 p-2 space-y-1">
          {sessions.map(s => (
            <div 
              key={s.id} 
              onClick={() => setActiveSession(s.id)}
              className={`p-3 rounded-lg cursor-pointer border ${activeSession === s.id ? 'bg-blue-50 border-blue-200' : 'bg-white border-transparent hover:border-slate-200'}`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-medium text-sm text-slate-900">{s.student}</span>
                <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded font-bold ${s.status === 'High Friction' ? 'bg-rose-100 text-rose-700' : s.status === 'Escalating' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}>{s.status}</span>
              </div>
              <div className="text-xs text-slate-500 truncate">{s.topic}</div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="flex-1 flex flex-col bg-white">
        {activeSession ? (
          <>
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <div>
                <h3 className="font-semibold text-slate-900">Session {activeSession}</h3>
                <div className="text-xs text-slate-500">Shadowing VIGBOT in real-time...</div>
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 bg-white border border-slate-200 rounded text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-1 transition-colors">
                  <UserX className="w-3.5 h-3.5" /> End Session
                </button>
              </div>
            </div>
            
            <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-slate-50/50">
              {transcript.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-xs font-medium text-slate-500">{msg.role === 'user' ? 'Student' : 'VIGBOT'}</span>
                    <span className="text-[10px] text-slate-400">{msg.time}</span>
                  </div>
                  <div className={`p-3 rounded-lg text-sm max-w-[80%] relative group ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-sm'}`}>
                    {msg.content}
                    {msg.role === 'agent' && (
                      <button title="Flag Hallucination/Error" className="absolute -right-8 top-2 p-1 text-slate-300 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">
                        <AlertOctagon className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="p-4 border-t border-slate-200 bg-white">
              <div className="flex gap-3">
                <button className="flex-1 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 rounded-lg py-2.5 text-sm font-semibold flex items-center justify-center gap-2 transition-colors">
                  <Ear className="w-4 h-4" /> Whisper Context to Agent
                </button>
                <button className="flex-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg py-2.5 text-sm font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm">
                  <MessageSquareOff className="w-4 h-4" /> Human Takeover
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            Select a session to begin shadowing
          </div>
        )}
      </div>
    </div>
  );
}

function VerificationsTab() {
  return (
    <div className="p-6 bg-slate-50 min-h-[600px] flex flex-col md:flex-row gap-6">
      <div className="flex-1 space-y-6">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" /> Pending Exemptions & Waivers
          </h3>
          <div className="space-y-3">
            <div className="p-4 border border-slate-100 rounded-lg bg-slate-50 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <div className="font-medium text-slate-900">Medical Attendance Exemption</div>
                <div className="text-sm text-slate-500">Student: 23MEC045 • Requested 75% threshold relaxation (medical condonation)</div>
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 text-xs font-medium bg-white border border-rose-200 text-rose-600 rounded hover:bg-rose-50 transition-colors">Reject</button>
                <button className="px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white rounded hover:bg-emerald-700 transition-colors shadow-sm">Approve Override</button>
              </div>
            </div>
            <div className="p-4 border border-slate-100 rounded-lg bg-slate-50 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <div className="font-medium text-slate-900">Fee Payment Hold Override</div>
                <div className="text-sm text-slate-500">Student: 21BEE092 • Unlock hall ticket generation temporarily</div>
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 text-xs font-medium bg-white border border-rose-200 text-rose-600 rounded hover:bg-rose-50 transition-colors">Reject</button>
                <button className="px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white rounded hover:bg-emerald-700 transition-colors shadow-sm">Approve Override</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="w-full md:w-80 shrink-0">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 h-full">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-600" /> Document Verification
          </h3>
          <p className="text-sm text-slate-500 mb-4">Cryptographically verify uploaded medical certificates or receipts.</p>
          
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Document Hash / ID</label>
              <input type="text" placeholder="e.g. hash_8f92a3..." className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg transition-colors">
              Verify Digital Signature
            </button>
            
            <div className="mt-6 p-4 rounded-lg bg-slate-50 border border-slate-100 hidden">
              {/* This would show after verification */}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BroadcastsTab() {
  return (
    <div className="p-6 bg-slate-50 min-h-[600px] flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Radio className="w-5 h-5 text-indigo-600" /> Push Campus Alert
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Banner Message</label>
              <textarea rows={3} placeholder="e.g., The fee payment portal will be down for maintenance from 2 PM to 4 PM today." className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"></textarea>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Target Cohort</label>
              <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option>All Students</option>
                <option>B.Tech CSE Only</option>
                <option>Hostel Residents</option>
              </select>
            </div>
            <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2">
              <Send className="w-4 h-4" /> Broadcast to Portals
            </button>
          </div>
        </div>
        
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 border-l-4 border-l-amber-500">
          <h3 className="font-semibold text-slate-900 mb-1 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-500" /> Temporary Guardrail Override
          </h3>
          <p className="text-xs text-slate-500 mb-4">Inject situational directives directly into the AI\'s system prompt.</p>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">System Directive</label>
              <textarea rows={3} placeholder="e.g., If asked about tomorrow\'s internal exam, state that it is rescheduled to Monday due to heavy rain." className="w-full bg-amber-50/50 border border-amber-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"></textarea>
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Expiry</label>
                <select className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500">
                  <option>1 Hour</option>
                  <option>24 Hours</option>
                  <option>Until Revoked</option>
                </select>
              </div>
              <div className="flex items-end flex-1">
                <button className="w-full bg-amber-100 hover:bg-amber-200 text-amber-800 text-sm font-semibold py-2 rounded-lg transition-colors border border-amber-300">
                  Inject Guardrail
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


function AgentHealthTab() {
  return (
    <div className="p-6 bg-slate-50 min-h-[600px] flex flex-col gap-6">
      <h2 className="text-xl font-bold text-slate-800 mb-2">Agent Health & Telemetry</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">System Uptime</div>
          <div className="text-2xl font-bold text-emerald-600">99.98%</div>
        </div>
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">Avg Response Latency</div>
          <div className="text-2xl font-bold text-slate-900">840ms</div>
        </div>
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">Hallucination Rate</div>
          <div className="text-2xl font-bold text-emerald-600">&lt; 0.1%</div>
        </div>
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-500 mb-1">API Token Usage (30d)</div>
          <div className="text-2xl font-bold text-slate-900">14.2M / 20M</div>
        </div>
      </div>
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex-1">
        <h3 className="font-semibold text-slate-800 mb-4">Live Sub-Agent Status</h3>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="pb-3 font-medium">Agent</th>
              <th className="pb-3 font-medium">Role</th>
              <th className="pb-3 font-medium">Status</th>
              <th className="pb-3 font-medium">Last Sync</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-slate-50">
              <td className="py-3 font-medium">Support_VIGBOT</td>
              <td className="py-3 text-slate-500">Frontline Triage</td>
              <td className="py-3"><span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">ONLINE</span></td>
              <td className="py-3 text-slate-500">Just now</td>
            </tr>
            <tr className="border-b border-slate-50">
              <td className="py-3 font-medium">Nav_Agent_Omega</td>
              <td className="py-3 text-slate-500">Campus Maps & Routing</td>
              <td className="py-3"><span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">ONLINE</span></td>
              <td className="py-3 text-slate-500">2m ago</td>
            </tr>
            <tr className="border-b border-slate-50">
              <td className="py-3 font-medium">Policy_Validator_9</td>
              <td className="py-3 text-slate-500">Compliance Checking</td>
              <td className="py-3"><span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">ONLINE</span></td>
              <td className="py-3 text-slate-500">1m ago</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KanbanTab({ grievances, handleStatusUpdate }: any) {
  const statuses = ['Pending', 'In Progress', 'Resolved'];
  return (
    <div className="p-6 bg-slate-50 min-h-[600px] flex flex-col h-full">
      <h2 className="text-xl font-bold text-slate-800 mb-6">Grievance Resolution Board</h2>
      <div className="flex gap-6 flex-1 overflow-x-auto pb-4">
        {statuses.map(status => (
          <div key={status} className="flex-1 min-w-[300px] bg-slate-100 rounded-xl p-4 flex flex-col">
            <h3 className="font-bold text-slate-700 mb-4 flex items-center justify-between">
              {status}
              <span className="bg-slate-200 text-slate-600 px-2 py-0.5 rounded text-xs">
                {grievances.filter((g: any) => g.status === status).length}
              </span>
            </h3>
            <div className="flex flex-col gap-3 overflow-y-auto">
              {grievances.filter((g: any) => g.status === status).map((g: any) => (
                <div key={g.id} className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
                  <div className="text-xs font-bold text-blue-600 mb-1">{g.category}</div>
                  <div className="font-medium text-slate-900 mb-2">{g.description}</div>
                  <div className="text-xs text-slate-500 flex justify-between items-center mt-4">
                    <span>{g.student_id}</span>
                    {status !== 'Resolved' && (
                      <button 
                        onClick={() => handleStatusUpdate(g.id, status === 'Pending' ? 'In Progress' : 'Resolved')}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Move →
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AuditTab() {
  const auditLogs = [
    { id: 1, time: '10:42 AM', action: 'Distress Protocol Triggered', user: 'VIGBOT', detail: 'Flagged chat #892 for manual review due to negative sentiment.' },
    { id: 2, time: '10:15 AM', action: 'Knowledge Base Queried', user: 'VIGBOT', detail: 'Fetched policy: Hostel Leave Guidelines 2024.' },
    { id: 3, time: '09:30 AM', action: 'Automated Email Sent', user: 'System', detail: 'Sent resolution receipt to 21BEE092@student.edu.' },
    { id: 4, time: '08:00 AM', action: 'Database Backup', user: 'System', detail: 'Nightly automated backup completed successfully.' },
  ];
  return (
    <div className="p-6 bg-slate-50 min-h-[600px] flex flex-col gap-6">
      <h2 className="text-xl font-bold text-slate-800 mb-2">System Audit Logs</h2>
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex-1 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-4 font-medium text-slate-500">Time</th>
              <th className="px-6 py-4 font-medium text-slate-500">Actor</th>
              <th className="px-6 py-4 font-medium text-slate-500">Action</th>
              <th className="px-6 py-4 font-medium text-slate-500">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {auditLogs.map(log => (
              <tr key={log.id} className="hover:bg-slate-50/50">
                <td className="px-6 py-4 text-slate-500 whitespace-nowrap">{log.time}</td>
                <td className="px-6 py-4 font-medium">{log.user}</td>
                <td className="px-6 py-4 text-slate-800">{log.action}</td>
                <td className="px-6 py-4 text-slate-500">{log.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KnowledgeTab() {
  return (
    <div className="p-6 bg-slate-50 min-h-[600px] flex flex-col gap-6">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-xl font-bold text-slate-800">Knowledge Base (RAG)</h2>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          + Upload Document
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm md:col-span-2">
          <h3 className="font-semibold text-slate-800 mb-4">Indexed Documents</h3>
          <div className="space-y-3">
            {[
              { name: 'Student Code of Conduct 2024.pdf', tokens: '45k', status: 'Indexed' },
              { name: 'Hostel Rules & Regulations.pdf', tokens: '12k', status: 'Indexed' },
              { name: 'Fee Structure AY2024-25.xlsx', tokens: '8k', status: 'Indexed' },
              { name: 'Exam Rescheduling Policy.pdf', tokens: '15k', status: 'Indexing...' },
            ].map(doc => (
              <div key={doc.name} className="flex justify-between items-center p-3 hover:bg-slate-50 rounded-lg border border-transparent hover:border-slate-100 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded flex items-center justify-center">📄</div>
                  <div>
                    <div className="text-sm font-medium text-slate-800">{doc.name}</div>
                    <div className="text-xs text-slate-500">{doc.tokens} tokens</div>
                  </div>
                </div>
                <span className={`text-xs font-bold px-2 py-1 rounded ${doc.status === 'Indexed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm h-fit">
          <h3 className="font-semibold text-slate-800 mb-4">Vector DB Stats</h3>
          <div className="space-y-4 text-sm">
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <span className="text-slate-500">Total Vectors</span>
              <span className="font-bold text-slate-800">12,405</span>
            </div>
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <span className="text-slate-500">Embedding Model</span>
              <span className="font-bold text-slate-800">text-embedding-3-small</span>
            </div>
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <span className="text-slate-500">Vector Dimension</span>
              <span className="font-bold text-slate-800">1536</span>
            </div>
            <div className="flex justify-between pb-2">
              <span className="text-slate-500">Last Sync</span>
              <span className="font-bold text-slate-800">Today, 02:00 AM</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}




// ============================================================================
// COGNITIVE REMEDIATION & GEMINI GOVERNANCE TAB (NODAL OFFICER SURVEILLANCE)
// ============================================================================
function CognitiveRemediationTab() {
  const [remediations, setRemediations] = useState<any[]>([]);
  const [summary, setSummary] = useState({
    total_audited: 0,
    active_rules: 0,
    policy_protected: 0,
    inactive_rules: 0,
    raw_feedback_count: 0
  });
  const [recentFeedback, setRecentFeedback] = useState<any[]>([]);
  const [geminiStatus, setGeminiStatus] = useState<any>({
    enable_gemini: false,
    masked_api_key: '',
    has_key: false,
    active_model: 'gemini-2.5-flash',
    available_models: ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-3.5-flash'],
    quota: {
      daily_requests_used: 0,
      daily_requests_limit: 1500,
      daily_requests_remaining: 1500,
      minute_requests_used: 0,
      minute_requests_limit: 15,
      minute_requests_remaining: 15,
      total_requests_all_time: 0,
      recent_calls: []
    }
  });

  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'ACTIVE' | 'POLICY_PROTECTED' | 'INACTIVE'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Key Switcher & Config State
  const [showConfigBox, setShowConfigBox] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
  const [showKeyText, setShowKeyText] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash');
  const [enableGeminiToggle, setEnableGeminiToggle] = useState(false);
  const [updatingConfig, setUpdatingConfig] = useState(false);
  const [configMessage, setConfigMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Ping State
  const [pinging, setPinging] = useState(false);
  const [pingResult, setPingResult] = useState<{ success: boolean; latency_ms?: number; message?: string; error?: string } | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [remRes, gemRes] = await Promise.all([
        fetchCognitiveRemediations(),
        fetchGeminiStatus()
      ]);

      if (remRes.success) {
        setRemediations(remRes.remediations || []);
        if (remRes.summary) setSummary(remRes.summary);
        if (remRes.recentFeedback) setRecentFeedback(remRes.recentFeedback);
      }

      if (gemRes.success) {
        setGeminiStatus(gemRes);
        setSelectedModel(gemRes.active_model || 'gemini-2.5-flash');
        setEnableGeminiToggle(Boolean(gemRes.enable_gemini));
      }
    } catch (e) {
      console.error('Failed to load cognitive remediation data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleStatus = async (remId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    const res = await updateRemediationStatus(remId, nextStatus);
    if (res.success) {
      setRemediations(prev =>
        prev.map(r => (r.remediation_id === remId ? { ...r, status: nextStatus } : r))
      );
      setSummary(prev => ({
        ...prev,
        active_rules: nextStatus === 'ACTIVE' ? prev.active_rules + 1 : Math.max(0, prev.active_rules - 1),
        inactive_rules: nextStatus === 'INACTIVE' ? prev.inactive_rules + 1 : Math.max(0, prev.inactive_rules - 1)
      }));
    } else {
      alert(res.error || 'Failed to update rule status.');
    }
  };

  const handleDeleteRule = async (remId: string) => {
    if (!window.confirm(`Permanently delete remediation rule ${remId}? The bot will revert to default routing for these queries.`)) {
      return;
    }
    const res = await deleteRemediationRule(remId);
    if (res.success) {
      setRemediations(prev => prev.filter(r => r.remediation_id !== remId));
      loadData();
    } else {
      alert(res.error || 'Failed to delete remediation rule.');
    }
  };

  const handleSaveGeminiConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdatingConfig(true);
    setConfigMessage(null);

    const payload: { apiKey?: string; enableGemini: boolean; model: string } = {
      enableGemini: enableGeminiToggle,
      model: selectedModel
    };
    if (newApiKey.trim()) {
      payload.apiKey = newApiKey.trim();
    }

    const res = await updateGeminiConfig(payload);
    setUpdatingConfig(false);

    if (res.success) {
      setConfigMessage({ text: res.message || 'Gemini configuration successfully verified and saved!', type: 'success' });
      setNewApiKey('');
      loadData();
    } else {
      setConfigMessage({ text: res.error || 'Failed to update Gemini configuration.', type: 'error' });
    }
  };

  const handlePingGemini = async () => {
    setPinging(true);
    setPingResult(null);
    const res = await pingGeminiConnection();
    setPinging(false);
    setPingResult(res);
  };

  // Filtered Remediations
  const filteredRemediations = remediations.filter(r => {
    if (filter === 'ACTIVE' && r.status !== 'ACTIVE') return false;
    if (filter === 'POLICY_PROTECTED' && r.status !== 'POLICY_PROTECTED') return false;
    if (filter === 'INACTIVE' && r.status !== 'INACTIVE') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchQuery = (r.user_query || '').toLowerCase().includes(q);
      const matchReason = (r.mismatch_reason || '').toLowerCase().includes(q);
      const matchTarget = (r.target_entity || '').toLowerCase().includes(q);
      const matchIntent = (r.intended_intent || '').toLowerCase().includes(q);
      const matchTriggers = Array.isArray(r.trigger_patterns) && r.trigger_patterns.some((t: string) => t.toLowerCase().includes(q));
      return matchQuery || matchReason || matchTarget || matchIntent || matchTriggers;
    }
    return true;
  });

  const quota = geminiStatus.quota || {};
  const dailyUsed = quota.daily_requests_used || 0;
  const dailyLimit = quota.daily_requests_limit || 1500;
  const dailyRemaining = quota.daily_requests_remaining ?? 1500;
  const usedPct = Math.min(100, Math.round((dailyUsed / dailyLimit) * 100));

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wide uppercase bg-purple-500/20 text-purple-200 border border-purple-400/30 flex items-center gap-1.5">
                <Sparkles className="w-3 h-3 text-purple-300 animate-pulse" /> Cognitive Remediation Hub
              </span>
              <span className="text-xs text-purple-200/80 font-mono">Neon PostgreSQL Sync</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">AI Feedback Surveillance & Gemini Governance</h2>
            <p className="text-sm text-purple-200/80 max-w-2xl">
              Monitor queries disliked by students in real-time, inspect Gemini intent-audit diagnoses, review self-learned Dijkstra routing rules pushed to Neon, and manage Google Gemini API quotas & active credentials.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              onClick={handlePingGemini}
              disabled={pinging}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white/10 hover:bg-white/20 text-white border border-white/10 transition-all cursor-pointer disabled:opacity-50"
              title="Send lightweight diagnostic ping to Google Gemini API"
            >
              <Zap className={`w-3.5 h-3.5 text-amber-300 ${pinging ? 'animate-spin' : ''}`} />
              {pinging ? 'Pinging Gemini...' : 'Ping Gemini API'}
            </button>

            <button
              onClick={() => setShowConfigBox(!showConfigBox)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-purple-500 hover:bg-purple-600 text-white shadow-sm transition-all cursor-pointer"
            >
              <KeyRound className="w-3.5 h-3.5" />
              {showConfigBox ? 'Hide API Key Manager' : 'Switch Gemini API Key'}
            </button>

            <button
              onClick={loadData}
              disabled={loading}
              className="inline-flex items-center gap-1 px-3 py-2 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/15 text-slate-200 border border-white/10 transition-all cursor-pointer"
              title="Refresh live data from Neon DB"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Live Ping Notification Banner */}
        {pingResult && (
          <div className={`mt-4 p-3 rounded-xl text-xs flex items-center justify-between border ${
            pingResult.success ? 'bg-emerald-500/20 border-emerald-400/40 text-emerald-100' : 'bg-rose-500/20 border-rose-400/40 text-rose-100'
          }`}>
            <div className="flex items-center gap-2">
              {pingResult.success ? <CheckCircle className="w-4 h-4 text-emerald-300" /> : <AlertCircle className="w-4 h-4 text-rose-300" />}
              <span>{pingResult.message || pingResult.error}</span>
            </div>
            {pingResult.latency_ms !== undefined && (
              <span className="font-mono font-bold bg-black/20 px-2 py-0.5 rounded text-[10px]">
                {pingResult.latency_ms} ms roundtrip
              </span>
            )}
          </div>
        )}
      </div>

      {/* Top 4 Telemetry Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Gemini Free Tier Quota */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Daily API Quota</div>
            <div className="p-1.5 bg-blue-50 text-blue-700 rounded-lg">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
              <span>{dailyRemaining.toLocaleString()}</span>
              <span className="text-xs font-semibold text-slate-400 font-sans">/ {dailyLimit.toLocaleString()} RPD</span>
            </div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">Remaining Google Gemini Free Calls</div>
          </div>
          {/* Visual Progress Bar */}
          <div className="space-y-1">
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  usedPct > 80 ? 'bg-rose-500' : usedPct > 50 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.max(5, usedPct)}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>{dailyUsed} calls used today</span>
              <span>15 RPM Limit</span>
            </div>
          </div>
        </div>

        {/* Card 2: Engine Status & Active Key */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Gemini Engine Status</div>
            <div className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded-full ${geminiStatus.enable_gemini ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <span className="text-xs font-bold text-slate-700">
                {geminiStatus.enable_gemini ? 'ENABLED' : 'PAUSED'}
              </span>
            </div>
          </div>
          <div>
            <div className="text-sm font-bold text-slate-900 font-mono truncate">
              {geminiStatus.masked_api_key || 'No Key Configured'}
            </div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">Active Credential (Masked)</div>
          </div>
          <div className="pt-1 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-500 font-medium">Active Model:</span>
            <span className="font-bold font-mono text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200/60 text-[10px]">
              {geminiStatus.active_model || 'gemini-2.5-flash'}
            </span>
          </div>
        </div>

        {/* Card 3: Active Remediations in Neon */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Rules in Neon</div>
            <div className="p-1.5 bg-purple-50 text-purple-700 rounded-lg">
              <Bot className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-black text-purple-700 tracking-tight">
              {summary.active_rules} <span className="text-xs font-bold text-slate-400 font-sans">Rules</span>
            </div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">Self-Learned Query Interceptors</div>
          </div>
          <div className="pt-1 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-500 font-medium">Runtime Routing:</span>
            <span className="font-bold text-emerald-700">Tier 0 Intercept</span>
          </div>
        </div>

        {/* Card 4: Policy Defense Guardrails */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Policy Guardrails Upheld</div>
            <div className="p-1.5 bg-emerald-50 text-emerald-700 rounded-lg">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-black text-emerald-700 tracking-tight">
              {summary.policy_protected} <span className="text-xs font-bold text-slate-400 font-sans">Protected</span>
            </div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">Clause 2.1 RLAC & Rules Upheld</div>
          </div>
          <div className="pt-1 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-500 font-medium">Integrity Check:</span>
            <span className="font-bold text-blue-700">100% Zero-Leak</span>
          </div>
        </div>
      </div>

      {/* API Key Switcher & Configuration Drawer */}
      {showConfigBox && (
        <div className="bg-white rounded-2xl border-2 border-purple-200 p-6 shadow-sm space-y-5 animate-in fade-in-50 duration-200">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 text-purple-700 rounded-xl">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Switch Google Gemini API Key & Engine Config</h3>
                <p className="text-xs text-slate-500">
                  Validated live with Google before persisting to Neon DB <code className="font-mono text-purple-700">system_settings</code>. Survives Render reboots.
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowConfigBox(false)}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-lg"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSaveGeminiConfig} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Input New API Key */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                  <span>Google Gemini API Key</span>
                  <button
                    type="button"
                    onClick={() => setShowKeyText(!showKeyText)}
                    className="text-[11px] text-purple-700 hover:underline cursor-pointer"
                  >
                    {showKeyText ? 'Hide Key' : 'Reveal Key'}
                  </button>
                </label>
                <div className="relative">
                  <input
                    type={showKeyText ? 'text' : 'password'}
                    placeholder="Paste new API Key (e.g. AIzaSy... or AQ.Ab8RN6...)"
                    value={newApiKey}
                    onChange={e => setNewApiKey(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 text-xs font-mono transition-all"
                  />
                </div>
                <p className="text-[11px] text-slate-400">Leave blank if only updating model or enablement status.</p>
              </div>

              {/* Model Selection */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700">Target Gemini Model</label>
                <select
                  value={selectedModel}
                  onChange={e => setSelectedModel(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 text-xs font-mono bg-white cursor-pointer"
                >
                  {(geminiStatus.available_models || ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-3.5-flash']).map((m: string) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-400">gemini-2.5-flash / gemini-1.5-flash recommended for fastest sub-second audits.</p>
              </div>
            </div>

            {/* Enable Gemini Toggle */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-xs font-bold text-slate-800">Enable Autonomous Gemini Feedback Loop</div>
                <div className="text-[11px] text-slate-500">
                  When active, student downvotes automatically trigger the Gemini cognitive audit in the background and persist verified remediations to Neon.
                </div>
              </div>
              <button
                type="button"
                onClick={() => setEnableGeminiToggle(!enableGeminiToggle)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  enableGeminiToggle ? 'bg-purple-600' : 'bg-slate-300'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    enableGeminiToggle ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {/* Status Toast */}
            {configMessage && (
              <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                configMessage.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
              }`}>
                {configMessage.type === 'success' ? <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />}
                <span>{configMessage.text}</span>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfigBox(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updatingConfig}
                className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 shadow-sm transition-all disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
              >
                {updatingConfig ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                {updatingConfig ? 'Validating with Google...' : 'Verify & Switch API Key'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === 'ALL' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            All Audited ({summary.total_audited})
          </button>
          <button
            onClick={() => setFilter('ACTIVE')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              filter === 'ACTIVE' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <CheckCircle className="w-3 h-3" /> Active in Neon ({summary.active_rules})
          </button>
          <button
            onClick={() => setFilter('POLICY_PROTECTED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
              filter === 'POLICY_PROTECTED' ? 'bg-purple-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Shield className="w-3 h-3" /> Policy Upheld ({summary.policy_protected})
          </button>
          <button
            onClick={() => setFilter('INACTIVE')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === 'INACTIVE' ? 'bg-slate-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Inactive ({summary.inactive_rules})
          </button>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search query, landmark, reason..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400"
          />
        </div>
      </div>

      {/* Disliked Queries & Remediations List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 space-y-3">
            <RefreshCw className="w-8 h-8 text-purple-600 animate-spin mx-auto" />
            <div className="text-sm font-semibold text-slate-700">Loading live audit trail from Neon PostgreSQL...</div>
          </div>
        ) : filteredRemediations.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 space-y-2">
            <Bot className="w-10 h-10 text-slate-300 mx-auto" />
            <div className="text-base font-bold text-slate-800">No Audited Queries Found</div>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              No disliked queries matching the active filter. When a student downvotes a query in the chat, the autonomous Gemini loop audits it here.
            </p>
          </div>
        ) : (
          filteredRemediations.map((rem: any) => {
            const isActive = rem.status === 'ACTIVE';
            const isPolicy = rem.status === 'POLICY_PROTECTED';
            const triggers: string[] = Array.isArray(rem.trigger_patterns) ? rem.trigger_patterns : [];

            return (
              <div
                key={rem.remediation_id}
                className={`bg-white rounded-2xl border transition-all shadow-2xs hover:shadow-xs overflow-hidden ${
                  isActive ? 'border-emerald-200/90' : isPolicy ? 'border-purple-200/90' : 'border-slate-200'
                }`}
              >
                {/* Header Strip */}
                <div className="p-4 sm:px-6 bg-slate-50/80 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                      isActive ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
                      isPolicy ? 'bg-purple-100 text-purple-800 border border-purple-300' :
                      'bg-slate-200 text-slate-700 border border-slate-300'
                    }`}>
                      {isActive && <CheckCircle className="w-3 h-3 text-emerald-600" />}
                      {isPolicy && <Shield className="w-3 h-3 text-purple-600" />}
                      {rem.status || 'UNKNOWN'}
                    </span>

                    <span className="font-bold font-mono text-[10px] text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                      {rem.intended_intent || 'GENERAL'}
                    </span>

                    <span className="font-mono text-[11px] text-slate-400">
                      ID: {rem.remediation_id}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-slate-400 text-[11px]">
                    <span>{rem.created_at ? new Date(rem.created_at).toLocaleString() : ''}</span>
                    
                    <button
                      onClick={() => handleToggleStatus(rem.remediation_id, rem.status)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-colors border ${
                        isActive ? 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100' :
                        'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                      }`}
                      title={isActive ? 'Pause rule from intercepting' : 'Activate rule for NLU interception'}
                    >
                      {isActive ? 'Pause Rule' : 'Activate Rule'}
                    </button>

                    <button
                      onClick={() => handleDeleteRule(rem.remediation_id)}
                      className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Delete rule permanently"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Main Card Content */}
                <div className="p-5 sm:p-6 space-y-4">
                  {/* Student Disliked Query Section */}
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">
                      <ThumbsDown className="w-3.5 h-3.5 text-rose-500" />
                      <span>Student Disliked Query</span>
                    </div>
                    <div className="text-base font-extrabold text-slate-900 bg-rose-50/50 p-3 rounded-xl border border-rose-100/80 font-sans">
                      "{rem.user_query}"
                    </div>
                    {rem.student_comment && (
                      <div className="text-xs text-rose-800 bg-rose-100/60 px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5">
                        <span className="font-bold uppercase text-[10px] tracking-wide">Student Feedback:</span>
                        <span>"{rem.student_comment}"</span>
                      </div>
                    )}
                  </div>

                  {/* Side-by-Side: Delivered vs Gemini Audit */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Left: Bot Output Delivered */}
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
                      <div className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
                        <span>Delivered Bot Output (Disliked)</span>
                        <span className="text-[10px] font-mono text-slate-400">Conversation Turn</span>
                      </div>
                      <div className="text-xs text-slate-700 font-sans line-clamp-4 leading-relaxed whitespace-pre-wrap">
                        {rem.bot_output || 'No output recorded'}
                      </div>
                    </div>

                    {/* Right: Gemini Audit Diagnosis */}
                    <div className={`p-4 rounded-xl border space-y-2 ${
                      rem.mismatch_detected ? 'bg-purple-50/70 border-purple-200' : 'bg-emerald-50/70 border-emerald-200'
                    }`}>
                      <div className="text-xs font-bold uppercase tracking-wider flex items-center justify-between">
                        <span className={rem.mismatch_detected ? 'text-purple-900' : 'text-emerald-900'}>
                          Gemini Autonomous Audit Diagnosis
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          rem.mismatch_detected ? 'bg-purple-200 text-purple-900' : 'bg-emerald-200 text-emerald-900'
                        }`}>
                          {rem.mismatch_detected ? 'Mismatch Detected' : 'Policy Upheld'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-800 font-medium leading-relaxed">
                        {rem.mismatch_reason || 'No audit explanation provided.'}
                      </p>
                    </div>
                  </div>

                  {/* What Gemini Instructed & Pushed to Neon */}
                  {rem.mismatch_detected && (
                    <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-100 space-y-2.5">
                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                        <span className="font-bold text-indigo-950 uppercase tracking-wider flex items-center gap-1.5">
                          <Bot className="w-4 h-4 text-indigo-600" />
                          Gemini Remediation Pushed to Neon
                        </span>
                        <div className="flex items-center gap-2 font-mono text-[11px]">
                          <span className="text-indigo-700 font-semibold">Routing Action:</span>
                          <span className="bg-white px-2 py-0.5 rounded border border-indigo-200 font-bold text-indigo-900">
                            {rem.routing_action || 'TOOL_ROUTING'}
                          </span>
                        </div>
                      </div>

                      {rem.target_entity && (
                        <div className="text-xs text-slate-700 flex items-center gap-2">
                          <span className="font-bold text-slate-500">Target Entity:</span>
                          <span className="font-mono font-bold bg-white px-2 py-0.5 rounded border border-slate-200 text-purple-700">
                            {rem.target_entity}
                          </span>
                        </div>
                      )}

                      {triggers.length > 0 && (
                        <div className="space-y-1.5">
                          <div className="text-[11px] font-bold text-slate-500">Learned Trigger Variations:</div>
                          <div className="flex flex-wrap gap-1.5">
                            {triggers.map((t, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-white text-indigo-900 border border-indigo-200/80 shadow-2xs"
                              >
                                "{t}"
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
