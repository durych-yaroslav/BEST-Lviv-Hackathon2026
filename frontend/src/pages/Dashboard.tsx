import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import * as XLSX from 'xlsx';
import Navbar from '../components/Navbar';
import PreviewTable from '../components/PreviewTable';

export default function Dashboard() {
  const navigate = useNavigate();
  const [landFile, setLandFile] = useState<File | null>(null);
  const [propertyFile, setPropertyFile] = useState<File | null>(null);
  const [landData, setLandData] = useState<any[] | null>(null);
  const [propertyData, setPropertyData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  const landInputRef = useRef<HTMLInputElement>(null);
  const propertyInputRef = useRef<HTMLInputElement>(null);

  const parseExcelFile = (file: File): Promise<any[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: 'array' });
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          resolve(jsonData);
        } catch (err) {
          reject(err);
        }
      };
      reader.onerror = (err) => reject(err);
      reader.readAsArrayBuffer(file);
    });
  };

  const handleLandFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLandFile(file);
      try {
        const data = await parseExcelFile(file);
        setLandData(data);
      } catch (err) {
        console.error("Помилка при зчитуванні Реєстру 1:", err);
        alert("Не вдалося розпарсити Реєстр 1");
      }
    }
  };

  const handlePropertyFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setPropertyFile(file);
      try {
        const data = await parseExcelFile(file);
        setPropertyData(data);
      } catch (err) {
        console.error("Помилка при зчитуванні Реєстру 2:", err);
        alert("Не вдалося розпарсити Реєстр 2");
      }
    }
  };

  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!landFile || !propertyFile) {
      setError('Будь ласка, завантажте обидва файли (Реєстр 1 та Реєстр 2) перед аналізом.');
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      setError('Ви не авторизовані. Будь ласка, увійдіть в систему знову.');
      navigate('/login');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('land', landFile);
      formData.append('property', propertyFile);

      // NOTE: Do NOT set Content-Type manually — fetch sets multipart boundary automatically.
      // NOTE: Trailing slash required by Django's APPEND_SLASH middleware.
      const response = await fetch('/api/reports/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        navigate('/login');
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || errorData.detail || errorData.message || `Помилка сервера (${response.status})`);
      }

      const data = await response.json();
      navigate(`/report/${data.report_id}`);
    } catch (err: any) {
      console.error('API Error:', err);
      setError(err.message || 'Сталася помилка при з\'єднанні з сервером.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen bg-[#F8F9FA] flex flex-col font-sans overflow-hidden">
      <Navbar />

      <main className="flex-1 p-6 md:p-10 flex flex-col items-center min-h-0">
        {/* Tables Container */}
        <div className="w-full max-w-[98%] grid grid-cols-1 lg:grid-cols-2 gap-8 mb-6 flex-1 min-h-0">

          {/* Left Table Container */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden min-h-0">
            <div className="py-3 px-6 border-b border-gray-50 flex justify-between items-center bg-white/50">
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
                {landFile ? 'Змінити файл' : 'Завантажити .xlsx файл'}
              </button>
            </div>
            <div className="p-4 flex flex-col items-center justify-center flex-1 overflow-hidden">
              {landData ? (
                <PreviewTable data={landData} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full">
                  <div className="w-20 h-20 mb-4 rounded-full flex items-center justify-center bg-gray-50 text-gray-300">
                    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <p className="text-gray-400 font-light italic">Дані відсутні</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Table Container */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden min-h-0">
            <div className="py-3 px-6 border-b border-gray-50 flex justify-between items-center bg-white/50">
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
                {propertyFile ? 'Змінити файл' : 'Завантажити .xlsx файл'}
              </button>
            </div>
            <div className="p-4 flex flex-col items-center justify-center flex-1 overflow-hidden">
              {propertyData ? (
                <PreviewTable data={propertyData} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full">
                  <div className="w-20 h-20 mb-4 rounded-full flex items-center justify-center bg-gray-50 text-gray-300">
                    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <p className="text-gray-400 font-light italic">Дані відсутні</p>
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Action Button & Error */}
        <div className="w-full max-w-[98%] flex flex-col items-end pb-4">
          {error && (
            <div className="mb-3 w-full p-3 bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl">
              <span className="font-bold">Помилка:</span> {error}
            </div>
          )}
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="px-12 py-4 rounded-full bg-[#556B2F] text-white font-bold text-lg hover:bg-[#4a5d28] shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 transform disabled:opacity-70 disabled:hover:-translate-y-0 flex items-center gap-3"
          >
            {loading && (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            )}
            {loading ? 'Аналізується...' : 'Аналізувати'}
          </button>
        </div>
      </main>
    </div>
  );
}
