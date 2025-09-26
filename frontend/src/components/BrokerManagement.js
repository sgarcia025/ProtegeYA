import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BrokerManagement = () => {
  const [brokers, setBrokers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedBroker, setSelectedBroker] = useState(null);
  const [newBroker, setNewBroker] = useState({
    name: "",
    email: "",
    phone_number: "",
    whatsapp_number: "",
    corretaje_name: "",
    broker_credential: "",
    monthly_lead_quota: 50,
    commission_percentage: 10.0,
    subscription_status: "Active"
  });
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [photoPreview, setPhotoPreview] = useState(null);
  const { isAdmin } = useAuth();

  useEffect(() => {
    if (isAdmin) {
      fetchBrokers();
    }
  }, [isAdmin]);

  const fetchBrokers = async () => {
    try {
      const response = await axios.get(`${API}/brokers`);
      setBrokers(response.data);
    } catch (error) {
      console.error("Error fetching brokers:", error);
    } finally {
      setLoading(false);
    }
  };

  const createBroker = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/brokers`, {
        ...newBroker,
        user_id: `broker_${Date.now()}` // Temporal ID
      });
      
      setNewBroker({
        name: "",
        email: "",
        phone_number: "",
        whatsapp_number: "",
        corretaje_name: "",
        broker_credential: "",
        monthly_lead_quota: 50,
        commission_percentage: 10.0,
        subscription_status: "Active"
      });
      setPhotoPreview(null);
      setShowCreateModal(false);
      fetchBrokers();
      alert("Corredor creado exitosamente");
    } catch (error) {
      console.error("Error creating broker:", error);
      alert("Error al crear corredor");
    }
  };

  const handleEditBroker = (broker) => {
    setSelectedBroker(broker);
    setShowEditModal(true);
  };

  const updateBroker = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/brokers/${selectedBroker.id}`, selectedBroker);
      setShowEditModal(false);
      fetchBrokers();
      alert("Corredor actualizado exitosamente");
    } catch (error) {
      console.error("Error updating broker:", error);
      alert("Error al actualizar corredor");
    }
  };

  const toggleBrokerStatus = async (brokerId, currentStatus) => {
    const newStatus = currentStatus === "Active" ? "Inactive" : "Active";
    try {
      await axios.put(`${API}/brokers/${brokerId}/subscription`, null, {
        params: { status: newStatus }
      });
      fetchBrokers();
    } catch (error) {
      console.error("Error updating broker status:", error);
      alert("Error al actualizar estado del corredor");
    }
  };

  const deleteBroker = async (brokerId) => {
    if (window.confirm("¿Está seguro de eliminar este corredor? Esta acción no se puede deshacer.")) {
      try {
        await axios.delete(`${API}/brokers/${brokerId}`);
        fetchBrokers();
        alert("Corredor eliminado exitosamente");
      } catch (error) {
        console.error("Error deleting broker:", error);
        alert("Error al eliminar corredor: " + (error.response?.data?.detail || "Error desconocido"));
      }
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      "Active": { color: "bg-emerald-100 text-emerald-800", label: "Activo" },
      "Inactive": { color: "bg-red-100 text-red-800", label: "Inactivo" },
      "PastDue": { color: "bg-orange-100 text-orange-800", label: "Vencido" },
      "Canceled": { color: "bg-gray-100 text-gray-800", label: "Cancelado" }
    };

    const config = statusConfig[status] || statusConfig["Inactive"];
    
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-GT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Acceso Denegado</h2>
          <p className="text-slate-600">Solo los administradores pueden acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <div className="mb-4">
              <a 
                href="/dashboard" 
                className="text-emerald-600 hover:text-emerald-800 inline-flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
                </svg>
                Volver al Dashboard
              </a>
            </div>
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Gestión de Corredores</h1>
            <p className="text-slate-600">Administra corredores, suscripciones y pagos</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            + Nuevo Corredor
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {brokers.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.196-2.121M17 20v-2a3 3 0 00-3-3H8a3 3 0 00-3 3v2m10-11a3 3 0 11-6 0 3 3 0 016 0zm-9 7h.01"></path>
              </svg>
              <h3 className="text-lg font-medium text-slate-800 mb-2">No hay corredores registrados</h3>
              <p className="text-slate-600">Crea el primer corredor para comenzar a asignar leads.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Corredor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Contacto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Quota Mensual
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Leads Actuales
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Ingresos
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {brokers.map((broker) => (
                    <tr key={broker.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-slate-800">{broker.name}</div>
                          <div className="text-sm text-slate-500">{broker.email}</div>
                          {broker.corretaje_name && (
                            <div className="text-xs text-slate-400">Corretaje: {broker.corretaje_name}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-slate-600">
                          <div>📞 {broker.phone_number}</div>
                          <div>📱 {broker.whatsapp_number}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(broker.subscription_status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {broker.monthly_lead_quota} leads
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {broker.current_month_leads} / {broker.monthly_lead_quota}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-slate-800">
                          Q{broker.total_revenue?.toLocaleString() || '0'}
                        </div>
                        <div className="text-xs text-slate-500">
                          {broker.total_closed_deals || 0} ventas
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleEditBroker(broker)}
                          className="text-emerald-600 hover:text-emerald-900"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => toggleBrokerStatus(broker.id, broker.subscription_status)}
                          className={`${
                            broker.subscription_status === "Active" 
                              ? "text-red-600 hover:text-red-900" 
                              : "text-emerald-600 hover:text-emerald-900"
                          }`}
                        >
                          {broker.subscription_status === "Active" ? "Desactivar" : "Activar"}
                        </button>
                        <button
                          onClick={() => deleteBroker(broker.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal para crear corredor */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-screen overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">Crear Nuevo Corredor</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <form onSubmit={createBroker} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Nombre Completo
                    </label>
                    <input
                      type="text"
                      value={newBroker.name}
                      onChange={(e) => setNewBroker({...newBroker, name: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Correo Electrónico
                    </label>
                    <input
                      type="email"
                      value={newBroker.email}
                      onChange={(e) => setNewBroker({...newBroker, email: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Nombre del Corretaje
                    </label>
                    <input
                      type="text"
                      value={newBroker.corretaje_name}
                      onChange={(e) => setNewBroker({...newBroker, corretaje_name: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      placeholder="Ej: Seguros García & Asociados"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Teléfono
                    </label>
                    <input
                      type="tel"
                      value={newBroker.phone_number}
                      onChange={(e) => setNewBroker({...newBroker, phone_number: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      WhatsApp
                    </label>
                    <input
                      type="tel"
                      value={newBroker.whatsapp_number}
                      onChange={(e) => setNewBroker({...newBroker, whatsapp_number: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Quota Mensual de Leads
                    </label>
                    <input
                      type="number"
                      value={newBroker.monthly_lead_quota}
                      onChange={(e) => setNewBroker({...newBroker, monthly_lead_quota: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      min="1"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Comisión (%)
                    </label>
                    <input
                      type="number"
                      value={newBroker.commission_percentage}
                      onChange={(e) => setNewBroker({...newBroker, commission_percentage: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      min="0"
                      max="100"
                      step="0.1"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Estado de Suscripción
                  </label>
                  <select
                    value={newBroker.subscription_status}
                    onChange={(e) => setNewBroker({...newBroker, subscription_status: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  >
                    <option value="Active">Activo</option>
                    <option value="Inactive">Inactivo</option>
                    <option value="PastDue">Vencido</option>
                    <option value="Canceled">Cancelado</option>
                  </select>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Crear Corredor
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal para editar corredor */}
        {showEditModal && selectedBroker && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-screen overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">Editar Corredor</h3>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <form onSubmit={updateBroker} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Nombre Completo
                    </label>
                    <input
                      type="text"
                      value={selectedBroker.name}
                      onChange={(e) => setSelectedBroker({...selectedBroker, name: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Correo Electrónico
                    </label>
                    <input
                      type="email"
                      value={selectedBroker.email}
                      onChange={(e) => setSelectedBroker({...selectedBroker, email: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Teléfono
                    </label>
                    <input
                      type="tel"
                      value={selectedBroker.phone_number}
                      onChange={(e) => setSelectedBroker({...selectedBroker, phone_number: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      WhatsApp
                    </label>
                    <input
                      type="tel"
                      value={selectedBroker.whatsapp_number}
                      onChange={(e) => setSelectedBroker({...selectedBroker, whatsapp_number: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Quota Mensual de Leads
                    </label>
                    <input
                      type="number"
                      value={selectedBroker.monthly_lead_quota}
                      onChange={(e) => setSelectedBroker({...selectedBroker, monthly_lead_quota: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      min="1"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Comisión (%)
                    </label>
                    <input
                      type="number"
                      value={selectedBroker.commission_percentage}
                      onChange={(e) => setSelectedBroker({...selectedBroker, commission_percentage: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      min="0"
                      max="100"
                      step="0.1"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Estado de Suscripción
                  </label>
                  <select
                    value={selectedBroker.subscription_status}
                    onChange={(e) => setSelectedBroker({...selectedBroker, subscription_status: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  >
                    <option value="Active">Activo</option>
                    <option value="Inactive">Inactivo</option>
                    <option value="PastDue">Vencido</option>
                    <option value="Canceled">Cancelado</option>
                  </select>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Actualizar Corredor
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrokerManagement;