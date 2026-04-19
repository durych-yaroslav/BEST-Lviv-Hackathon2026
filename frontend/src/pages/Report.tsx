import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Files, AlertTriangle, CheckCircle2 } from 'lucide-react';

// ─── Types from API (matches RecordSerializer + README schema) ────────────────

interface LandData {
  cadastral_number: string | null;
  koatuu: string | null;
  form_of_ownership: string | null;
  purpose: string | null;
  location: string | null;
  type_of_agricultural_land: string | null;
  area: number | null;
  average_monetary_valuation: number | null;
  edrpou_of_land_user: string | null;
  land_user: string | null;
  share_of_ownership: number | null;
  date_of_state_registration_of_ownership: string | null;
  record_number_of_ownership: string | null;
  authority_that_performed_state_registration_of_ownership: string | null;
  type: string | null;
  subtype: string | null;
}

interface PropertyData {
  tax_number_of_pp: string | null;
  name_of_the_taxpayer: string | null;
  type_of_object: string | null;
  address_of_the_object: string | null;
  date_of_state_registration_of_ownership: string | null;
  date_of_state_registration_of_pledge_of_ownership: string | null;
  total_area: number | null;
  type_of_joint_ownership: string | null;
  share_of_ownership: number | null;
}

interface Record {
  report_id: string;
  record_id: string;
  problems: string[];
  land_data: LandData;
  property_data: PropertyData;
}

// ─── Problem labels (Ukrainian) ───────────────────────────────────────────────

const PROBLEM_LABELS: Record<string, string> = {
  edrpou_of_land_user: 'ЄДРПОУ землекористувача',
  land_user: 'Землекористувач',
  location: 'Місцезнаходження',
  area: 'Площа',
  date_of_state_registration_of_ownership: 'Дата реєстрації права',
  share_of_ownership: 'Частка власності',
  purpose: 'Цільове призначення',
  missing_owner: 'Невідомий власник',
};

// ─── Comparison rows for expanded record detail view ─────────────────────────

interface ComparisonField {
  label: string;
  landValue: string | number | null;
  propValue: string | number | null;
  problemKey: string;
}

function buildComparisonFields(record: Record): ComparisonField[] {
  const { land_data: l, property_data: p } = record;
  return [
    { label: 'Площа', landValue: l.area, propValue: p.total_area, problemKey: 'area' },
    { label: 'Цільове призначення', landValue: l.purpose, propValue: p.type_of_object, problemKey: 'purpose' },
    { label: 'Форма власності / Тип', landValue: l.form_of_ownership, propValue: p.type_of_joint_ownership, problemKey: '' },
    { label: 'Землекористувач / Платник', landValue: l.land_user, propValue: p.name_of_the_taxpayer, problemKey: 'land_user' },
    { label: 'ЄДРПОУ / ІПН', landValue: l.edrpou_of_land_user, propValue: p.tax_number_of_pp, problemKey: 'edrpou_of_land_user' },
    { label: 'Місцезнаходження / Адреса', landValue: l.location, propValue: p.address_of_the_object, problemKey: 'location' },
    // share_of_ownership intentionally excluded per business rules
    { label: 'Дата реєстрації права', landValue: l.date_of_state_registration_of_ownership, propValue: p.date_of_state_registration_of_ownership, problemKey: 'date_of_state_registration_of_ownership' },
  ];
}

// ─── Forgiving business-rules filter ─────────────────────────────────────────

function getFilteredProblems(record: Record): string[] {
  let problems = [...(record.problems || [])];

  // Rule 1: share_of_ownership is never an error
  problems = problems.filter(p => p !== 'share_of_ownership');

  // Rule 2: Area — land > property total area is acceptable (land includes property)
  const landArea = record.land_data?.area ?? 0;
  const propArea = record.property_data?.total_area ?? 0;
  if ((landArea as number) > (propArea as number)) {
    problems = problems.filter(p => p !== 'area');
  }

  // Rule 3: Date — if either date is missing we treat it as acceptable
  const landDate = record.land_data?.date_of_state_registration_of_ownership;
  const propDate = record.property_data?.date_of_state_registration_of_ownership;
  if (!landDate || !propDate) {
    problems = problems.filter(p => p !== 'date_of_state_registration_of_ownership');
  }

  return problems;
}

// ─── Custom Checkbox ──────────────────────────────────────────────────────────

const Checkbox: React.FC<{
  checked: boolean;
  onChange: () => void;
  title?: string;
}> = ({ checked, onChange, title }) => (
  <label
    className="flex items-center cursor-pointer shrink-0"
    title={title}
    onClick={e => e.stopPropagation()}
  >
    <input type="checkbox" checked={checked} onChange={onChange} className="sr-only" />
    <span
      className={`
        w-4 h-4 rounded-[3px] border-2 border-gray-900
        flex items-center justify-center transition-colors
        ${checked ? 'bg-gray-900' : 'bg-white hover:bg-gray-100'}
      `}
    >
      <svg
        className={`w-2.5 h-2.5 text-white transition-opacity ${checked ? 'opacity-100' : 'opacity-0'}`}
        viewBox="0 0 10 8" fill="none" stroke="currentColor"
      >
        <polyline points="1,4 3.5,6.5 9,1" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  </label>
);

// ─── Single record row (accordion) ───────────────────────────────────────────

interface RecordRowProps {
  record: Record;
  defaultOpen?: boolean;
  isSelected: boolean;
  onToggleSelect: (id: string) => void;
}

const RecordRow: React.FC<RecordRowProps> = ({ record, defaultOpen = false, isSelected, onToggleSelect }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  // Apply forgiving business rules — do NOT mutate record.problems
  const filteredProblems = getFilteredProblems(record);
  const mismatchCount = filteredProblems.length;
  const compFields = buildComparisonFields(record);
  const matchCount = compFields.length - mismatchCount;
  const cadastral = record.land_data.cadastral_number || record.record_id.slice(0, 18) + '...';

  return (
    <div className={`border rounded-xl bg-white mb-4 overflow-hidden shadow-sm p-2 transition-colors ${isSelected ? 'border-[#556B2F]/40 bg-[#556B2F]/5' : 'border-gray-100'
      }`}>
      <div className="flex items-center">
        {/* Row content */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex-1 grid grid-cols-3 p-3 gap-4 hover:bg-gray-50 transition-colors items-center text-left focus:outline-none rounded-lg"
        >
          <span className="font-mono text-base font-semibold text-gray-900 truncate tracking-tight">
            {cadastral}
          </span>
          <span className="text-gray-500 text-sm font-medium">
            {matchCount} <span className="text-xs font-normal text-gray-400">полів збігається</span>
          </span>
          <span className={`${mismatchCount > 0 ? 'bg-red-50 text-red-600 border-red-100' : 'bg-green-50 text-green-600 border-green-100'} border px-3 py-1 rounded-full text-xs font-semibold inline-flex items-center justify-center w-fit`}>
            {mismatchCount} <span className="ml-1 font-normal opacity-80">розбіжностей</span>
          </span>
        </button>
        {/* Checkbox — right side */}
        <div className="pl-3 pr-2 flex-shrink-0">
          <Checkbox
            checked={isSelected}
            onChange={() => onToggleSelect(record.record_id)}
          />
        </div>
      </div>

      {isOpen && (
        <div className="p-6 border-t border-gray-50 bg-white">
          {/* Problem badges — only filtered, forgiving set */}
          {mismatchCount > 0 && (
            <div className="mb-5 flex flex-wrap gap-2">
              {filteredProblems.map(p => (
                <span key={p} className="bg-red-50 text-red-600 border border-red-100 rounded-full px-3 py-1 text-xs font-semibold">
                  {PROBLEM_LABELS[p] || p}
                </span>
              ))}
            </div>
          )}

          <h5 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-6">
            Порівняння даних реєстрів
          </h5>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400">
                  <th className="pb-3 text-[11px] font-bold uppercase tracking-wider">Характеристика</th>
                  <th className="pb-3 text-[11px] font-bold uppercase tracking-wider">Держгеокадастр</th>
                  <th className="pb-3 text-[11px] font-bold uppercase tracking-wider">Реєстр речових прав</th>
                  <th className="pb-3 text-[11px] font-bold uppercase tracking-wider italic">Статус</th>
                </tr>
              </thead>
              <tbody className="text-gray-900 divide-y divide-gray-50">
                {compFields.map(field => {
                  // Use forgiving filteredProblems (not raw record.problems) for highlighting
                  const hasProblem = !!field.problemKey && filteredProblems.includes(field.problemKey);
                  const landVal = field.landValue !== null && field.landValue !== undefined ? String(field.landValue) : '—';
                  const propVal = field.propValue !== null && field.propValue !== undefined ? String(field.propValue) : '—';
                  return (
                    <tr key={field.label}>
                      <td className="py-4 text-xs font-semibold text-gray-500 uppercase">{field.label}</td>
                      <td className="py-4 font-medium">{landVal}</td>
                      <td className={`py-4 font-medium ${hasProblem ? 'text-red-600' : ''}`}>{propVal}</td>
                      <td className={`py-4 text-xs italic font-bold ${hasProblem ? 'text-red-500' : 'text-green-600'}`}>
                        {hasProblem ? 'Розбіжність' : 'Співпадіння'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Main Report page ─────────────────────────────────────────────────────────

export default function Report() {
  const { id: reportId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [records, setRecords] = useState<Record[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterProblem, setFilterProblem] = useState('');
  const [sortOrder, setSortOrder] = useState<'none' | 'asc' | 'desc'>('none');
  const [exportLoading, setExportLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [chatOpen, setChatOpen] = useState(false);
  const PAGE_SIZE = 100;

  // ── Fetch records on mount ────────────────────────────────────────────────
  useEffect(() => {
    if (!reportId) {
      setError('Ідентифікатор звіту відсутній. Спочатку завантажте файли.');
      setLoading(false);
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchAllRecords = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch first page to get total count
        const firstRes = await fetch(`/api/reports/${reportId}/records/?page=1&size=50`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!firstRes.ok) {
          const errData = await firstRes.json().catch(() => ({}));
          throw new Error(errData.detail || errData.error || `Помилка сервера: ${firstRes.status}`);
        }
        const firstPage = await firstRes.json();
        const allItems: Record[] = [...firstPage.items];
        const total: number = firstPage.total;

        // If more pages exist, fetch them all in parallel
        if (total > 50) {
          const pageCount = Math.ceil(total / 50);
          const pagePromises = [];
          for (let page = 2; page <= pageCount; page++) {
            pagePromises.push(
              fetch(`/api/reports/${reportId}/records/?page=${page}&size=50`, {
                headers: { Authorization: `Bearer ${token}` },
              }).then(r => r.json())
            );
          }
          const restPages = await Promise.all(pagePromises);
          restPages.forEach(p => allItems.push(...p.items));
        }

        setRecords(allItems);
      } catch (err: any) {
        console.error('Fetch records error:', err);
        setError(err.message || 'Не вдалося завантажити дані звіту. Перевірте підключення.');
      } finally {
        setLoading(false);
      }
    };

    fetchAllRecords();
  }, [reportId, navigate]);

  // ── Local filtering (real-time, no API debounce needed) ──────────────────
  const filteredRecords = useMemo(() => {
    let result = records;

    if (filterProblem) {
      result = result.filter(r => r.problems && r.problems.includes(filterProblem));
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(r => {
        const cadastral  = String(r.land_data?.cadastral_number ?? '').toLowerCase();
        const location   = String(r.land_data?.location ?? '').toLowerCase();
        const address    = String(r.property_data?.address_of_the_object ?? '').toLowerCase();
        const landUser   = String(r.land_data?.land_user ?? '').toLowerCase();
        const taxpayer   = String(r.property_data?.name_of_the_taxpayer ?? '').toLowerCase();
        return (
          cadastral.includes(q) ||
          location.includes(q)  ||
          address.includes(q)   ||
          landUser.includes(q)  ||
          taxpayer.includes(q)
        );
      });
    }

    return result;
  }, [records, searchQuery, filterProblem]);

  // Reset to page 1 whenever filter/search/sort changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, filterProblem, sortOrder]);

  // ── Pagination slice (with optional sort) ────────────────────────────────
  const totalPages = Math.max(1, Math.ceil(filteredRecords.length / PAGE_SIZE));
  const paginatedRecords = useMemo(() => {
    let sorted = [...filteredRecords];
    if (sortOrder === 'desc') {
      sorted.sort((a, b) => (b.problems?.length ?? 0) - (a.problems?.length ?? 0));
    } else if (sortOrder === 'asc') {
      sorted.sort((a, b) => (a.problems?.length ?? 0) - (b.problems?.length ?? 0));
    }
    const start = (currentPage - 1) * PAGE_SIZE;
    return sorted.slice(start, start + PAGE_SIZE);
  }, [filteredRecords, currentPage, PAGE_SIZE, sortOrder]);

  // ── Selection helpers ─────────────────────────────────────────────────────
  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const allPageSelected = paginatedRecords.length > 0 && paginatedRecords.every(r => selectedIds.has(r.record_id));

  const toggleSelectAll = () => {
    if (allPageSelected) {
      setSelectedIds(prev => {
        const next = new Set(prev);
        paginatedRecords.forEach(r => next.delete(r.record_id));
        return next;
      });
    } else {
      setSelectedIds(prev => {
        const next = new Set(prev);
        paginatedRecords.forEach(r => next.add(r.record_id));
        return next;
      });
    }
  };

  // ── Share report ──────────────────────────────────────────────────────────
  const [copied, setCopied] = useState(false);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // ── Export as PDF ─────────────────────────────────────────────────────────
  const handleExport = async () => {
    if (!reportId) return;
    const token = localStorage.getItem('token');
    if (!token) { navigate('/login'); return; }

    // Export only selected records, or all if none selected
    const exportIds = selectedIds.size > 0
      ? Array.from(selectedIds)
      : records.map(r => r.record_id);

    setExportLoading(true);
    try {
      const res = await fetch(`/api/reports/${reportId}/export/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ record_ids: exportIds }),
      });
      if (!res.ok) throw new Error('Не вдалося завантажити PDF');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${reportId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || 'Помилка при завантаженні звіту');
    } finally {
      setExportLoading(false);
    }
  };

  // ── Analytics ─────────────────────────────────────────────────────────────
  const totalRecords = records.length;
  const recordsWithProblems = records.filter(r => r.problems && r.problems.length > 0).length;
  const cleanRecords = totalRecords - recordsWithProblems;
  const totalProblems = recordsWithProblems;

  const PROBLEM_UA: Record<string, string> = {
    area: 'Площа',
    location: 'Місцезнаходження',
    land_user: 'Землекористувач',
    edrpou_of_land_user: 'ЄДРПОУ',
    date_of_state_registration_of_ownership: 'Дата реєстрації',
    share_of_ownership: 'Частка власності',
    purpose: 'Цільове призначення',
    missing_owner: 'Невідомий власник',
  };

  const CHART_COLORS = ['#f87171','#fb923c','#fbbf24','#34d399','#60a5fa','#818cf8','#a78bfa'];

  const problemDistribution = useMemo(() => {
    const counts: Record<string, number> = {};
    records.forEach(r => {
      (r.problems || []).forEach(p => {
        counts[p] = (counts[p] || 0) + 1;
      });
    });
    return Object.entries(counts).map(([key, value]) => ({
      name: PROBLEM_UA[key] || key,
      value,
    }));
  }, [records]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="h-screen bg-[#F8F9FA] flex flex-col font-sans overflow-hidden">
      <Navbar />

      <main className="flex-1 flex w-full h-full min-h-0">
        {/* Left Side: Report Content (75%) */}
        <div className="w-3/4 p-6 md:p-10 flex flex-col overflow-y-auto">

          {/* ── Analytics Dashboard ─────────────────────────────────────────── */}
          {!loading && !error && totalRecords > 0 && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {/* Total */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
                  <div className="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
                    <Files className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-800">{totalRecords}</p>
                    <p className="text-xs text-gray-400 font-medium mt-0.5">Всього об'єктів</p>
                  </div>
                </div>
                {/* Problems */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
                  <div className="w-11 h-11 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-red-500">{recordsWithProblems}</p>
                    <p className="text-xs text-gray-400 font-medium mt-0.5">Знайдено розбіжностей</p>
                  </div>
                </div>
                {/* Clean */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
                  <div className="w-11 h-11 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-emerald-600">{cleanRecords}</p>
                    <p className="text-xs text-gray-400 font-medium mt-0.5">Співпадіння 100%</p>
                  </div>
                </div>
              </div>

              {/* Charts — side by side */}
              <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                 {/* Doughnut: problem type distribution — legend on the left */}
                {problemDistribution.length > 0 && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h4 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Розподіл розбіжностей за типом</h4>
                    <div className="flex items-center gap-4">
                      {/* Custom legend — left side */}
                      <div className="flex flex-col gap-2 min-w-[130px] shrink-0">
                        {problemDistribution.map((entry, index) => (
                          <div key={entry.name} className="flex items-center gap-2">
                            <span
                              className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
                              style={{ background: CHART_COLORS[index % CHART_COLORS.length] }}
                            />
                            <span className="text-xs text-gray-500 leading-tight">{entry.name}</span>
                          </div>
                        ))}
                      </div>
                      {/* Chart — right side */}
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie
                            data={problemDistribution}
                            cx="50%"
                            cy="50%"
                            innerRadius={55}
                            outerRadius={85}
                            paddingAngle={3}
                            dataKey="value"
                          >
                            {problemDistribution.map((_entry, index) => (
                              <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(value: number) => [`${value} записів`, '']}
                            contentStyle={{ borderRadius: '10px', border: '1px solid #f1f5f9', fontSize: '12px' }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Bar chart: match vs mismatch */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <h4 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Знайдено розбіжностей / Співпадіння 100%</h4>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart
                      data={[
                        { name: 'Знайдено розбіжностей', value: recordsWithProblems, fill: '#f87171' },
                        { name: 'Співпадіння 100%', value: cleanRecords, fill: '#34d399' },
                      ]}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                      <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={140}
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        formatter={(value: number) => [`${value} записів`, '']}
                        contentStyle={{ borderRadius: '10px', border: '1px solid #f1f5f9', fontSize: '12px' }}
                        cursor={{ fill: '#f8fafc' }}
                      />
                      <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={40}>
                        {[
                          <Cell key="mismatch" fill="#f87171" />,
                          <Cell key="match" fill="#34d399" />,
                        ]}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}

          {/* Header Controls */}
          <div className="flex justify-between items-center mb-8 bg-white p-4 rounded-2xl shadow-sm border border-gray-50">
            <div className="flex gap-3 items-center">
              <div className="relative w-80">
                <input
                  type="text"
                  placeholder="Пошук: кадастровий №, адреса, землекористувач..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:bg-white focus:ring-2 focus:ring-slate-200 transition-all text-sm placeholder:text-gray-400"
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </span>
              </div>
              <div className="relative">
                <svg className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                <select
                  value={filterProblem}
                  onChange={e => setFilterProblem(e.target.value)}
                  className={`pl-9 pr-8 py-2.5 rounded-xl border text-sm font-medium transition-colors shadow-sm appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-slate-200 ${
                    filterProblem
                      ? 'bg-red-50 border-red-200 text-red-700'
                      : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <option value="">Фільтрація</option>
                  <option value="location">Місцезнаходження</option>
                  <option value="area">Площа</option>
                  <option value="date_of_state_registration_of_ownership">Дата реєстрації права</option>
                  <option value="purpose">Цільове призначення</option>
                  <option value="missing_owner">Невідомий власник</option>
                </select>
                <svg className="w-4 h-4 text-gray-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Share button */}
              <div className="relative">
                <button
                  onClick={handleShare}
                  className="px-5 py-2.5 rounded-xl border border-gray-200 bg-white text-slate-700 text-sm font-medium hover:bg-gray-50 shadow-sm transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                  </svg>
                  Поширити звіт
                </button>
                {copied && (
                  <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs font-medium px-3 py-1.5 rounded-lg whitespace-nowrap shadow-lg animate-fade-in pointer-events-none">
                    ✓ Посилання скопійовано!
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                  </div>
                )}
              </div>

              {/* Export button */}
              <button
                onClick={handleExport}
                disabled={exportLoading}
                className="px-6 py-2.5 rounded-xl bg-slate-800 text-white text-sm font-medium hover:bg-slate-700 shadow-sm transition-all flex items-center gap-2 disabled:opacity-60"
              >
                {exportLoading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                )}
                {selectedIds.size > 0
                  ? `Завантажити звіт (${selectedIds.size})`
                  : 'Завантажити звіт'}
              </button>
            </div>
          </div>

          {/* Stats bar */}
          {!loading && !error && records.length > 0 && (
            <div className="flex gap-4 mb-6">
              <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                <span className="text-2xl font-bold text-slate-800">{records.length}</span>
                <span className="text-xs text-gray-500 font-medium leading-tight">Всього<br />записів</span>
              </div>
              <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                <span className="text-2xl font-bold text-red-500">{totalProblems}</span>
                <span className="text-xs text-gray-500 font-medium leading-tight">Записів з<br />розбіжностями</span>
              </div>
              <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                <span className="text-2xl font-bold text-green-600">{records.length - totalProblems}</span>
                <span className="text-xs text-gray-500 font-medium leading-tight">Без<br />розбіжностей</span>
              </div>
              {(searchQuery || filterProblem) && (
                <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                  <span className="text-2xl font-bold text-slate-600">{filteredRecords.length}</span>
                  <span className="text-xs text-gray-500 font-medium leading-tight">Результатів<br />фільтру</span>
                </div>
              )}
            </div>
          )}

          {/* Column Headers */}
          <div className="flex items-center px-2 mb-4 text-xs font-bold text-gray-400 uppercase tracking-widest">
            {/* Text columns — mirror row button grid */}
            <div className="flex-1 grid grid-cols-3 gap-4 px-3">
              <div>Кадастровий номер</div>
              <div>Співпадіння</div>
              <button
                onClick={() =>
                  setSortOrder(prev =>
                    prev === 'none' ? 'desc' : prev === 'desc' ? 'asc' : 'none'
                  )
                }
                className="flex items-center gap-1.5 hover:text-slate-600 transition-colors group"
                title="Сортувати за кількістю розбіжностей"
              >
                Розбіжності
                <span className="inline-flex flex-col leading-none">
                  <svg
                    className={`w-2.5 h-2.5 transition-colors ${
                      sortOrder === 'asc' ? 'text-slate-700' : 'text-gray-300 group-hover:text-gray-400'
                    }`}
                    viewBox="0 0 10 6" fill="currentColor"
                  >
                    <path d="M5 0l5 6H0z" />
                  </svg>
                  <svg
                    className={`w-2.5 h-2.5 transition-colors ${
                      sortOrder === 'desc' ? 'text-slate-700' : 'text-gray-300 group-hover:text-gray-400'
                    }`}
                    viewBox="0 0 10 6" fill="currentColor"
                  >
                    <path d="M5 6L0 0h10z" />
                  </svg>
                </span>
              </button>
            </div>
            {/* Checkbox column — same padding as row checkboxes */}
            <div className="pl-3 pr-2 flex-shrink-0 flex items-center">
              <Checkbox
                checked={allPageSelected}
                onChange={toggleSelectAll}
                title="Вибрати всі на сторінці"
              />
            </div>
          </div>

          {/* Content States */}
          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center gap-4 text-gray-400">
              <div className="w-10 h-10 border-2 border-gray-200 border-t-[#556B2F] rounded-full animate-spin" />
              <p className="text-sm font-medium">Завантаження даних звіту...</p>
            </div>
          )}

          {error && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center gap-4">
              <div className="bg-red-50 border border-red-100 rounded-2xl p-8 text-center max-w-md">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.834-1.964-.834-2.732 0L3.072 16.5C2.302 18.333 3.264 20 4.804 20z" />
                  </svg>
                </div>
                <p className="text-red-700 font-semibold mb-2">Помилка завантаження</p>
                <p className="text-red-500 text-sm">{error}</p>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="mt-4 px-6 py-2 bg-red-500 text-white rounded-xl text-sm font-medium hover:bg-red-600 transition-colors"
                >
                  Повернутися на головну
                </button>
              </div>
            </div>
          )}

          {!loading && !error && filteredRecords.length === 0 && records.length > 0 && (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-gray-400">
              <svg className="w-12 h-12 opacity-30 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <p className="font-medium">Нічого не знайдено</p>
              <p className="text-sm">Спробуйте змінити пошуковий запит або фільтр</p>
            </div>
          )}

          {!loading && !error && records.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-gray-400">
              <p className="font-medium">Звіт не містить записів</p>
            </div>
          )}

          {/* Records List */}
          {!loading && !error && filteredRecords.length > 0 && (
            <div className="flex-1 flex flex-col">
              {paginatedRecords.map((record, idx) => (
                <RecordRow
                  key={record.record_id}
                  record={record}
                  defaultOpen={idx === 0 && currentPage === 1 && record.problems.length > 0}
                  isSelected={selectedIds.has(record.record_id)}
                  onToggleSelect={toggleSelect}
                />
              ))}

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-4 pb-2 mt-2 border-t border-gray-100">
                  <span className="text-xs text-gray-400 font-medium">
                    Показано {((currentPage - 1) * PAGE_SIZE) + 1}–{Math.min(currentPage * PAGE_SIZE, filteredRecords.length)} з {filteredRecords.length} записів
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="px-2.5 py-1.5 rounded-lg text-xs font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                      title="Перша сторінка"
                    >
                      «
                    </button>
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      ‹ Назад
                    </button>

                    {/* Page number pills */}
                    {Array.from({ length: totalPages }, (_, i) => i + 1)
                      .filter(p => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 2)
                      .reduce<(number | 'ellipsis')[]>((acc, p, i, arr) => {
                        if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push('ellipsis');
                        acc.push(p);
                        return acc;
                      }, [])
                      .map((item, i) =>
                        item === 'ellipsis' ? (
                          <span key={`e${i}`} className="px-1 text-gray-400 text-xs">…</span>
                        ) : (
                          <button
                            key={item}
                            onClick={() => setCurrentPage(item as number)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${currentPage === item
                              ? 'bg-slate-800 text-white border-slate-800'
                              : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                              }`}
                          >
                            {item}
                          </button>
                        )
                      )
                    }

                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      Вперед ›
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className="px-2.5 py-1.5 rounded-lg text-xs font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                      title="Остання сторінка"
                    >
                      »
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Side: AI Chat (25%) */}
        {/* On desktop: always visible. On mobile: slides in as an overlay when chatOpen */}
        <div className={`
          flex flex-col h-full bg-white border-l border-gray-100 shadow-sm z-20 transition-all duration-300
          fixed right-0 top-0 bottom-0 w-[85vw] max-w-[360px]
          md:static md:w-1/4 md:min-w-[300px] md:max-w-none md:translate-x-0
          ${chatOpen ? 'translate-x-0' : 'translate-x-full md:translate-x-0'}
        `}>
          {/* Chat Header */}
          <div className="p-5 border-b border-gray-50 bg-white/80 backdrop-blur-sm flex items-center justify-between">
            <h3 className="font-bold text-slate-800 flex items-center gap-2.5 text-sm tracking-tight">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              AI Помічник
            </h3>
            {/* Close button — visible on mobile only */}
            <button
              onClick={() => setChatOpen(false)}
              className="md:hidden p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Chat Messages Area */}
          <div className="flex-1 p-5 overflow-y-auto flex flex-col gap-5 bg-white space-y-4 pr-2">
            <div className="self-start bg-gray-50 text-gray-700 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed w-fit max-w-[85%] shadow-sm border border-gray-100/50">
              Вітаю! Я ваш AI-асистент. Допомогти проаналізувати розбіжності у знайдених даних?
            </div>
          </div>

          {/* Chat Input Area */}
          <div className="p-5 border-t border-gray-50 bg-white">
            <div className="flex items-center bg-gray-50 rounded-full px-4 py-2 border border-gray-200 shadow-sm focus-within:bg-white focus-within:ring-2 focus-within:ring-slate-100 transition-all">
              <input
                type="text"
                placeholder="Напишіть повідомлення..."
                className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-sm text-gray-900 placeholder-gray-400 py-1"
              />
              <button className="ml-2 bg-slate-800 text-white rounded-full p-2.5 flex items-center justify-center hover:bg-slate-700 transition-all cursor-pointer shadow-sm active:scale-95">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile: backdrop overlay when chat is open */}
        {chatOpen && (
          <div
            className="fixed inset-0 bg-black/30 z-10 md:hidden"
            onClick={() => setChatOpen(false)}
          />
        )}

        {/* Mobile: floating button to open AI chat */}
        <button
          onClick={() => setChatOpen(true)}
          className={`md:hidden fixed bottom-6 right-6 z-30 bg-slate-800 text-white rounded-full p-4 shadow-xl hover:bg-slate-700 transition-all active:scale-95 ${chatOpen ? 'hidden' : 'flex'
            } items-center justify-center`}
          title="AI Помічник"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      </main>
    </div>
  );
}
