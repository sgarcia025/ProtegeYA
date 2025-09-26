import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

const MyAccount = ({ user }) => {
  const [account, setAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  const isBroker = user?.role === 'broker';

  useEffect(() => {
    if (isBroker) {
      fetchMyAccount();
      fetchMyTransactions();
    }
  }, []);

  const fetchMyAccount = async () => {
    try {
      const response = await axios.get(`${API}/my-account`);
      setAccount(response.data);
    } catch (error) {
      console.error("Error fetching account:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyTransactions = async () => {
    try {
      const response = await axios.get(`${API}/my-transactions`);
      setTransactions(response.data);
    } catch (error) {
      console.error("Error fetching transactions:", error);
    }
  };

  const getStatusInfo = (status) => {
    const statusConfig = {
      'Active': { 
        color: 'text-emerald-600', 
        bgColor: 'bg-emerald-100', 
        icon: '✅', 
        text: 'Al Día',
        message: 'Su cuenta está al corriente con los pagos.'
      },
      'Overdue': { 
        color: 'text-orange-600', 
        bgColor: 'bg-orange-100', 
        icon: '⚠️', 
        text: 'Vencido',
        message: 'Su pago está vencido. Por favor regularice su situación.'
      },
      'GracePeriod': { 
        color: 'text-yellow-600', 
        bgColor: 'bg-yellow-100', 
        icon: '⏰', 
        text: 'Período de Gracia',
        message: 'Tiene tiempo limitado para regularizar su pago antes de la suspensión.'
      },
      'Suspended': { 
        color: 'text-red-600', 
        bgColor: 'bg-red-100', 
        icon: '❌', 
        text: 'Suspendido',
        message: 'Su cuenta ha sido suspendida. Contacte al administrador para reactivarla.'
      }
    };
    
    return statusConfig[status] || { 
      color: 'text-slate-600', 
      bgColor: 'bg-slate-100', 
      icon: 'ℹ️', 
      text: status,
      message: 'Estado de cuenta desconocido.'
    };
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-GT', {
      style: 'currency',
      currency: 'GTQ'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-GT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('es-GT');
  };

  if (!isBroker) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-800">Acceso Denegado</h1>
          <p className="text-slate-600">Solo los corredores pueden acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Cargando información de cuenta...</p>
        </div>
      </div>
    );
  }

  if (!account) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="max-w-4xl mx-auto">
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
          
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">📋</div>
            <h1 className="text-2xl font-bold text-slate-800 mb-2">Sin Plan Asignado</h1>
            <p className="text-slate-600 mb-6">
              Aún no tiene un plan de suscripción asignado. Contacte al administrador para activar su cuenta.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-700">
                Una vez que el administrador le asigne un plan de suscripción, podrá ver aquí toda la información de su cuenta corriente, 
                incluyendo balances, movimientos y fechas de vencimiento.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const statusInfo = getStatusInfo(account.account_status);

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-4xl mx-auto">
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

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Mi Cuenta Corriente</h1>
          <p className="text-slate-600">Estado financiero de su suscripción</p>
        </div>

        {/* Información general de la cuenta */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Estado de cuenta */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-800">Estado de Cuenta</h2>
              <span className="text-2xl">{statusInfo.icon}</span>
            </div>
            
            <div className={`${statusInfo.bgColor} rounded-lg p-4 mb-4`}>
              <div className={`text-lg font-bold ${statusInfo.color} mb-2`}>
                {statusInfo.text}
              </div>
              <p className="text-sm text-slate-600">{statusInfo.message}</p>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Número de Cuenta:</span>
                <span className="font-medium">{account.account_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Suscrito desde:</span>
                <span className="font-medium">{formatDate(account.subscription_start_date)}</span>
              </div>
            </div>
          </div>

          {/* Balance actual */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Balance Actual</h2>
            
            <div className="text-center">
              <div className={`text-4xl font-bold mb-2 ${
                account.current_balance < 0 
                  ? 'text-red-600' 
                  : account.current_balance > 0 
                    ? 'text-emerald-600' 
                    : 'text-slate-600'
              }`}>
                {formatCurrency(account.current_balance)}
              </div>
              
              <p className="text-sm text-slate-600 mb-4">
                {account.current_balance < 0 
                  ? 'Saldo pendiente de pago' 
                  : account.current_balance > 0 
                    ? 'Saldo a favor' 
                    : 'Cuenta balanceada'
                }
              </p>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600">Próximo vencimiento:</span>
                  <span className="font-medium">{formatDate(account.next_due_date)}</span>
                </div>
                
                {account.grace_period_end && (
                  <div className="flex justify-between">
                    <span className="text-orange-600">Período de gracia hasta:</span>
                    <span className="font-medium text-orange-600">
                      {formatDate(account.grace_period_end)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Alertas importantes */}
        {(account.current_balance < 0 || account.account_status !== 'Active') && (
          <div className="mb-8">
            {account.account_status === 'GracePeriod' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <div className="flex items-center">
                  <div className="text-yellow-600 text-xl mr-3">⚠️</div>
                  <div>
                    <h3 className="font-semibold text-yellow-800">Período de Gracia Activo</h3>
                    <p className="text-sm text-yellow-700">
                      Tiene hasta el <strong>{formatDate(account.grace_period_end)}</strong> para regularizar su pago.
                      Después de esta fecha, su cuenta será suspendida automáticamente.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {account.account_status === 'Suspended' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div className="flex items-center">
                  <div className="text-red-600 text-xl mr-3">❌</div>
                  <div>
                    <h3 className="font-semibold text-red-800">Cuenta Suspendida</h3>
                    <p className="text-sm text-red-700">
                      Su cuenta ha sido suspendida por falta de pago. Para reactivarla, debe regularizar su situación
                      y contactar al administrador.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {account.current_balance < 0 && account.account_status === 'Active' && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
                <div className="flex items-center">
                  <div className="text-orange-600 text-xl mr-3">💰</div>
                  <div>
                    <h3 className="font-semibold text-orange-800">Pago Pendiente</h3>
                    <p className="text-sm text-orange-700">
                      Tiene un saldo pendiente de <strong>{formatCurrency(Math.abs(account.current_balance))}</strong>.
                      Próximo vencimiento: <strong>{formatDate(account.next_due_date)}</strong>
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Historial de movimientos */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200">
            <h2 className="text-xl font-semibold text-slate-800">Historial de Movimientos</h2>
          </div>

          {transactions.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-6xl mb-4">📝</div>
              <p className="text-slate-600">No hay movimientos registrados en su cuenta.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Descripción
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Monto
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Balance
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {transactions.map((transaction, index) => (
                    <tr key={transaction.id} className={index % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {formatDateTime(transaction.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
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
                      <td className="px-6 py-4 text-sm text-slate-600">
                        <div>
                          {transaction.description}
                          {transaction.reference_number && (
                            <div className="text-xs text-slate-400 mt-1">
                              Ref: {transaction.reference_number}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className={`text-sm font-medium ${
                          transaction.amount > 0 ? 'text-emerald-600' : 'text-red-600'
                        }`}>
                          {transaction.amount > 0 ? '+' : ''}{formatCurrency(transaction.amount)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className={`text-sm font-medium ${
                          transaction.balance_after < 0 ? 'text-red-600' : 'text-emerald-600'
                        }`}>
                          {formatCurrency(transaction.balance_after)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Información de contacto */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="text-blue-600 text-2xl mr-4">ℹ️</div>
            <div>
              <h3 className="font-semibold text-blue-800 mb-2">¿Necesita ayuda?</h3>
              <p className="text-sm text-blue-700">
                Si tiene preguntas sobre su cuenta, movimientos o necesita realizar un pago, 
                contacte al administrador del sistema para obtener asistencia.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyAccount;