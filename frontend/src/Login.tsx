import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Помилка авторизації. Перевірте дані.');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Сталася помилка');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#F8F9FA] font-sans px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg shadow-black/5 p-8 border border-gray-100">
        <h2 className="text-3xl font-bold text-center text-[#2F4F4F] mb-8">
          Вхід
        </h2>
        
        <form className="space-y-6" onSubmit={handleSubmit}>
          {error && <div className="text-red-500 text-sm text-center bg-red-50 p-2 rounded-lg">{error}</div>}
          
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-colors"
              placeholder="name@example.com"
              required
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
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-colors"
              placeholder="••••••••"
              required
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
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-[#556B2F] text-white font-medium hover:bg-[#4a5d28] hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-70"
          >
            {loading ? "Зачекайте..." : "Увійти"}
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
