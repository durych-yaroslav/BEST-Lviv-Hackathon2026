import { Link } from 'react-router-dom';

export default function Login() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#F8F9FA] font-sans px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg shadow-black/5 p-8 border border-gray-100">
        <h2 className="text-3xl font-bold text-center text-[#2F4F4F] mb-8">
          Вхід
        </h2>
        
        <form className="space-y-6">
          <div>
            <label 
              htmlFor="email" 
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Електронна пошта
            </label>
            <input 
              type="email" 
              id="email" 
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-colors"
              placeholder="name@example.com"
            />
          </div>

          <div>
            <label 
              htmlFor="password" 
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Пароль
            </label>
            <input 
              type="password" 
              id="password" 
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-colors"
              placeholder="••••••••"
            />
            <div className="mt-2 text-right">
              <a 
                href="#" 
                className="text-sm font-light text-gray-400 hover:text-gray-600 transition-colors"
              >
                Забули пароль?
              </a>
            </div>
          </div>

          <button 
            type="submit" 
            className="w-full py-3.5 rounded-xl bg-[#556B2F] text-white font-medium hover:bg-[#4a5d28] hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
          >
            Увійти
          </button>

          <p className="text-center text-sm text-gray-500 mt-6">
            Немає акаунту?{' '}
            <Link 
              to="/register" 
              className="font-medium text-[#556B2F] hover:text-[#4a5d28] transition-colors"
            >
              Зареєструватися
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
