// src/pages/Login.jsx
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuth } from '../hooks/useAuth.jsx';
import { useNavigate, Navigate } from 'react-router-dom';
import { useState } from 'react';

const schema = yup.object({
  email: yup.string().email('Email no válido').required('Obligatorio'),
  password: yup.string().min(6, 'Mínimo 6 caracteres').required('Obligatorio'),
}).required();

export default function Login() {
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: yupResolver(schema) });
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [formError, setFormError] = useState('');

const onSubmit = async (data) => {
  setFormError('');
  try {
    await login(data.email, data.password);
    navigate('/mis-pedidos');
  } catch (err) {
    setFormError(err.message || 'Credenciales inválidas.');
  }
};

  if (isAuthenticated) {
    return <Navigate to="/mis-pedidos" replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-white p-8 rounded-2xl shadow-md w-full max-w-sm space-y-4"
      >
        <h1 className="text-2xl font-bold text-center">Iniciar sesión</h1>
        {formError && (
          <div className="text-red-500 text-center mb-2">{formError}</div>
        )}
        <div>
          <label className="block font-medium mb-1">Email</label>
          <input type="email" {...register('email')} className="w-full border rounded p-2" />
          <p className="text-red-500 text-sm">{errors.email?.message}</p>
        </div>
        <div>
          <label className="block font-medium mb-1">Contraseña</label>
          <input type="password" {...register('password')} className="w-full border rounded p-2" />
          <p className="text-red-500 text-sm">{errors.password?.message}</p>
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded-xl shadow hover:bg-blue-700 transition"
        >
          Entrar
        </button>
      </form>
    </div>
  );
}
