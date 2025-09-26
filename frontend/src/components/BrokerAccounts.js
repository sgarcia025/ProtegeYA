import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

const BrokerAccounts = ({ user }) => {
  const [accounts, setAccounts] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showTransactionsModal, setShowTransactionsModal] = useState(false);
  const [showAssignPlanModal, setShowAssignPlanModal] = useState(false);
  const [selectedBroker, setSelectedBroker] = useState(null);
  const [paymentData, setPaymentData] = useState({
    amount: '',
    reference_number: '',
    description: ''
  });
  const [planAssignment, setPlanAssignment] = useState({
    subscription_plan_id: ''
  });

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (isAdmin) {
      fetchAccounts();
      fetchBrokers();
      fetchPlans();
    }
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get(`${API}/admin/accounts`);
      setAccounts(response.data);
    } catch (error) {
      console.error("Error fetching accounts:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBrokers = async () => {
    try {
      const response = await axios.get(`${API}/brokers`);
      setBrokers(response.data);
    } catch (error) {
      console.error("Error fetching brokers:", error);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/admin/plans`);
      setPlans(response.data);
    } catch (error) {
      console.error("Error fetching plans:", error);
    }
  };

  const fetchTransactions = async (accountId) => {
    try {
      const response = await axios.get(`${API}/admin/transactions/${accountId}`);
      setTransactions(response.data);
    } catch (error) {
      console.error("Error fetching transactions:", error);
    }
  };

  const applyPayment = async (e) => {
    e.preventDefault();
    try {
      const brokerId = selectedAccount.broker_id;
      await axios.post(`${API}/admin/accounts/${brokerId}/apply-payment`, paymentData);
      
      setShowPaymentModal(false);
      setPaymentData({
        amount: '',
        reference_number: '',
        description: ''
      });
      fetchAccounts(); // Refresh accounts
      alert("Pago aplicado exitosamente");
    } catch (error) {
      console.error("Error applying payment:", error);
      alert("Error al aplicar pago: " + (error.response?.data?.detail || "Error desconocido"));
    }
  };

  const assignPlan = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/brokers/${selectedBroker.id}/assign-plan`, planAssignment);
      
      setShowAssignPlanModal(false);
      setPlanAssignment({ subscription_plan_id: '' });
      setSelectedBroker(null);
      fetchAccounts(); // Refresh accounts
      fetchBrokers(); // Refresh brokers
      alert("Plan asignado y cuenta creada exitosamente");
    } catch (error) {
      console.error("Error assigning plan:", error);
      alert("Error al asignar plan: " + (error.response?.data?.detail || "Error desconocido"));
    }
  };

  const generateCharges = async () => {
    if (window.confirm("¿Generar cargos mensuales para todos los corredores?")) {
      try {
        await axios.post(`${API}/admin/accounts/generate-charges`);
        fetchAccounts();
        alert("Cargos mensuales generados exitosamente");
      } catch (error) {
        console.error("Error generating charges:", error);
        alert("Error al generar cargos: " + (error.response?.data?.detail || "Error desconocido"));
      }
    }
  };

  const checkOverdue = async () => {
    if (window.confirm("¿Verificar cuentas vencidas y aplicar acciones automáticas?")) {
      try {
        await axios.post(`${API}/admin/accounts/check-overdue`);
        fetchAccounts();
        alert("Verificación de cuentas vencidas completada");
      } catch (error) {
        console.error("Error checking overdue:", error);
        alert("Error al verificar cuentas: " + (error.response?.data?.detail || "Error desconocido"));
      }
    }
  };

  const viewTransactions = async (account) => {
    setSelectedAccount(account);
    await fetchTransactions(account.id);
    setShowTransactionsModal(true);
  };

  const handlePayment = (account) => {
    setSelectedAccount(account);
    setShowPaymentModal(true);
  };

  const handleAssignPlan = (broker) => {
    setSelectedBroker(broker);
    setShowAssignPlanModal(true);
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Active': { color: 'bg-emerald-100 text-emerald-800', text: 'Al Día' },
      'Overdue': { color: 'bg-orange-100 text-orange-800', text: 'Vencido' },
      'GracePeriod': { color: 'bg-yellow-100 text-yellow-800', text: 'En Gracia' },
      'Suspended': { color: 'bg-red-100 text-red-800', text: 'Suspendido' }
    };
    
    const config = statusConfig[status] || { color: 'bg-slate-100 text-slate-800', text: status };
    
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${config.color}`}>
        {config.text}
      </span>
    );
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-GT', {
      style: 'currency',
      currency: 'GTQ'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-GT');
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-800">Acceso Denegado</h1>
          <p className="text-slate-600">Solo los administradores pueden acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Cargando cuentas...</p>
        </div>
      </div>
    );
  }

  // Get brokers without accounts
  const brokersWithoutAccounts = brokers.filter(broker => 
    !accounts.some(account => account.broker_id === broker.id)
  );

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto">
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
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Cuentas Corrientes</h1>
            <p className="text-slate-600">Gestión financiera de corredores</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={generateCharges}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
            >
              Generar Cargos
            </button>
            <button
              onClick={checkOverdue}
              className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
            >
              Verificar Vencimientos
            </button>
          </div>
        </div>

        {/* Brokers sin cuenta */}
        {brokersWithoutAccounts.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-8">
            <h3 className="text-lg font-semibold text-yellow-800 mb-4">
              Corredores sin Plan Asignado ({brokersWithoutAccounts.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {brokersWithoutAccounts.map((broker) => (
                <div key={broker.id} className="bg-white p-4 rounded-lg border border-yellow-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-slate-800">{broker.name}</h4>
                      <p className="text-sm text-slate-600">{broker.email}</p>
                      <p className="text-sm text-slate-500">{broker.corretaje_name}</p>
                    </div>
                    <button
                      onClick={() => handleAssignPlan(broker)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1 rounded text-sm font-semibold transition-colors"
                    >
                      Asignar Plan
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cuentas corrientes */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200">
            <h2 className="text-xl font-semibold text-slate-800">Cuentas de Corredores</h2>
          </div>

          {accounts.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-slate-600">No hay cuentas corrientes registradas.</p>
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
                      Cuenta
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Balance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Próximo Vencimiento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {accounts.map((account) => {
                    const broker = brokers.find(b => b.id === account.broker_id);
                    return (
                      <tr key={account.id} className="hover:bg-slate-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-slate-800">
                              {broker?.name || 'Corredor Desconocido'}
                            </div>
                            <div className="text-sm text-slate-500">{broker?.email}</div>
                            <div className="text-xs text-slate-400">{broker?.corretaje_name}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-slate-800">
                            {account.account_number}
                          </div>
                          <div className="text-sm text-slate-500">
                            Desde: {formatDate(account.subscription_start_date)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`text-sm font-bold ${
                            account.current_balance < 0 
                              ? 'text-red-600' 
                              : account.current_balance > 0 
                                ? 'text-emerald-600' 
                                : 'text-slate-600'
                          }`}>
                            {formatCurrency(account.current_balance)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(account.account_status)}
                          {account.grace_period_end && (
                            <div className="text-xs text-orange-600 mt-1">
                              Gracia hasta: {formatDate(account.grace_period_end)}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                          {formatDate(account.next_due_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => viewTransactions(account)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Movimientos
                          </button>
                          <button
                            onClick={() => handlePayment(account)}
                            className="text-emerald-600 hover:text-emerald-900"
                          >
                            Aplicar Pago
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal para aplicar pago */}
        {showPaymentModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">Aplicar Pago</h3>
                <button
                  onClick={() => setShowPaymentModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              {selectedAccount && (
                <div className="mb-4 p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600">
                    <strong>Cuenta:</strong> {selectedAccount.account_number}<br/>
                    <strong>Balance actual:</strong> <span className={`font-bold ${
                      selectedAccount.current_balance < 0 ? 'text-red-600' : 'text-emerald-600'
                    }`}>{formatCurrency(selectedAccount.current_balance)}</span>
                  </p>
                </div>
              )}

              <form onSubmit={applyPayment} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Monto del Pago *
                  </label>
                  <input
                    type="number"
                    value={paymentData.amount}
                    onChange={(e) => setPaymentData({...paymentData, amount: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                    min="0.01"
                    step="0.01"
                    placeholder="Ej: 500.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Número de Referencia
                  </label>
                  <input
                    type="text"
                    value={paymentData.reference_number}
                    onChange={(e) => setPaymentData({...paymentData, reference_number: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="Ej: TXN123456, Cheque #1001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Descripción
                  </label>
                  <textarea
                    value={paymentData.description}
                    onChange={(e) => setPaymentData({...paymentData, description: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    rows="3"
                    placeholder="Detalles adicionales del pago..."
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Aplicar Pago
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowPaymentModal(false)}
                    className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal para asignar plan */}
        {showAssignPlanModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">Asignar Plan de Suscripción</h3>
                <button
                  onClick={() => setShowAssignPlanModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              {selectedBroker && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <strong>Corredor:</strong> {selectedBroker.name}<br/>
                    <strong>Email:</strong> {selectedBroker.email}<br/>
                    <strong>Corretaje:</strong> {selectedBroker.corretaje_name}
                  </p>
                </div>
              )}

              <form onSubmit={assignPlan} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Plan de Suscripción *
                  </label>
                  <select
                    value={planAssignment.subscription_plan_id}
                    onChange={(e) => setPlanAssignment({...planAssignment, subscription_plan_id: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                  >
                    <option value="">Seleccionar plan</option>
                    {plans.map((plan) => (
                      <option key={plan.id} value={plan.id}>
                        {plan.name} - {formatCurrency(plan.amount)}/{plan.period}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-sm text-yellow-800">
                    <strong>Nota:</strong> Se creará una cuenta corriente y se aplicará el primer cargo de suscripción automáticamente.
                  </p>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Asignar Plan
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAssignPlanModal(false)}
                    className="flex-1 bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal para ver movimientos */}
        {showTransactionsModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">
                  Movimientos de Cuenta - {selectedAccount?.account_number}
                </h3>
                <button
                  onClick={() => setShowTransactionsModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              {transactions.length === 0 ? (
                <p className="text-center text-slate-600 py-8">No hay movimientos registrados.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                          Fecha
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                          Tipo
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                          Descripción
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                          Monto
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                          Balance
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                          Referencia
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                      {transactions.map((transaction) => (
                        <tr key={transaction.id}>
                          <td className="px-4 py-3 text-sm text-slate-600">
                            {formatDate(transaction.created_at)}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              transaction.transaction_type === 'Payment' 
                                ? 'bg-emerald-100 text-emerald-800' 
                                : transaction.transaction_type === 'Charge'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-blue-100 text-blue-800'
                            }`}>
                              {transaction.transaction_type === 'Payment' ? 'Pago' : 
                               transaction.transaction_type === 'Charge' ? 'Cargo' : 'Ajuste'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-600">
                            {transaction.description}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`text-sm font-medium ${
                              transaction.amount > 0 ? 'text-emerald-600' : 'text-red-600'
                            }`}>
                              {transaction.amount > 0 ? '+' : ''}{formatCurrency(transaction.amount)}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`text-sm font-medium ${
                              transaction.balance_after < 0 ? 'text-red-600' : 'text-emerald-600'
                            }`}>
                              {formatCurrency(transaction.balance_after)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-600">
                            {transaction.reference_number || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="flex justify-end pt-6">
                <button
                  onClick={() => setShowTransactionsModal(false)}
                  className="bg-slate-300 hover:bg-slate-400 text-slate-700 py-2 px-4 rounded-lg font-semibold transition-colors"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrokerAccounts;