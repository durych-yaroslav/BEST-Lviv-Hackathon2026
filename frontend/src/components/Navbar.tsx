import { Link } from 'react-router-dom';

interface NavbarProps {
  username?: string;
}

export default function Navbar({ username = "Адміністратор" }: NavbarProps) {
  return (
    <nav className="w-full py-6 px-6 md:px-10 flex justify-between items-center bg-white shadow-sm font-sans">
      <div className="text-xl md:text-2xl font-bold text-[#556B2F] tracking-tight">
        <Link to="/">Автоматизація обліку активів в ОТГ</Link>
      </div>
      <div className="flex items-center gap-6">
        <span className="text-[#2F4F4F] font-medium hidden sm:block">
          {username}
        </span>
        <button 
          className="px-5 py-2 md:px-7 rounded-full font-medium border-2 border-[#556B2F] text-[#556B2F] hover:bg-[#556B2F] hover:text-white transition-all duration-200"
        >
          Вихід
        </button>
      </div>
    </nav>
  );
}
