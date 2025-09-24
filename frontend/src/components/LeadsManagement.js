import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LeadsManagement = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateData, setUpdateData] = useState({
    broker_status: "",
    notes: "",
    closed_amount: ""
  });
  const { user, isBroker, isAdmin } = useAuth();

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

  const handleUpdateLead = (lead) => {
    setSelectedLead(lead);
    setUpdateData({
      broker_status: lead.broker_status || "New",
      notes: lead.broker_notes || "",
      closed_amount: lead.closed_amount || ""
    });
    setShowUpdateModal(true);
  };

  const submitUpdate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/leads/${selectedLead.id}/status`, {
        lead_id: selectedLead.id,
        broker_status: updateData.broker_status,
        notes: updateData.notes || null,
        closed_amount: updateData.closed_amount ? parseFloat(updateData.closed_amount) : null
      });

      setShowUpdateModal(false);
      fetchLeads(); // Reload leads
      
      // Show success message
      alert("Lead actualizado exitosamente");
    } catch (error) {
      console.error("Error updating lead:", error);
      alert("Error al actualizar lead");
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      "New": { color: "bg-gray-100 text-gray-800", label: "Nuevo" },
      "Contacted": { color: "bg-blue-100 text-blue-800", label: "Contactado" },
      "Interested": { color: "bg-yellow-100 text-yellow-800", label: "Interesado" },
      "Negotiation": { color: "bg-orange-100 text-orange-800", label: "Negociación" },
      "NotInterested": { color: "bg-red-100 text-red-800", label: "No Interesado" },
      "ClosedWon": { color: "bg-emerald-100 text-emerald-800", label: "Cerrado Ganado" },
      "ClosedLost": { color: "bg-red-100 text-red-800", label: "Cerrado Perdido" }
    };

    const config = statusConfig[status] || statusConfig["New"];
    
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
        <div className="mb-8">
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
          <h1 className="text-4xl font-bold text-slate-800 mb-2">
            {isBroker ? "Mis Leads Asignados" : "Gestión de Leads"}
          </h1>
          <p className="text-slate-600">
            {isBroker 
              ? "Actualiza el estado de tus leads y gestiona las oportunidades de venta"
              : "Visualiza y gestiona todos los leads del sistema"
            }
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {leads.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <h3 className="text-lg font-medium text-slate-800 mb-2">
                {isBroker ? "No tienes leads asignados" : "No hay leads en el sistema"}
              </h3>
              <p className="text-slate-600">
                {isBroker 
                  ? "Los leads aparecerán aquí cuando se te asignen nuevas oportunidades."
                  : "Los leads aparecerán aquí cuando los usuarios soliciten cotizaciones."
                }
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Lead ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Usuario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Estado Sistema
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Estado Broker
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Monto Cerrado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Creado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {leads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-800">
                        {lead.id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {lead.user_id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          lead.status === 'AssignedToBroker' 
                            ? 'bg-emerald-100 text-emerald-800'
                            : lead.status === 'QuotedNoPreference'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {lead.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(lead.broker_status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {lead.closed_amount ? `Q${lead.closed_amount.toLocaleString()}` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {formatDate(lead.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {(isBroker || isAdmin) && (
                          <button
                            onClick={() => handleUpdateLead(lead)}
                            className="text-emerald-600 hover:text-emerald-900 mr-4"
                          >
                            Actualizar
                          </button>
                        )}
                        <button className="text-blue-600 hover:text-blue-900">
                          Ver Detalles
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal para actualizar lead */}
        {showUpdateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Actualizar Lead</h3>
                <button
                  onClick={() => setShowUpdateModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <form onSubmit={submitUpdate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Estado del Lead
                  </label>
                  <select
                    value={updateData.broker_status}
                    onChange={(e) => setUpdateData({...updateData, broker_status: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                  >
                    <option value="New">Nuevo</option>
                    <option value="Contacted">Contactado</option>
                    <option value="Interested">Interesado</option>
                    <option value="Negotiation">En Negociación</option>
                    <option value="NotInterested">No Interesado</option>
                    <option value="ClosedWon">Cerrado Ganado</option>
                    <option value="ClosedLost">Cerrado Perdido</option>
                  </select>
                </div>

                {(updateData.broker_status === "ClosedWon") && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Monto de la Venta (GTQ)
                    </label>
                    <input
                      type="number"
                      value={updateData.closed_amount}
                      onChange={(e) => setUpdateData({...updateData, closed_amount: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      placeholder="Ej: 12000"
                      min="0"
                      step="0.01"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Notas
                  </label>
                  <textarea
                    value={updateData.notes}
                    onChange={(e) => setUpdateData({...updateData, notes: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    rows={3}
                    placeholder="Agregar notas sobre el seguimiento del lead..."
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Actualizar Lead
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowUpdateModal(false)}
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

export default LeadsManagement;