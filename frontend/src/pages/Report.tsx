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
    <div className="border border-gray-100 rounded-xl bg-white mb-3 overflow-hidden shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full grid grid-cols-3 p-4 gap-4 bg-gray-50 hover:bg-[#556B2F]/5 transition-colors items-center text-left focus:outline-none"
      >
        <span className="font-mono font-medium text-[#2F4F4F] truncate">{cadastralNumber}</span>
        <span className="text-gray-600 font-medium">{matches} <span className="text-xs font-normal text-gray-400">полів збігається</span></span>
        <span className={`${mismatches > 0 ? 'text-red-500' : 'text-gray-400'} font-medium`}>
          {mismatches} <span className="text-xs font-normal">розбіжностей</span>
        </span>
      </button>
      
      {isOpen && (
        <div className="p-6 border-t border-gray-100 bg-white">
          <h5 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Порівняння даних</h5>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400">
                  <th className="pb-2 font-medium">Характеристика</th>
                  <th className="pb-2 font-medium">Держгеокадастр</th>
                  <th className="pb-2 font-medium">Реєстр речових прав</th>
                  <th className="pb-2 font-medium italic">Статус</th>
                </tr>
              </thead>
              <tbody className="text-gray-600 divide-y divide-gray-50">
                <tr>
                  <td className="py-3 font-medium">Площа</td>
                  <td className="py-3">0.1250 га</td>
                  <td className="py-3">0.1250 га</td>
                  <td className="py-3 text-green-500 italic">Співпадіння</td>
                </tr>
                <tr>
                  <td className="py-3 font-medium">Цільове призначення</td>
                  <td className="py-3">Для будівництва</td>
                  <td className="py-3">Для с/г потреб</td>
                  <td className="py-3 text-red-500 italic font-medium">Розбіжність</td>
                </tr>
                <tr>
                  <td className="py-3 font-medium">Форма власності</td>
                  <td className="py-3">Приватна</td>
                  <td className="py-3">Комунальна</td>
                  <td className="py-3 text-red-500 italic font-medium">Розбіжність</td>
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
          <div className="flex justify-between items-center mb-10">
            <div className="flex gap-4 items-center">
              <div className="relative w-72">
                <input 
                  type="text" 
                  placeholder="Пошук..." 
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border-2 border-gray-100 focus:outline-none focus:border-[#556B2F]/50 transition-all text-sm"
                />
                <button className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#556B2F] transition-colors focus:outline-none">
                  <svg 
                    className="w-5 h-5" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
              <button className="px-6 py-2 rounded-lg border-2 border-[#556B2F] text-[#556B2F] font-bold hover:bg-[#556B2F] hover:text-white transition-all shadow-sm">
                Фільтрація
              </button>
            </div>
            <div>
              <button className="px-8 py-2 rounded-lg bg-[#556B2F] text-white font-bold hover:bg-[#4a5d28] shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5">
                Звіт
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
        <div className="w-1/4 min-w-[300px] border-l border-gray-200 bg-white flex flex-col h-full shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] z-10">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-100 bg-gray-50 flex items-center justify-center">
            <h3 className="font-bold text-[#2F4F4F] flex items-center gap-2">
              <svg className="w-5 h-5 text-[#556B2F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              AI Помічник
            </h3>
          </div>

          {/* Chat Messages Area */}
          <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4 bg-white/50">
            <div className="self-start bg-gray-100 rounded-2xl rounded-tl-sm p-3 max-w-[85%] text-sm text-gray-700 shadow-sm">
              Вітаю! Я ваш AI-асистент. Допомогти проаналізувати розбіжності у знайдених даних?
            </div>
            {/* Placeholder message */}
            {/* <div className="self-end bg-[#556B2F] text-white rounded-2xl rounded-tr-sm p-3 max-w-[85%] text-sm shadow-sm">
              Так, покажи мені неспівпадіння для активу А.
            </div> */}
          </div>

          {/* Chat Input Area */}
          <div className="p-4 border-t border-gray-100 bg-white">
            <div className="relative">
              <input
                type="text"
                placeholder="Напишіть повідомлення..."
                className="w-full px-4 py-3 pr-12 rounded-xl text-sm border border-gray-200 focus:outline-none focus:border-[#556B2F] focus:ring-1 focus:ring-[#556B2F] transition-all bg-gray-50 focus:bg-white"
              />
              <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-[#556B2F] hover:bg-[#556B2F]/10 rounded-lg transition-colors">
                <svg className="w-5 h-5 translate-x-px" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
