import { Link, useNavigate } from 'react-router-dom';

export default function Landing() {
  const navigate = useNavigate();

  const handleStart = () => {
    if (localStorage.getItem('token')) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#F8F9FA] text-[#2F4F4F]">
      {/* Navbar */}
      <nav className="w-full py-6 px-10 flex justify-between items-center bg-white shadow-sm">
        <div className="text-xl md:text-2xl font-bold text-[#556B2F] tracking-tight">
          Автоматизація обліку активів в ОТГ
        </div>
        <div className="flex gap-3 md:gap-4">
          <Link 
            to="/login"
            className="px-5 py-2.5 md:px-7 rounded-full font-medium text-[#2F4F4F] hover:bg-gray-100 transition-colors duration-200"
          >
            Увійти
          </Link>
          <Link 
            to="/register"
            className="px-5 py-2.5 md:px-7 rounded-full font-medium bg-[#556B2F] text-white hover:bg-[#6B8E23] shadow-md hover:shadow-lg transition-all duration-200"
          >
            Зареєструватись
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex items-center justify-center p-6 md:p-12">
        <div className="max-w-5xl w-full bg-white rounded-3xl shadow-md p-10 md:p-20 text-center border border-gray-50 flex flex-col items-center justify-center">
          <h1 className="text-3xl md:text-5xl lg:text-6xl font-extrabold text-[#2F4F4F] leading-tight mb-6 md:mb-8 tracking-tight">
            Прозорість та ефективність <br className="hidden md:block" />
            <span className="text-[#556B2F]">управління громадою</span>
          </h1>
          <p className="text-base md:text-xl text-gray-500 max-w-3xl mx-auto mb-10 md:mb-14 leading-relaxed font-light">
            Автоматичне виявлення розбіжностей у реєстрах нерухомості та землі.
          </p>
          <button 
            onClick={handleStart}
            className="px-10 py-4 md:px-12 md:py-5 rounded-full text-lg font-semibold bg-[#2F4F4F] text-white hover:bg-[#1f3535] shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
            Розпочати
          </button>
        </div>
      </main>
    </div>
  );
}


