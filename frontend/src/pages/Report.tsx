import React, { useState } from 'react';
import Navbar from '../components/Navbar';

interface ReportTableItemProps {
  cadastralNumber: string;
  matches: number;
  mismatches: number;
  defaultOpen?: boolean;
}

const ReportTableItem: React.FC<ReportTableItemProps> = ({ 
  cadastralNumber, matches, mismatches, defaultOpen = false 
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-100 rounded-xl bg-white mb-4 overflow-hidden shadow-sm p-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full grid grid-cols-3 p-3 gap-4 hover:bg-gray-50 transition-colors items-center text-left focus:outline-none rounded-lg"
      >
        <span className="font-mono text-base font-semibold text-gray-900 truncate tracking-tight">{cadastralNumber}</span>
        <span className="text-gray-500 text-sm font-medium">{matches} <span className="text-xs font-normal text-gray-400">полів збігається</span></span>
        <span className={`${mismatches > 0 ? 'bg-red-50 text-red-600 border-red-100' : 'bg-gray-50 text-gray-400 border-gray-100'} border px-3 py-1 rounded-full text-xs font-semibold inline-flex items-center justify-center w-fit`}>
          {mismatches} <span className="ml-1 font-normal opacity-80">розбіжностей</span>
        </span>
      </button>
      
      {isOpen && (
        <div className="p-6 border-t border-gray-50 bg-white">
          <h5 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-6">Порівняння даних реєстрів</h5>
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
                <tr>
                  <td className="py-4 text-xs font-semibold text-gray-500 uppercase">Площа</td>
                  <td className="py-4 font-medium">0.1250 га</td>
                  <td className="py-4 font-medium">0.1250 га</td>
                  <td className="py-4 text-green-600 font-medium italic text-xs">Співпадіння</td>
                </tr>
                <tr>
                  <td className="py-4 text-xs font-semibold text-gray-500 uppercase">Цільове призначення</td>
                  <td className="py-4 font-medium">Для будівництва</td>
                  <td className="py-4 font-medium text-red-600">Для с/г потреб</td>
                  <td className="py-4 text-red-500 italic font-bold text-xs">Розбіжність</td>
                </tr>
                <tr>
                  <td className="py-4 text-xs font-semibold text-gray-500 uppercase">Форма власності</td>
                  <td className="py-4 font-medium">Приватна</td>
                  <td className="py-4 font-medium text-red-600">Комунальна</td>
                  <td className="py-4 text-red-500 italic font-bold text-xs">Розбіжність</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default function Report() {
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
                  placeholder="Пошук по базі..." 
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:bg-white focus:ring-2 focus:ring-slate-200 transition-all text-sm placeholder:text-gray-400"
                />
                <button className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 transition-colors focus:outline-none">
                  <svg 
                    className="w-4 h-4" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
              <button className="px-5 py-2.5 rounded-xl border border-gray-200 bg-white text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors shadow-sm inline-flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                Фільтрація
              </button>
            </div>
            <div>
              <button className="px-6 py-2.5 rounded-xl bg-slate-800 text-white text-sm font-medium hover:bg-slate-700 shadow-sm transition-all flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Завантажити звіт
              </button>
            </div>
          </div>

          {/* Table Header Labels */}
          <div className="grid grid-cols-3 px-4 mb-4 text-xs font-bold text-gray-400 uppercase tracking-widest gap-4">
            <div>Кадастровий номер</div>
            <div>Співпадіння</div>
            <div>Неспівпадіння</div>
          </div>

          {/* Report Content - Table Items */}
          <div className="flex-1 flex flex-col">
            <ReportTableItem 
              cadastralNumber="4624884200:15:000:0684" 
              matches={12} 
              mismatches={2} 
              defaultOpen={true}
            />
            
            <ReportTableItem 
              cadastralNumber="4624884200:15:000:0125" 
              matches={14} 
              mismatches={0}
            />

            <ReportTableItem 
              cadastralNumber="4624884200:15:000:0991" 
              matches={8} 
              mismatches={6}
            />
          </div>
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
          <div className="flex-1 p-5 overflow-y-auto flex flex-col gap-5 bg-white space-y-4 pr-2 custom-scrollbar">
            <div className="self-start bg-gray-50 text-gray-700 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed w-fit max-w-[85%] shadow-sm border border-gray-100/50 transition-all hover:shadow-md">
              Вітаю! Я ваш AI-асистент. Допомогти проаналізувати розбіжності у знайдених даних?
            </div>
            {/* User message placeholder (simulated style) */}
            <div className="self-end bg-slate-800 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed w-fit max-w-[85%] ml-auto shadow-md transition-all hover:shadow-lg">
              Покажи результати по кадастровому номеру 46248...
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
