import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Register() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (password !== confirmPassword) {
      setError('Паролі не співпадають');
      return;
    }
    
    setLoading(true);

    try {
      const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        throw new Error('Помилка реєстрації. Можливо, такий користувач вже існує.');
      }

      navigate('/login');
    } catch (err: any) {
      setError(err.message || 'Сталася помилка');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen overflow-hidden flex items-center justify-center bg-gray-50 font-sans px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg shadow-black/5 p-8 border border-gray-100">
        <h2 className="text-3xl font-bold text-center text-[#2F4F4F] mb-8">
          Реєстрація
        </h2>
        
        <form className="space-y-5" onSubmit={handleSubmit}>
          {error && <div className="text-red-500 text-sm text-center bg-red-50 p-2 rounded-lg">{error}</div>}

          {/* Name Input */}
          <div>
            <label 
              htmlFor="name" 
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Ім'я та прізвище
            </label>
            <input 
              type="text" 
              id="name" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-all"
              placeholder="Олександр Коваленко"
              required
            />
          </div>

          {/* Email Input */}
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
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-all"
              placeholder="name@example.com"
              required
            />
          </div>

          {/* Password Input */}
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
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          {/* Confirm Password Input */}
          <div>
            <label 
              htmlFor="confirm-password" 
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Підтвердження пароля
            </label>
            <input 
              type="password" 
              id="confirm-password" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#556B2F]/50 focus:border-[#556B2F] transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-4 rounded-xl bg-[#556B2F] text-white font-semibold hover:bg-[#4a5f29] shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 mt-2 disabled:opacity-70"
          >
            {loading ? "Зачекайте..." : "Зареєструватися"}
          </button>

          {/* Navigation Link */}
          <p className="text-center text-sm text-gray-500 mt-6">
            Вже є акаунт?{' '}
            <Link 
              to="/login" 
              className="font-medium text-[#556B2F] hover:text-[#4a5f29] transition-colors"
            >
              Увійти
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
