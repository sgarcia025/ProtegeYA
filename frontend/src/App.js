import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import "./App.css";
import LeadsManagement from "./components/LeadsManagement";
import BrokerManagement from "./components/BrokerManagement";
import SystemConfiguration from "./components/SystemConfiguration";
import UserManagement from "./components/UserManagement";
import SubscriptionPlans from "./components/SubscriptionPlans";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error("Error fetching profile:", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || "Error de login" 
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isBroker: user?.role === 'broker'
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

// Login Component
const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await login(email, password);
    
    if (result.success) {
      navigate("/dashboard", { replace: true });
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-20 w-auto flex items-center justify-center">
            <h1 className="text-4xl font-bold text-slate-800">ProtegeYA</h1>
            <div className="ml-2 bg-emerald-500 text-white px-3 py-1 rounded-xl text-sm font-semibold">
              YA
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-slate-800">
            Iniciar Sesión
          </h2>
          <p className="mt-2 text-center text-sm text-slate-600">
            Accede a tu cuenta de ProtegeYa
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-slate-300 placeholder-slate-500 text-slate-900 rounded-t-md focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 focus:z-10 sm:text-sm"
                placeholder="Correo electrónico"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Contraseña
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-slate-300 placeholder-slate-500 text-slate-900 rounded-b-md focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 focus:z-10 sm:text-sm"
                placeholder="Contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50"
            >
              {loading ? "Iniciando sesión..." : "Iniciar Sesión"}
            </button>
          </div>

          <div className="text-center">
            <p className="text-xs text-slate-500">
              Credenciales de prueba:<br/>
              <strong>admin@protegeya.com</strong> / <strong>admin123</strong>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();
  
  return (
    <nav className="bg-white shadow-lg border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-2xl font-bold text-slate-800">ProtegeYA</h1>
              <div className="ml-2 bg-emerald-500 text-white px-2 py-1 rounded-lg text-xs font-semibold">
                YA
              </div>
            </div>
            <div className="ml-10 flex items-baseline space-x-4">
              <a
                href="/dashboard"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === "/dashboard"
                    ? "bg-emerald-100 text-emerald-700"
                    : "text-slate-600 hover:text-emerald-600"
                }`}
              >
                Dashboard
              </a>
              {isAdmin && (
                <>
                  <a
                    href="/admin/users"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      location.pathname.includes("/admin")
                        ? "bg-emerald-100 text-emerald-700"
                        : "text-slate-600 hover:text-emerald-600"
                    }`}
                  >
                    Usuarios
                  </a>
                  <a
                    href="/admin/insurers"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      location.pathname.includes("/admin")
                        ? "bg-emerald-100 text-emerald-700"
                        : "text-slate-600 hover:text-emerald-600"
                    }`}
                  >
                    Aseguradoras
                  </a>
                  <a
                    href="/admin/plans" 
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      location.pathname.includes("/admin")
                        ? "bg-emerald-100 text-emerald-700"
                        : "text-slate-600 hover:text-emerald-600"
                    }`}
                  >
                    Planes
                  </a>
                  <a
                    href="/admin/brokers"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      location.pathname.includes("/brokers")
                        ? "bg-emerald-100 text-emerald-700"
                        : "text-slate-600 hover:text-emerald-600"
                    }`}
                  >
                    Corredores
                  </a>
                  <a
                    href="/admin/configuration"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      location.pathname.includes("/configuration")
                        ? "bg-emerald-100 text-emerald-700"
                        : "text-slate-600 hover:text-emerald-600"
                    }`}
                  >
                    Configuración
                  </a>
                </>
              )}
              <a
                href="/leads"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === "/leads"
                    ? "bg-emerald-100 text-emerald-700"
                    : "text-slate-600 hover:text-emerald-600"
                }`}
              >
                Leads
              </a>
              <a
                href="/test-quote"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === "/test-quote"
                    ? "bg-emerald-100 text-emerald-700"
                    : "text-slate-600 hover:text-emerald-600"
                }`}
              >
                Test Cotización
              </a>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-600">
              {user?.name} ({user?.role})
            </span>
            <button
              onClick={logout}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Dashboard principal
const Dashboard = () => {
  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user, isAdmin, isBroker } = useAuth();

  useEffect(() => {
    fetchKPIData();
  }, []);

  const fetchKPIData = async () => {
    try {
      const response = await axios.get(`${API}/reports/kpi`);
      setKpiData(response.data);
    } catch (error) {
      console.error("Error fetching KPI data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50">
      <Navigation />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">
            {isBroker ? `¡Hola ${user?.name}!` : "Dashboard ProtegeYa"}
          </h1>
          <p className="text-slate-600">
            {isBroker 
              ? "Gestiona tus leads asignados y cierra más ventas" 
              : "Comparador de seguros y generador de leads - Guatemala"
            }
          </p>
        </div>

        {/* KPI Cards */}
        {isBroker ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Leads Asignados</p>
                  <p className="text-3xl font-bold text-slate-800">{kpiData?.total_assigned_leads || 0}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-full">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.196-2.121M17 20v-2a3 3 0 00-3-3H8a3 3 0 00-3 3v2m10-11a3 3 0 11-6 0 3 3 0 016 0zm-9 7h.01"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-emerald-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Ventas Cerradas</p>
                  <p className="text-3xl font-bold text-slate-800">{kpiData?.closed_won_deals || 0}</p>
                </div>
                <div className="p-3 bg-emerald-100 rounded-full">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Ingresos Totales</p>
                  <p className="text-3xl font-bold text-slate-800">Q{(kpiData?.total_revenue || 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-full">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Tasa Conversión</p>
                  <p className="text-3xl font-bold text-slate-800">{kpiData?.conversion_rate || 0}%</p>
                </div>
                <div className="p-3 bg-orange-100 rounded-full">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Total Leads</p>
                  <p className="text-3xl font-bold text-slate-800">{kpiData?.total_leads || 0}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-full">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.196-2.121M17 20v-2a3 3 0 00-3-3H8a3 3 0 00-3 3v2m10-11a3 3 0 11-6 0 3 3 0 016 0zm-9 7h.01"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-emerald-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Leads Asignados</p>
                  <p className="text-3xl font-bold text-slate-800">{kpiData?.assigned_leads || 0}</p>
                </div>
                <div className="p-3 bg-emerald-100 rounded-full">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Corredores Activos</p>
                  <p className="text-3xl font-bold text-slate-800">{kpiData?.active_brokers || 0}</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-full">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m8 6V9a2 2 0 00-2-2H6a2 2 0 00-2 2v3.5"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm mb-1">Ingresos Totales</p>
                  <p className="text-3xl font-bold text-slate-800">Q{(kpiData?.total_revenue || 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-orange-100 rounded-full">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Disclaimer Legal */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-8">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-amber-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
            </svg>
            <div>
              <h3 className="text-amber-800 font-semibold text-sm mb-1">Aviso Legal</h3>
              <p className="text-amber-700 text-sm">
                ProtegeYa es un comparador y generador de leads. No es aseguradora ni corredor. 
                Precios indicativos a confirmar con un corredor autorizado.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <a href="/leads" className="group">
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 transform group-hover:-translate-y-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-slate-800">
                  {isBroker ? "Mis Leads" : "Gestionar Leads"}
                </h3>
                <div className="p-2 bg-emerald-100 rounded-lg group-hover:bg-emerald-200 transition-colors">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                  </svg>
                </div>
              </div>
              <p className="text-slate-600 text-sm">
                {isBroker 
                  ? "Ver y actualizar tus leads asignados" 
                  : "Ver todos los leads y su estado actual"
                }
              </p>
            </div>
          </a>

          {isAdmin && (
            <a href="/admin/insurers" className="group">
              <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 transform group-hover:-translate-y-1">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-slate-800">Administración</h3>
                  <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                  </div>
                </div>
                <p className="text-slate-600 text-sm">Gestionar aseguradoras y productos</p>
              </div>
            </a>
          )}

          <a href="/test-quote" className="group">
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 transform group-hover:-translate-y-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-slate-800">Test Cotización</h3>
                <div className="p-2 bg-yellow-100 rounded-lg group-hover:bg-yellow-200 transition-colors">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                </div>
              </div>
              <p className="text-slate-600 text-sm">Probar el motor de cotización</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
};

// Test de Cotización Component (reusing from previous implementation)
const TestQuote = () => {
  const [quoteData, setQuoteData] = useState({
    make: "",
    model: "",
    year: new Date().getFullYear(),
    value: "",
    municipality: ""
  });
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/quotes/simulate`, {
        ...quoteData,
        value: parseFloat(quoteData.value)
      });
      setQuotes(response.data.quotes);
    } catch (error) {
      console.error("Error getting quotes:", error);
      alert("Error al obtener cotizaciones");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50">
      <Navigation />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Test de Cotización</h1>
          <p className="text-slate-600">Probar el motor de cotización de seguros</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Formulario */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-slate-800 mb-6">Datos del Vehículo</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Marca</label>
                <input
                  type="text"
                  value={quoteData.make}
                  onChange={(e) => setQuoteData({...quoteData, make: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Ej: Toyota"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Modelo</label>
                <input
                  type="text"
                  value={quoteData.model}
                  onChange={(e) => setQuoteData({...quoteData, model: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Ej: Corolla"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Año</label>
                <input
                  type="number"
                  value={quoteData.year}
                  onChange={(e) => setQuoteData({...quoteData, year: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  min="1990"
                  max={new Date().getFullYear() + 1}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Valor (GTQ)</label>
                <input
                  type="number"
                  value={quoteData.value}
                  onChange={(e) => setQuoteData({...quoteData, value: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Ej: 120000"
                  min="1000"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Municipio (opcional)</label>
                <input
                  type="text"
                  value={quoteData.municipality}
                  onChange={(e) => setQuoteData({...quoteData, municipality: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Ej: Guatemala"
                />
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white py-3 px-4 rounded-lg font-semibold transition-colors"
              >
                {loading ? "Cotizando..." : "Obtener Cotizaciones"}
              </button>
            </form>
          </div>

          {/* Resultados */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-slate-800 mb-6">Cotizaciones</h2>
            
            {quotes.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <h3 className="text-lg font-medium text-slate-800 mb-2">Sin cotizaciones</h3>
                <p className="text-slate-600">Complete el formulario para ver las cotizaciones disponibles.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {quotes.map((quote, index) => (
                  <div key={index} className="border border-slate-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-lg text-slate-800">{quote.insurer_name}</h3>
                        <p className="text-slate-600">{quote.product_name}</p>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs mt-1 ${
                          quote.insurance_type === 'FullCoverage' 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-orange-100 text-orange-800'
                        }`}>
                          {quote.insurance_type === 'FullCoverage' ? 'Cobertura Completa' : 'Responsabilidad Civil'}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-emerald-600">Q{quote.monthly_premium.toLocaleString()}</p>
                        <p className="text-sm text-slate-500">/ mes</p>
                      </div>
                    </div>
                    
                    {Object.keys(quote.coverage).length > 0 && (
                      <div>
                        <h4 className="font-medium text-slate-800 mb-2">Coberturas:</h4>
                        <div className="grid grid-cols-1 gap-1">
                          {Object.entries(quote.coverage).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-sm">
                              <span className="text-slate-600">{key}:</span>
                              <span className="font-medium">{value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-sm text-amber-800">
                    <strong>Aviso legal:</strong> ProtegeYa es un comparador y generador de leads. 
                    No es aseguradora ni corredor. Precios indicativos a confirmar con un corredor autorizado.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/leads" 
              element={
                <ProtectedRoute>
                  <LeadsManagement />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/users" 
              element={
                <ProtectedRoute adminOnly>
                  <UserManagement />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/plans" 
              element={
                <ProtectedRoute adminOnly>
                  <SubscriptionPlans />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/insurers" 
              element={
                <ProtectedRoute adminOnly>
                  <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                      <h1 className="text-2xl font-bold text-slate-800 mb-4">Gestión de Aseguradoras</h1>
                      <p className="text-slate-600">Módulo en desarrollo - Gestionar aseguradoras y productos.</p>
                    </div>
                  </div>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/test-quote" 
              element={
                <ProtectedRoute>
                  <TestQuote />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/configuration" 
              element={
                <ProtectedRoute adminOnly>
                  <SystemConfiguration />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/*" 
              element={
                <ProtectedRoute adminOnly>
                  <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                      <h1 className="text-2xl font-bold text-slate-800 mb-4">Módulo en Desarrollo</h1>
                      <p className="text-slate-600">Esta sección estará disponible próximamente.</p>
                    </div>
                  </div>
                </ProtectedRoute>
              } 
            />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;