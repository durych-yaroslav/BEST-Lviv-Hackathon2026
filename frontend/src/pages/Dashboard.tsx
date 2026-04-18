import { useState, useRef } from 'react';
import Navbar from '../components/Navbar';

export default function Dashboard() {
  const [landFile, setLandFile] = useState<File | null>(null);
  const [propertyFile, setPropertyFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  
  const landInputRef = useRef<HTMLInputElement>(null);
  const propertyInputRef = useRef<HTMLInputElement>(null);

  const handleLandFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setLandFile(e.target.files[0]);
    }
  };

  const handlePropertyFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setPropertyFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!landFile || !propertyFile) {
      alert('Будь ласка, завантажте обидва файли (Реєстр 1 та Реєстр 2) перед аналізом.');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('land', landFile);
      formData.append('property', propertyFile);

      const response = await fetch('/api/reports', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Помилка при створенні звіту');
      }

      const data = await response.json();
      alert(`Аналіз успішно завершено! ID звіту: ${data.report_id}`);
    } catch (err: any) {
      alert(err.message || 'Сталася помилка при відправці файлів');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 p-6 md:p-10 flex flex-col items-center">
        {/* Tables Container */}
        <div className="w-full max-w-[98%] grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">

          {/* Left Table Container */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
            <div className="p-6 border-b border-gray-50 flex justify-between items-center bg-white/50">
              <h3 className="text-lg font-bold text-[#2F4F4F]">Реєстр 1 (Земля)</h3>
              <input 
                type="file" 
                accept=".xlsx" 
                className="hidden" 
                ref={landInputRef}
                onChange={handleLandFileChange}
              />
              <button 
                onClick={() => landInputRef.current?.click()}
                className="text-sm px-4 py-2 rounded-lg bg-[#556B2F]/10 text-[#556B2F] hover:bg-[#556B2F] hover:text-white transition-all font-medium"
              >
                Завантажити .xlsx файл
              </button>
            </div>
            <div className="p-10 flex flex-col items-center justify-center min-h-[600px]">
              <div className={`w-20 h-20 mb-4 rounded-full flex items-center justify-center transition-colors ${landFile ? 'bg-[#556B2F]/20 text-[#556B2F]' : 'bg-gray-50 text-gray-300'}`}>
                <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {landFile ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  )}
                </svg>
              </div>
              <p className={`font-light ${landFile ? 'text-[#2F4F4F] font-medium' : 'text-gray-400 italic'}`}>
                {landFile ? `Файл: ${landFile.name}` : 'Дані відсутні'}
              </p>
            </div>
          </div>

          {/* Right Table Container */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
            <div className="p-6 border-b border-gray-50 flex justify-between items-center bg-white/50">
              <h3 className="text-lg font-bold text-[#2F4F4F]">Реєстр 2 (Нерухомість)</h3>
              <input 
                type="file" 
                accept=".xlsx" 
                className="hidden" 
                ref={propertyInputRef}
                onChange={handlePropertyFileChange}
              />
              <button 
                onClick={() => propertyInputRef.current?.click()}
                className="text-sm px-4 py-2 rounded-lg bg-[#556B2F]/10 text-[#556B2F] hover:bg-[#556B2F] hover:text-white transition-all font-medium"
              >
                Завантажити .xlsx файл
              </button>
            </div>
            <div className="p-10 flex flex-col items-center justify-center min-h-[600px]">
              <div className={`w-20 h-20 mb-4 rounded-full flex items-center justify-center transition-colors ${propertyFile ? 'bg-[#556B2F]/20 text-[#556B2F]' : 'bg-gray-50 text-gray-300'}`}>
                <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {propertyFile ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  )}
                </svg>
              </div>
              <p className={`font-light ${propertyFile ? 'text-[#2F4F4F] font-medium' : 'text-gray-400 italic'}`}>
                {propertyFile ? `Файл: ${propertyFile.name}` : 'Дані відсутні'}
              </p>
            </div>
          </div>

        </div>

        {/* Action Button */}
        <div className="w-full max-w-[98%] flex justify-end">
          <button 
            onClick={handleAnalyze}
            disabled={loading}
            className="px-12 py-4 rounded-full bg-[#556B2F] text-white font-bold text-lg hover:bg-[#4a5d28] shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 transform disabled:opacity-70 disabled:hover:-translate-y-0"
          >
            {loading ? 'Аналізується...' : 'Аналізувати'}
          </button>
        </div>
      </main>
    </div>
  );
}
