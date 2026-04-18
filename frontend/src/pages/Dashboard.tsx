import Navbar from '../components/Navbar';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 p-6 md:p-10 flex flex-col items-center">
        {/* Tables Container */}
        <div className="w-full max-w-[95%] grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">

          {/* Left Table Container */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
            <div className="p-6 border-b border-gray-50 flex justify-between items-center bg-white/50">
              <h3 className="text-lg font-bold text-[#2F4F4F]">Реєстр 1</h3>
              <button className="text-sm px-4 py-2 rounded-lg bg-[#556B2F]/10 text-[#556B2F] hover:bg-[#556B2F] hover:text-white transition-all font-medium">
                Завантажити .xlsx файл
              </button>
            </div>
            <div className="p-10 flex flex-col items-center justify-center min-h-[500px]">
              <div className="w-20 h-20 mb-4 bg-gray-50 rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-gray-400 font-light italic">Дані відсутні</p>
            </div>
          </div>

          {/* Right Table Container */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
            <div className="p-6 border-b border-gray-50 flex justify-between items-center bg-white/50">
              <h3 className="text-lg font-bold text-[#2F4F4F]">Реєстр 2</h3>
              <button className="text-sm px-4 py-2 rounded-lg bg-[#556B2F]/10 text-[#556B2F] hover:bg-[#556B2F] hover:text-white transition-all font-medium">
                Завантажити .xlsx файл
              </button>
            </div>
            <div className="p-10 flex flex-col items-center justify-center min-h-[400px]">
              <div className="w-20 h-20 mb-4 bg-gray-50 rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-gray-400 font-light italic">Дані відсутні</p>
            </div>
          </div>

        </div>

        {/* Action Button */}
        <div className="w-full max-w-[95%] flex justify-end">
          <button className="px-12 py-4 rounded-full bg-[#556B2F] text-white font-bold text-lg hover:bg-[#4a5d28] shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 transform">
            Аналізувати
          </button>
        </div>
      </main>

      {/* Footer mimic existing style */}
      <footer className="w-full py-6 bg-[#E9ECEF] text-center mt-auto">
        <p className="text-[#6c757d] text-sm font-medium">
          Команда: <span className="font-bold text-[#495057]">vibekodery228</span>
        </p>
      </footer>
    </div>
  );
}
