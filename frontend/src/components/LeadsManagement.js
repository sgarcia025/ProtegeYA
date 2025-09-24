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
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [brokers, setBrokers] = useState([]);
  const [updateData, setUpdateData] = useState({
    broker_status: "",
    notes: "",
    closed_amount: ""
  });
  const [newLead, setNewLead] = useState({
    name: "",
    phone_number: "",
    vehicle_make: "",
    vehicle_model: "",
    vehicle_year: new Date().getFullYear(),
    vehicle_value: "",
    selected_insurer: "",
    selected_quote_price: "",
    status: "PendingData"
  });
  const [insurers, setInsurers] = useState([]);
  const [products, setProducts] = useState([]);
  const [assignmentType, setAssignmentType] = useState("manual"); // "manual" or "roundrobin"
  const [selectedBrokerId, setSelectedBrokerId] = useState("");
  const [quoteType, setQuoteType] = useState("existing"); // "existing" or "custom"
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showReassignModal, setShowReassignModal] = useState(false);
  const [selectedLeadForReassign, setSelectedLeadForReassign] = useState(null);
  const { user, isBroker, isAdmin } = useAuth();

  useEffect(() => {
    fetchLeads();
    if (isAdmin) {
      fetchBrokers();
      fetchInsurers();
      fetchProducts();
    }
  }, []);

  const fetchBrokers = async () => {
    try {
      const response = await axios.get(`${API}/brokers`);
      setBrokers(response.data);
    } catch (error) {
      console.error("Error fetching brokers:", error);
    }
  };

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

  const createLead = async (e) => {
    e.preventDefault();
    try {
      // Step 1: Create the lead
      const leadResponse = await axios.post(`${API}/admin/leads`, newLead);
      const createdLead = leadResponse.data;
      
      // Step 2: Handle assignment based on selected type
      if (assignmentType === "manual" && selectedBrokerId) {
        // Manual assignment to specific broker
        await axios.post(`${API}/admin/leads/${createdLead.id}/assign?broker_id=${selectedBrokerId}`, {}, {
          headers: { 'Content-Type': 'application/json' }
        });
      } else if (assignmentType === "roundrobin") {
        // Automatic round-robin assignment
        await axios.post(`${API}/admin/leads/${createdLead.id}/assign-auto`, {}, {
          headers: { 'Content-Type': 'application/json' }
        });
      }
      
      // Reset form
      setNewLead({
        name: "",
        phone_number: "",
        vehicle_make: "",
        vehicle_model: "",
        vehicle_year: new Date().getFullYear(),
        vehicle_value: "",
        selected_insurer: "",
        selected_quote_price: "",
        status: "PendingData"
      });
      setAssignmentType("manual");
      setSelectedBrokerId("");
      setQuoteType("existing");
      setShowCreateModal(false);
      fetchLeads(); // Reload leads
      
      alert("Lead creado y asignado exitosamente");
    } catch (error) {
      console.error("Error creating lead:", error);
      alert("Error al crear lead: " + (error.response?.data?.detail || "Error desconocido"));
    }
  };

  const handleAssignLead = (lead) => {
    setSelectedLead(lead);
    setShowAssignModal(true);
  };

  const assignLeadToBroker = async (brokerId) => {
    try {
      await axios.post(`${API}/admin/leads/${selectedLead.id}/assign?broker_id=${brokerId}`, {}, {
        headers: { 'Content-Type': 'application/json' }
      });
      
      setShowAssignModal(false);
      fetchLeads(); // Reload leads
      
      alert("Lead asignado exitosamente al corredor");
    } catch (error) {
      console.error("Error assigning lead:", error);
      alert("Error al asignar lead: " + (error.response?.data?.detail || "Error desconocido"));
    }
  };

  const handleViewDetails = (lead) => {
    setSelectedLead(lead);
    setShowDetailsModal(true);
  };

  const handleReassignLead = (lead) => {
    setSelectedLeadForReassign(lead);
    setShowReassignModal(true);
  };

  const reassignLeadToBroker = async (brokerId) => {
    try {
      await axios.post(`${API}/admin/leads/${selectedLeadForReassign.id}/assign?broker_id=${brokerId}`, {}, {
        headers: { 'Content-Type': 'application/json' }
      });
      
      setShowReassignModal(false);
      setSelectedLeadForReassign(null);
      fetchLeads(); // Reload leads
      
      alert("Lead re-asignado exitosamente al corredor");
    } catch (error) {
      console.error("Error reassigning lead:", error);
      alert("Error al re-asignar lead: " + (error.response?.data?.detail || "Error desconocido"));
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
          {isAdmin && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              + Crear Lead Manual
            </button>
          )}
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
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Vehículo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Corredor Asignado
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
                        <div>
                          <div className="font-medium">{lead.name || 'Sin nombre'}</div>
                          <div className="text-xs text-slate-500">{lead.phone_number}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        <div>
                          <div className="font-medium">{lead.vehicle_make} {lead.vehicle_model}</div>
                          <div className="text-xs text-slate-500">
                            {lead.vehicle_year} - {lead.vehicle_value ? `Q${lead.vehicle_value.toLocaleString()}` : 'Sin valor'}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {lead.assigned_broker_id ? (
                          <div>
                            <div className="font-medium text-emerald-600">
                              {brokers.find(b => b.id === lead.assigned_broker_id)?.name || 'Corredor desconocido'}
                            </div>
                            <div className="text-xs text-slate-500">
                              {brokers.find(b => b.id === lead.assigned_broker_id)?.corretaje_name || ''}
                            </div>
                          </div>
                        ) : (
                          <span className="text-slate-400">Sin asignar</span>
                        )}
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
                        {isAdmin && !lead.assigned_broker_id && (
                          <button
                            onClick={() => handleAssignLead(lead)}
                            className="text-orange-600 hover:text-orange-900 mr-4"
                          >
                            Asignar
                          </button>
                        )}
                        <button 
                          onClick={() => handleViewDetails(lead)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          Ver Detalles
                        </button>
                        {isAdmin && lead.assigned_broker_id && (
                          <button
                            onClick={() => handleReassignLead(lead)}
                            className="text-purple-600 hover:text-purple-900"
                          >
                            Re-asignar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal para crear lead manual */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Crear Lead Manual</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <form onSubmit={createLead} className="space-y-4">
                {/* Información Personal */}
                <div className="border-b pb-4">
                  <h4 className="text-md font-medium text-slate-700 mb-3">Información Personal</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Nombre Completo *
                      </label>
                      <input
                        type="text"
                        value={newLead.name}
                        onChange={(e) => setNewLead({...newLead, name: e.target.value})}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ej: Juan Carlos Pérez"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Teléfono *
                      </label>
                      <input
                        type="tel"
                        value={newLead.phone_number}
                        onChange={(e) => setNewLead({...newLead, phone_number: e.target.value})}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ej: +502-1234-5678"
                        required
                      />
                    </div>
                  </div>
                </div>

                {/* Información del Vehículo */}
                <div className="border-b pb-4">
                  <h4 className="text-md font-medium text-slate-700 mb-3">Información del Vehículo</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Marca *
                      </label>
                      <input
                        type="text"
                        value={newLead.vehicle_make}
                        onChange={(e) => setNewLead({...newLead, vehicle_make: e.target.value})}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ej: Toyota"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Modelo *
                      </label>
                      <input
                        type="text"
                        value={newLead.vehicle_model}
                        onChange={(e) => setNewLead({...newLead, vehicle_model: e.target.value})}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ej: Corolla"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Año *
                      </label>
                      <input
                        type="number"
                        value={newLead.vehicle_year}
                        onChange={(e) => setNewLead({...newLead, vehicle_year: parseInt(e.target.value)})}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ej: 2023"
                        min="1990"
                        max="2025"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Valor del Vehículo (GTQ) *
                      </label>
                      <input
                        type="number"
                        value={newLead.vehicle_value}
                        onChange={(e) => setNewLead({...newLead, vehicle_value: parseFloat(e.target.value)})}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ej: 150000"
                        min="0"
                        step="1000"
                        required
                      />
                    </div>
                  </div>
                </div>

                {/* Información de la Cotización */}
                <div className="border-b pb-4">
                  <h4 className="text-md font-medium text-slate-700 mb-3">Información de la Cotización</h4>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Tipo de Cotización
                    </label>
                    <div className="flex gap-4">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value="existing"
                          checked={quoteType === "existing"}
                          onChange={(e) => setQuoteType(e.target.value)}
                          className="mr-2"
                        />
                        Producto Existente
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value="custom"
                          checked={quoteType === "custom"}
                          onChange={(e) => setQuoteType(e.target.value)}
                          className="mr-2"
                        />
                        Cotización Personalizada
                      </label>
                    </div>
                  </div>

                  {quoteType === "existing" ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                          Aseguradora
                        </label>
                        <select
                          value={newLead.selected_insurer}
                          onChange={(e) => setNewLead({...newLead, selected_insurer: e.target.value})}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        >
                          <option value="">Seleccionar Aseguradora</option>
                          {insurers.map((insurer) => (
                            <option key={insurer.id} value={insurer.name}>
                              {insurer.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                          Precio de Cotización (GTQ)
                        </label>
                        <input
                          type="number"
                          value={newLead.selected_quote_price || ""}
                          onChange={(e) => setNewLead({...newLead, selected_quote_price: parseFloat(e.target.value)})}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                          placeholder="Ej: 2500"
                          min="0"
                          step="0.01"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                          Aseguradora Personalizada
                        </label>
                        <input
                          type="text"
                          value={newLead.selected_insurer}
                          onChange={(e) => setNewLead({...newLead, selected_insurer: e.target.value})}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                          placeholder="Ej: Seguros Personalizados S.A."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                          Precio de Cotización (GTQ)
                        </label>
                        <input
                          type="number"
                          value={newLead.selected_quote_price || ""}
                          onChange={(e) => setNewLead({...newLead, selected_quote_price: parseFloat(e.target.value)})}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                          placeholder="Ej: 2500"
                          min="0"
                          step="0.01"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Asignación de Corredor */}
                <div>
                  <h4 className="text-md font-medium text-slate-700 mb-3">Asignación de Corredor</h4>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Tipo de Asignación
                    </label>
                    <div className="flex gap-4">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value="manual"
                          checked={assignmentType === "manual"}
                          onChange={(e) => setAssignmentType(e.target.value)}
                          className="mr-2"
                        />
                        Asignar Manualmente
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value="roundrobin"
                          checked={assignmentType === "roundrobin"}
                          onChange={(e) => setAssignmentType(e.target.value)}
                          className="mr-2"
                        />
                        Asignación Automática (Round-Robin)
                      </label>
                    </div>
                  </div>

                  {assignmentType === "manual" && (
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Seleccionar Corredor
                      </label>
                      <select
                        value={selectedBrokerId}
                        onChange={(e) => setSelectedBrokerId(e.target.value)}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        required={assignmentType === "manual"}
                      >
                        <option value="">Seleccionar Corredor</option>
                        {brokers
                          .filter(broker => broker.subscription_status === "Active")
                          .map((broker) => (
                          <option key={broker.id} value={broker.id}>
                            {broker.name} - {broker.corretaje_name} ({broker.current_month_leads}/{broker.monthly_lead_quota} leads)
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Crear Lead
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

        {/* Modal para asignar lead */}
        {showAssignModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Asignar Lead a Corredor</h3>
                <button
                  onClick={() => setShowAssignModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-slate-600 mb-4">
                    Lead: {selectedLead?.name || selectedLead?.user_id?.substring(0, 8)}
                  </p>
                  
                  <h4 className="text-sm font-medium text-slate-700 mb-3">Seleccionar Corredor:</h4>
                  
                  <div className="space-y-2">
                    {brokers
                      .filter(broker => broker.subscription_status === "Active")
                      .map((broker) => (
                      <button
                        key={broker.id}
                        onClick={() => assignLeadToBroker(broker.id)}
                        className="w-full text-left p-3 border border-slate-200 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-colors"
                      >
                        <div className="font-medium text-slate-800">{broker.name}</div>
                        <div className="text-sm text-slate-600">{broker.corretaje_name}</div>
                        <div className="text-sm text-slate-500">
                          Leads actuales: {broker.current_month_leads}/{broker.monthly_lead_quota}
                        </div>
                      </button>
                    ))}
                  </div>

                  <div className="mt-4 pt-4 border-t">
                    <button
                      onClick={async () => {
                        try {
                          await axios.post(`${API}/admin/leads/${selectedLead.id}/assign-auto`, {}, {
                            headers: { 'Content-Type': 'application/json' }
                          });
                          setShowAssignModal(false);
                          fetchLeads();
                          alert("Lead asignado automáticamente");
                        } catch (error) {
                          console.error("Error auto-assigning lead:", error);
                          alert("Error en asignación automática: " + (error.response?.data?.detail || "Error desconocido"));
                        }
                      }}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                    >
                      Asignación Automática (Round-Robin)
                    </button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShowAssignModal(false)}
                    className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal para ver detalles del lead */}
        {showDetailsModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Detalles del Lead</h3>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              {selectedLead && (
                <div className="space-y-6">
                  {/* Información Personal */}
                  <div className="border-b pb-4">
                    <h4 className="text-md font-medium text-slate-700 mb-3">Información Personal</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-slate-600">Nombre</label>
                        <p className="text-slate-800">{selectedLead.name || 'No especificado'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Teléfono</label>
                        <p className="text-slate-800">{selectedLead.phone_number || 'No especificado'}</p>
                      </div>
                    </div>
                  </div>

                  {/* Información del Vehículo */}
                  <div className="border-b pb-4">
                    <h4 className="text-md font-medium text-slate-700 mb-3">Información del Vehículo</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-slate-600">Marca</label>
                        <p className="text-slate-800">{selectedLead.vehicle_make || 'No especificado'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Modelo</label>
                        <p className="text-slate-800">{selectedLead.vehicle_model || 'No especificado'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Año</label>
                        <p className="text-slate-800">{selectedLead.vehicle_year || 'No especificado'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Valor del Vehículo</label>
                        <p className="text-slate-800">
                          {selectedLead.vehicle_value ? `Q${selectedLead.vehicle_value.toLocaleString()}` : 'No especificado'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Información de la Cotización */}
                  <div className="border-b pb-4">
                    <h4 className="text-md font-medium text-slate-700 mb-3">Información de Cotización</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-slate-600">Aseguradora Seleccionada</label>
                        <p className="text-slate-800">{selectedLead.selected_insurer || 'No seleccionada'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Precio de Cotización</label>
                        <p className="text-slate-800">
                          {selectedLead.selected_quote_price ? `Q${selectedLead.selected_quote_price.toLocaleString()}` : 'No especificado'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Estados y Asignación */}
                  <div className="border-b pb-4">
                    <h4 className="text-md font-medium text-slate-700 mb-3">Estado y Asignación</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-slate-600">Estado del Sistema</label>
                        <p className="text-slate-800">{selectedLead.status}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Estado del Broker</label>
                        <p className="text-slate-800">{selectedLead.broker_status}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Corredor Asignado</label>
                        <p className="text-slate-800">
                          {selectedLead.assigned_broker_id 
                            ? brokers.find(b => b.id === selectedLead.assigned_broker_id)?.name || 'Corredor desconocido'
                            : 'Sin asignar'
                          }
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Monto Cerrado</label>
                        <p className="text-slate-800">
                          {selectedLead.closed_amount ? `Q${selectedLead.closed_amount.toLocaleString()}` : 'No cerrado'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Notas del Broker */}
                  {selectedLead.broker_notes && (
                    <div className="border-b pb-4">
                      <h4 className="text-md font-medium text-slate-700 mb-3">Notas del Corredor</h4>
                      <p className="text-slate-800 bg-slate-50 p-3 rounded-lg">{selectedLead.broker_notes}</p>
                    </div>
                  )}

                  {/* Fechas */}
                  <div>
                    <h4 className="text-md font-medium text-slate-700 mb-3">Fechas Importantes</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-slate-600">Fecha de Creación</label>
                        <p className="text-slate-800">{formatDate(selectedLead.created_at)}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-600">Última Actualización</label>
                        <p className="text-slate-800">{formatDate(selectedLead.updated_at)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-6">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal para re-asignar lead */}
        {showReassignModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Re-asignar Lead</h3>
                <button
                  onClick={() => setShowReassignModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-slate-600 mb-4">
                    Re-asignar lead: <strong>{selectedLeadForReassign?.name || selectedLeadForReassign?.user_id?.substring(0, 8)}</strong>
                  </p>
                  <p className="text-sm text-slate-500 mb-4">
                    Corredor actual: <strong>
                      {selectedLeadForReassign?.assigned_broker_id 
                        ? brokers.find(b => b.id === selectedLeadForReassign.assigned_broker_id)?.name || 'Desconocido'
                        : 'Sin asignar'
                      }
                    </strong>
                  </p>
                  
                  <h4 className="text-sm font-medium text-slate-700 mb-3">Seleccionar Nuevo Corredor:</h4>
                  
                  <div className="space-y-2">
                    {brokers
                      .filter(broker => broker.subscription_status === "Active" && broker.id !== selectedLeadForReassign?.assigned_broker_id)
                      .map((broker) => (
                      <button
                        key={broker.id}
                        onClick={() => reassignLeadToBroker(broker.id)}
                        className="w-full text-left p-3 border border-slate-200 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-colors"
                      >
                        <div className="font-medium text-slate-800">{broker.name}</div>
                        <div className="text-sm text-slate-600">{broker.corretaje_name}</div>
                        <div className="text-sm text-slate-500">
                          Leads actuales: {broker.current_month_leads}/{broker.monthly_lead_quota}
                        </div>
                      </button>
                    ))}
                  </div>

                  <div className="mt-4 pt-4 border-t">
                    <button
                      onClick={async () => {
                        try {
                          await axios.post(`${API}/admin/leads/${selectedLeadForReassign.id}/assign-auto`, {}, {
                            headers: { 'Content-Type': 'application/json' }
                          });
                          setShowReassignModal(false);
                          setSelectedLeadForReassign(null);
                          fetchLeads();
                          alert("Lead re-asignado automáticamente");
                        } catch (error) {
                          console.error("Error auto-reassigning lead:", error);
                          alert("Error en re-asignación automática: " + (error.response?.data?.detail || "Error desconocido"));
                        }
                      }}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                    >
                      Re-asignar Automáticamente (Round-Robin)
                    </button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowReassignModal(false);
                      setSelectedLeadForReassign(null);
                    }}
                    className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

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