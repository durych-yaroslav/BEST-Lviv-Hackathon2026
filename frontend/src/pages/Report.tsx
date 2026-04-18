import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

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
    { label: 'Площа (га)', landValue: l.area, propValue: p.total_area, problemKey: 'area' },
    { label: 'Цільове призначення', landValue: l.purpose, propValue: p.type_of_object, problemKey: 'purpose' },
    { label: 'Форма власності / Тип', landValue: l.form_of_ownership, propValue: p.type_of_joint_ownership, problemKey: '' },
    { label: 'Землекористувач / Платник', landValue: l.land_user, propValue: p.name_of_the_taxpayer, problemKey: 'land_user' },
    { label: 'ЄДРПОУ / ІПН', landValue: l.edrpou_of_land_user, propValue: p.tax_number_of_pp, problemKey: 'edrpou_of_land_user' },
    { label: 'Місцезнаходження / Адреса', landValue: l.location, propValue: p.address_of_the_object, problemKey: 'location' },
    { label: 'Частка власності', landValue: l.share_of_ownership, propValue: p.share_of_ownership, problemKey: 'share_of_ownership' },
    { label: 'Дата реєстрації права', landValue: l.date_of_state_registration_of_ownership, propValue: p.date_of_state_registration_of_ownership, problemKey: 'date_of_state_registration_of_ownership' },
  ];
}

// ─── Single record row (accordion) ───────────────────────────────────────────

const RecordRow: React.FC<{ record: Record; defaultOpen?: boolean }> = ({ record, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const mismatchCount = record.problems.length;
  const matchCount = buildComparisonFields(record).length - mismatchCount;
  const cadastral = record.land_data.cadastral_number || record.record_id.slice(0, 18) + '...';
  const compFields = buildComparisonFields(record);

  return (
    <div className="border border-gray-100 rounded-xl bg-white mb-4 overflow-hidden shadow-sm p-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full grid grid-cols-3 p-3 gap-4 hover:bg-gray-50 transition-colors items-center text-left focus:outline-none rounded-lg"
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

      {isOpen && (
        <div className="p-6 border-t border-gray-50 bg-white">
          {/* Problem badges */}
          {mismatchCount > 0 && (
            <div className="mb-5 flex flex-wrap gap-2">
              {record.problems.map(p => (
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
                  const hasProblem = field.problemKey && record.problems.includes(field.problemKey);
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
  const [filterProblems, setFilterProblems] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
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

    if (filterProblems) {
      result = result.filter(r => r.problems.length > 0);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(r => {
        const cadastral = (r.land_data.cadastral_number || '').toLowerCase();
        const landUser = (r.land_data.land_user || '').toLowerCase();
        const location = (r.land_data.location || '').toLowerCase();
        const edrpou = (r.land_data.edrpou_of_land_user || '').toLowerCase();
        const taxpayer = (r.property_data.name_of_the_taxpayer || '').toLowerCase();
        return (
          cadastral.includes(q) ||
          landUser.includes(q) ||
          location.includes(q) ||
          edrpou.includes(q) ||
          taxpayer.includes(q)
        );
      });
    }

    return result;
  }, [records, searchQuery, filterProblems]);

  // Reset to page 1 whenever filter/search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, filterProblems]);

  // ── Pagination slice ──────────────────────────────────────────────────────
  const totalPages = Math.max(1, Math.ceil(filteredRecords.length / PAGE_SIZE));
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredRecords.slice(start, start + PAGE_SIZE);
  }, [filteredRecords, currentPage, PAGE_SIZE]);

  // ── Export as PDF ─────────────────────────────────────────────────────────
  const handleExport = async () => {
    if (!reportId) return;
    const token = localStorage.getItem('token');
    if (!token) { navigate('/login'); return; }

    setExportLoading(true);
    try {
      const res = await fetch(`/api/reports/${reportId}/export/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ record_ids: [] }), // export all records in this report
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

  // ── Stats ─────────────────────────────────────────────────────────────────
  const totalProblems = records.filter(r => r.problems.length > 0).length;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="h-screen bg-[#F8F9FA] flex flex-col font-sans overflow-hidden">
      <Navbar />

      <main className="flex-1 flex w-full h-full min-h-0">
        {/* Left Side: Report Content (75%) */}
        <div className="w-3/4 p-6 md:p-10 flex flex-col overflow-y-auto">

          {/* Header Controls */}
          <div className="flex justify-between items-center mb-8 bg-white p-4 rounded-2xl shadow-sm border border-gray-50">
            <div className="flex gap-3 items-center">
              <div className="relative w-80">
                <input
                  type="text"
                  placeholder="Пошук за кадастровим номером, ЄДРПОУ..."
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
              <button
                onClick={() => setFilterProblems(prev => !prev)}
                className={`px-5 py-2.5 rounded-xl border text-sm font-medium hover:bg-gray-50 transition-colors shadow-sm inline-flex items-center gap-2 ${filterProblems ? 'bg-red-50 border-red-200 text-red-600' : 'bg-white border-gray-200 text-gray-700'}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                {filterProblems ? 'Лише з проблемами' : 'Фільтрація'}
              </button>
            </div>
            <div>
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
                Завантажити звіт
              </button>
            </div>
          </div>

          {/* Stats bar */}
          {!loading && !error && records.length > 0 && (
            <div className="flex gap-4 mb-6">
              <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                <span className="text-2xl font-bold text-slate-800">{records.length}</span>
                <span className="text-xs text-gray-500 font-medium leading-tight">Всього<br/>записів</span>
              </div>
              <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                <span className="text-2xl font-bold text-red-500">{totalProblems}</span>
                <span className="text-xs text-gray-500 font-medium leading-tight">Записів з<br/>розбіжностями</span>
              </div>
              <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                <span className="text-2xl font-bold text-green-600">{records.length - totalProblems}</span>
                <span className="text-xs text-gray-500 font-medium leading-tight">Без<br/>розбіжностей</span>
              </div>
              {(searchQuery || filterProblems) && (
                <div className="bg-white rounded-xl px-5 py-3 shadow-sm border border-gray-100 flex items-center gap-3">
                  <span className="text-2xl font-bold text-slate-600">{filteredRecords.length}</span>
                  <span className="text-xs text-gray-500 font-medium leading-tight">Результатів<br/>фільтру</span>
                </div>
              )}
            </div>
          )}

          {/* Column Headers */}
          <div className="grid grid-cols-3 px-4 mb-4 text-xs font-bold text-gray-400 uppercase tracking-widest gap-4">
            <div>Кадастровий номер</div>
            <div>Співпадіння</div>
            <div>Розбіжності</div>
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
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                              currentPage === item
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
        <div className="w-1/4 min-w-[320px] border-l border-gray-100 bg-white flex flex-col h-full shadow-sm z-10 transition-all">
          {/* Chat Header */}
          <div className="p-5 border-b border-gray-50 bg-white/80 backdrop-blur-sm flex items-center justify-center">
            <h3 className="font-bold text-slate-800 flex items-center gap-2.5 text-sm tracking-tight">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              AI Помічник
            </h3>
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
      </main>
    </div>
  );
}
