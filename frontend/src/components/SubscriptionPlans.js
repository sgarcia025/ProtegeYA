import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SubscriptionPlans = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [newPlan, setNewPlan] = useState({
    name: "",
    amount: 500.00,
    currency: "GTQ",
    period: "monthly",
    benefits: ["Acceso al panel de corredores", "Hasta 50 leads por mes", "Soporte técnico básico"],
    active: true
  });
  const { isAdmin } = useAuth();

  useEffect(() => {
    if (isAdmin) {
      fetchPlans();
    }
  }, [isAdmin]);

  const fetchPlans = async () => {
    try {
      // Mock data mientras implementamos el endpoint real
      const mockPlans = [
        {
          id: "plan_basic",
          name: "Plan Básico ProtegeYa",
          amount: 500.00,
          currency: "GTQ",
          period: "monthly",
          benefits: [
            "Acceso al panel de corredores",
            "Hasta 50 leads por mes",
            "Soporte técnico básico",
            "Reportes mensuales",
            "WhatsApp integration"
          ],
          active: true,
          created_at: new Date().toISOString()
        }
      ];
      setPlans(mockPlans);
    } catch (error) {
      console.error("Error fetching plans:", error);
    } finally {
      setLoading(false);
    }
  };

  const createPlan = async (e) => {
    e.preventDefault();
    try {
      // Mock creation
      const newPlanData = {
        ...newPlan,
        id: `plan_${Date.now()}`,
        created_at: new Date().toISOString()
      };
      
      setPlans([...plans, newPlanData]);
      
      setNewPlan({
        name: "",
        amount: 500.00,
        currency: "GTQ",
        period: "monthly",
        benefits: ["Acceso al panel de corredores", "Hasta 50 leads por mes", "Soporte técnico básico"],
        active: true
      });
      setShowCreateModal(false);
      alert("Plan creado exitosamente");
    } catch (error) {
      console.error("Error creating plan:", error);
      alert("Error al crear plan");
    }
  };

  const updatePlan = async (e) => {
    e.preventDefault();
    try {
      const updatedPlans = plans.map(plan => 
        plan.id === selectedPlan.id ? selectedPlan : plan
      );
      setPlans(updatedPlans);
      
      setShowEditModal(false);
      alert("Plan actualizado exitosamente");
    } catch (error) {
      console.error("Error updating plan:", error);
      alert("Error al actualizar plan");
    }
  };

  const togglePlanStatus = async (planId, currentStatus) => {
    try {
      const updatedPlans = plans.map(plan => 
        plan.id === planId ? {...plan, active: !currentStatus} : plan
      );
      setPlans(updatedPlans);
    } catch (error) {
      console.error("Error toggling plan status:", error);
      alert("Error al cambiar estado del plan");
    }
  };

  const handleEditPlan = (plan) => {
    setSelectedPlan({...plan});
    setShowEditModal(true);
  };

  const addBenefit = (planData, setPlanData) => {
    const newBenefit = "";
    setPlanData({...planData, benefits: [...planData.benefits, newBenefit]});
  };

  const updateBenefit = (index, value, planData, setPlanData) => {
    const updatedBenefits = planData.benefits.map((benefit, i) => 
      i === index ? value : benefit
    );
    setPlanData({...planData, benefits: updatedBenefits});
  };

  const removeBenefit = (index, planData, setPlanData) => {
    const updatedBenefits = planData.benefits.filter((_, i) => i !== index);
    setPlanData({...planData, benefits: updatedBenefits});
  };

  const getPeriodLabel = (period) => {
    const labels = {
      monthly: "Mensual",
      quarterly: "Trimestral", 
      semiannual: "Semestral",
      annual: "Anual"
    };
    return labels[period] || period;
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
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Planes de Suscripción</h1>
            <p className="text-slate-600">Gestiona los planes disponibles para corredores</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            + Nuevo Plan
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div key={plan.id} className="bg-white rounded-xl shadow-lg p-6 border-2 border-emerald-100">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-slate-800">{plan.name}</h3>
                  <p className="text-slate-600">{getPeriodLabel(plan.period)}</p>
                </div>
                <div className="text-right">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    plan.active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {plan.active ? 'Activo' : 'Inactivo'}
                  </span>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline">
                  <span className="text-3xl font-bold text-slate-900">Q{plan.amount.toFixed(2)}</span>
                  <span className="text-slate-500 ml-2">/ {getPeriodLabel(plan.period).toLowerCase()}</span>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="font-semibold text-slate-800 mb-3">Beneficios incluidos:</h4>
                <ul className="space-y-2">
                  {plan.benefits.map((benefit, index) => (
                    <li key={index} className="flex items-start">
                      <svg className="w-5 h-5 text-emerald-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                      </svg>
                      <span className="text-slate-600 text-sm">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEditPlan(plan)}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 py-2 px-4 rounded-lg font-medium transition-colors"
                >
                  Editar
                </button>
                <button
                  onClick={() => togglePlanStatus(plan.id, plan.active)}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    plan.active 
                      ? 'bg-red-100 hover:bg-red-200 text-red-700'
                      : 'bg-emerald-100 hover:bg-emerald-200 text-emerald-700'
                  }`}
                >
                  {plan.active ? 'Desactivar' : 'Activar'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Modal para crear plan */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-screen overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">Crear Nuevo Plan</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <form onSubmit={createPlan} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Nombre del Plan
                    </label>
                    <input
                      type="text"
                      value={newPlan.name}
                      onChange={(e) => setNewPlan({...newPlan, name: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Monto (GTQ)
                    </label>
                    <input
                      type="number"
                      value={newPlan.amount}
                      onChange={(e) => setNewPlan({...newPlan, amount: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Periodicidad
                    </label>
                    <select
                      value={newPlan.period}
                      onChange={(e) => setNewPlan({...newPlan, period: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    >
                      <option value="monthly">Mensual</option>
                      <option value="quarterly">Trimestral</option>
                      <option value="semiannual">Semestral</option>
                      <option value="annual">Anual</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Estado
                    </label>
                    <select
                      value={newPlan.active ? "active" : "inactive"}
                      onChange={(e) => setNewPlan({...newPlan, active: e.target.value === "active"})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    >
                      <option value="active">Activo</option>
                      <option value="inactive">Inactivo</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Beneficios del Plan
                  </label>
                  {newPlan.benefits.map((benefit, index) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={benefit}
                        onChange={(e) => updateBenefit(index, e.target.value, newPlan, setNewPlan)}
                        className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Beneficio del plan"
                      />
                      <button
                        type="button"
                        onClick={() => removeBenefit(index, newPlan, setNewPlan)}
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addBenefit(newPlan, setNewPlan)}
                    className="bg-emerald-100 hover:bg-emerald-200 text-emerald-700 px-3 py-2 rounded-lg text-sm"
                  >
                    + Agregar Beneficio
                  </button>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Crear Plan
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

        {/* Modal para editar plan */}
        {showEditModal && selectedPlan && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-screen overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">Editar Plan</h3>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <form onSubmit={updatePlan} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Nombre del Plan
                    </label>
                    <input
                      type="text"
                      value={selectedPlan.name}
                      onChange={(e) => setSelectedPlan({...selectedPlan, name: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Monto (GTQ)
                    </label>
                    <input
                      type="number"
                      value={selectedPlan.amount}
                      onChange={(e) => setSelectedPlan({...selectedPlan, amount: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Periodicidad
                    </label>
                    <select
                      value={selectedPlan.period}
                      onChange={(e) => setSelectedPlan({...selectedPlan, period: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    >
                      <option value="monthly">Mensual</option>
                      <option value="quarterly">Trimestral</option>
                      <option value="semiannual">Semestral</option>
                      <option value="annual">Anual</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Estado
                    </label>
                    <select
                      value={selectedPlan.active ? "active" : "inactive"}
                      onChange={(e) => setSelectedPlan({...selectedPlan, active: e.target.value === "active"})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    >
                      <option value="active">Activo</option>
                      <option value="inactive">Inactivo</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Beneficios del Plan
                  </label>
                  {selectedPlan.benefits.map((benefit, index) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={benefit}
                        onChange={(e) => updateBenefit(index, e.target.value, selectedPlan, setSelectedPlan)}
                        className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Beneficio del plan"
                      />
                      <button
                        type="button"
                        onClick={() => removeBenefit(index, selectedPlan, setSelectedPlan)}
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addBenefit(selectedPlan, setSelectedPlan)}
                    className="bg-emerald-100 hover:bg-emerald-200 text-emerald-700 px-3 py-2 rounded-lg text-sm"
                  >
                    + Agregar Beneficio
                  </button>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Actualizar Plan
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

export default SubscriptionPlans;