import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard principal
const Dashboard = () => {
  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(true);

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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">ProtegeYa</h1>
          <p className="text-gray-600">Comparador de seguros y generador de leads - Guatemala</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">Total Leads</p>
                <p className="text-3xl font-bold text-gray-900">{kpiData?.total_leads || 0}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.196-2.121M17 20v-2a3 3 0 00-3-3H8a3 3 0 00-3 3v2m10-11a3 3 0 11-6 0 3 3 0 016 0zm-9 7h.01"></path>
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">Leads Asignados</p>
                <p className="text-3xl font-bold text-gray-900">{kpiData?.assigned_leads || 0}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">Corredores Activos</p>
                <p className="text-3xl font-bold text-gray-900">{kpiData?.active_brokers || 0}</p>
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
                <p className="text-gray-600 text-sm mb-1">Tasa de Asignación</p>
                <p className="text-3xl font-bold text-gray-900">{kpiData?.assignment_rate || 0}%</p>
              </div>
              <div className="p-3 bg-orange-100 rounded-full">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>

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
          <Link to="/admin" className="group">
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 transform group-hover:-translate-y-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-900">Panel Admin</h3>
                <div className="p-2 bg-indigo-100 rounded-lg group-hover:bg-indigo-200 transition-colors">
                  <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                </div>
              </div>
              <p className="text-gray-600 text-sm">Gestionar aseguradoras, productos y configuraciones</p>
            </div>
          </Link>

          <Link to="/broker" className="group">
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 transform group-hover:-translate-y-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-900">CRM Corredor</h3>
                <div className="p-2 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                  </svg>
                </div>
              </div>
              <p className="text-gray-600 text-sm">Gestionar leads asignados y seguimiento</p>
            </div>
          </Link>

          <Link to="/test-quote" className="group">
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 transform group-hover:-translate-y-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-900">Test Cotización</h3>
                <div className="p-2 bg-yellow-100 rounded-lg group-hover:bg-yellow-200 transition-colors">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                </div>
              </div>
              <p className="text-gray-600 text-sm">Probar el motor de cotización</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

// Panel Admin
const AdminPanel = () => {
  const [insurers, setInsurers] = useState([]);
  const [products, setProducts] = useState([]);
  const [newInsurer, setNewInsurer] = useState({ name: "", logo_url: "" });
  const [newProduct, setNewProduct] = useState({ 
    insurer_id: "", 
    name: "", 
    insurance_type: "FullCoverage" 
  });
  const [showInsurerForm, setShowInsurerForm] = useState(false);
  const [showProductForm, setShowProductForm] = useState(false);

  useEffect(() => {
    fetchInsurers();
    fetchProducts();
  }, []);

  const fetchInsurers = async () => {
    try {
      const response = await axios.get(`${API}/admin/insurers`);
      setInsurers(response.data);
    } catch (error) {
      console.error("Error fetching insurers:", error);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/admin/products`);
      setProducts(response.data);
    } catch (error) {
      console.error("Error fetching products:", error);
    }
  };

  const createInsurer = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/insurers`, newInsurer);
      setNewInsurer({ name: "", logo_url: "" });
      setShowInsurerForm(false);
      fetchInsurers();
    } catch (error) {
      console.error("Error creating insurer:", error);
    }
  };

  const createProduct = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/products`, newProduct);
      setNewProduct({ insurer_id: "", name: "", insurance_type: "FullCoverage" });
      setShowProductForm(false);
      fetchProducts();
    } catch (error) {
      console.error("Error creating product:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <Link to="/" className="text-indigo-600 hover:text-indigo-800 mb-4 inline-flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            Volver al dashboard
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Panel Administrativo</h1>
          <p className="text-gray-600">Gestionar aseguradoras y productos</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Aseguradoras */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Aseguradoras</h2>
              <button
                onClick={() => setShowInsurerForm(!showInsurerForm)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                + Nueva Aseguradora
              </button>
            </div>

            {showInsurerForm && (
              <form onSubmit={createInsurer} className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                    <input
                      type="text"
                      value={newInsurer.name}
                      onChange={(e) => setNewInsurer({...newInsurer, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">URL del Logo</label>
                    <input
                      type="url"
                      value={newInsurer.logo_url}
                      onChange={(e) => setNewInsurer({...newInsurer, logo_url: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      Crear
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowInsurerForm(false)}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </form>
            )}

            <div className="space-y-3">
              {insurers.map((insurer) => (
                <div key={insurer.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    {insurer.logo_url && (
                      <img src={insurer.logo_url} alt={insurer.name} className="w-8 h-8 rounded mr-3" />
                    )}
                    <span className="font-medium">{insurer.name}</span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    insurer.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {insurer.active ? 'Activa' : 'Inactiva'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Productos */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Productos</h2>
              <button
                onClick={() => setShowProductForm(!showProductForm)}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                + Nuevo Producto
              </button>
            </div>

            {showProductForm && (
              <form onSubmit={createProduct} className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Aseguradora</label>
                    <select
                      value={newProduct.insurer_id}
                      onChange={(e) => setNewProduct({...newProduct, insurer_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      required
                    >
                      <option value="">Seleccionar aseguradora</option>
                      {insurers.map((insurer) => (
                        <option key={insurer.id} value={insurer.id}>{insurer.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nombre del Producto</label>
                    <input
                      type="text"
                      value={newProduct.name}
                      onChange={(e) => setNewProduct({...newProduct, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Seguro</label>
                    <select
                      value={newProduct.insurance_type}
                      onChange={(e) => setNewProduct({...newProduct, insurance_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    >
                      <option value="FullCoverage">Cobertura Completa</option>
                      <option value="ThirdParty">Responsabilidad Civil</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      Crear
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowProductForm(false)}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </form>
            )}

            <div className="space-y-3">
              {products.map((product) => {
                const insurer = insurers.find(i => i.id === product.insurer_id);
                return (
                  <div key={product.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{product.name}</h4>
                        <p className="text-sm text-gray-600">{insurer?.name}</p>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs mt-1 ${
                          product.insurance_type === 'FullCoverage' 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-orange-100 text-orange-800'
                        }`}>
                          {product.insurance_type === 'FullCoverage' ? 'Completa' : 'RC'}
                        </span>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        product.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {product.active ? 'Activo' : 'Inactivo'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// CRM Corredor (básico)
const BrokerCRM = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const response = await axios.get(`${API}/leads`);
      setLeads(response.data);
    } catch (error) {
      console.error("Error fetching leads:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <Link to="/" className="text-green-600 hover:text-green-800 mb-4 inline-flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            Volver al dashboard
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">CRM Corredor</h1>
          <p className="text-gray-600">Gestión de leads asignados</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Leads Asignados</h2>
          
          {leads.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No hay leads asignados</h3>
              <p className="text-gray-600">Los leads aparecerán aquí cuando sean asignados a corredores activos.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creado</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {lead.id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {lead.user_id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          lead.status === 'AssignedToBroker' 
                            ? 'bg-green-100 text-green-800'
                            : lead.status === 'QuotedNoPreference'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {lead.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(lead.created_at).toLocaleDateString('es-GT')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-green-600 hover:text-green-900">Ver detalles</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Test de Cotización
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
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 to-orange-100">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <Link to="/" className="text-orange-600 hover:text-orange-800 mb-4 inline-flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            Volver al dashboard
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Test de Cotización</h1>
          <p className="text-gray-600">Probar el motor de cotización de seguros</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Formulario */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Datos del Vehículo</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Marca</label>
                <input
                  type="text"
                  value={quoteData.make}
                  onChange={(e) => setQuoteData({...quoteData, make: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Ej: Toyota"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Modelo</label>
                <input
                  type="text"
                  value={quoteData.model}
                  onChange={(e) => setQuoteData({...quoteData, model: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Ej: Corolla"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Año</label>
                <input
                  type="number"
                  value={quoteData.year}
                  onChange={(e) => setQuoteData({...quoteData, year: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  min="1990"
                  max={new Date().getFullYear() + 1}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Valor (GTQ)</label>
                <input
                  type="number"
                  value={quoteData.value}
                  onChange={(e) => setQuoteData({...quoteData, value: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Ej: 120000"
                  min="1000"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Municipio (opcional)</label>
                <input
                  type="text"
                  value={quoteData.municipality}
                  onChange={(e) => setQuoteData({...quoteData, municipality: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Ej: Guatemala"
                />
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white py-3 px-4 rounded-lg font-semibold transition-colors"
              >
                {loading ? "Cotizando..." : "Obtener Cotizaciones"}
              </button>
            </form>
          </div>

          {/* Resultados */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Cotizaciones</h2>
            
            {quotes.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Sin cotizaciones</h3>
                <p className="text-gray-600">Complete el formulario para ver las cotizaciones disponibles.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {quotes.map((quote, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-lg">{quote.insurer_name}</h3>
                        <p className="text-gray-600">{quote.product_name}</p>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs mt-1 ${
                          quote.insurance_type === 'FullCoverage' 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-orange-100 text-orange-800'
                        }`}>
                          {quote.insurance_type === 'FullCoverage' ? 'Cobertura Completa' : 'Responsabilidad Civil'}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-green-600">Q{quote.monthly_premium.toLocaleString()}</p>
                        <p className="text-sm text-gray-500">/ mes</p>
                      </div>
                    </div>
                    
                    {Object.keys(quote.coverage).length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Coberturas:</h4>
                        <div className="grid grid-cols-1 gap-1">
                          {Object.entries(quote.coverage).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-sm">
                              <span className="text-gray-600">{key}:</span>
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

// Componente de Navegación
const Navigation = () => {
  const location = useLocation();
  
  return null; // No necesitamos navegación fija por ahora
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/broker" element={<BrokerCRM />} />
          <Route path="/test-quote" element={<TestQuote />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;