import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, Save, X, AlertCircle, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const InsuranceCompanyManagement = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('aseguradoras');
  const [aseguradoras, setAseguradoras] = useState([]);
  const [vehiculosNoAsegurables, setVehiculosNoAsegurables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form state for Aseguradora
  const [aseguradoraForm, setAseguradoraForm] = useState({
    nombre: '',
    iva: 0.12,
    cuotas: 12,
    completo_gastos_emision: 0,
    completo_asistencia: 0,
    completo_prima_minima: 0,
    rc_gastos_emision: 0,
    rc_asistencia: 0,
    completo_tasas: [],
    rc_prima_neta: 0,
    completo_año_desde: 2000,
    completo_año_hasta: 2025,
    rc_año_desde: 2000,
    rc_año_hasta: 2025,
    activo: true
  });

  // Form state for Vehiculo No Asegurable
  const [vehiculoForm, setVehiculoForm] = useState({
    marca: '',
    modelo: '',
    año: null,
    razon: ''
  });

  const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchAseguradoras();
    fetchVehiculosNoAsegurables();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  // ===== ASEGURADORAS FUNCTIONS =====
  const fetchAseguradoras = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/admin/aseguradoras`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setAseguradoras(data);
      }
    } catch (error) {
      console.error('Error fetching aseguradoras:', error);
      setError('Error al cargar aseguradoras');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAseguradora = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/aseguradoras`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(aseguradoraForm)
      });

      if (response.ok) {
        setSuccess('Aseguradora creada exitosamente');
        setShowForm(false);
        resetAseguradoraForm();
        fetchAseguradoras();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const error = await response.json();
        setError(error.detail || 'Error al crear aseguradora');
      }
    } catch (error) {
      console.error('Error creating aseguradora:', error);
      setError('Error al crear aseguradora');
    }
  };

  const handleUpdateAseguradora = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/aseguradoras/${id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(aseguradoraForm)
      });

      if (response.ok) {
        setSuccess('Aseguradora actualizada exitosamente');
        setEditingId(null);
        resetAseguradoraForm();
        fetchAseguradoras();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const error = await response.json();
        setError(error.detail || 'Error al actualizar aseguradora');
      }
    } catch (error) {
      console.error('Error updating aseguradora:', error);
      setError('Error al actualizar aseguradora');
    }
  };

  const handleDeleteAseguradora = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar esta aseguradora?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/admin/aseguradoras/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        setSuccess('Aseguradora eliminada exitosamente');
        fetchAseguradoras();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const error = await response.json();
        setError(error.detail || 'Error al eliminar aseguradora');
      }
    } catch (error) {
      console.error('Error deleting aseguradora:', error);
      setError('Error al eliminar aseguradora');
    }
  };

  const startEditAseguradora = (aseguradora) => {
    setEditingId(aseguradora.id);
    setAseguradoraForm(aseguradora);
    setShowForm(true);
  };

  const resetAseguradoraForm = () => {
    setAseguradoraForm({
      nombre: '',
      iva: 0.12,
      cuotas: 12,
      completo_gastos_emision: 0,
      completo_asistencia: 0,
      completo_prima_minima: 0,
      rc_gastos_emision: 0,
      rc_asistencia: 0,
      completo_tasas: [],
      rc_prima_neta: 0,
      completo_año_desde: 2000,
      completo_año_hasta: 2025,
      rc_año_desde: 2000,
      rc_año_hasta: 2025,
      activo: true
    });
    setEditingId(null);
    setShowForm(false);
  };

  const addTasaRango = (tipo) => {
    const newTasa = { desde: 0, hasta: 0, tasa: 0 };
    setAseguradoraForm({
      ...aseguradoraForm,
      completo_tasas: [...aseguradoraForm.completo_tasas, newTasa]
    });
  };

  const removeTasaRango = (index) => {
    const newTasas = aseguradoraForm.completo_tasas.filter((_, i) => i !== index);
    setAseguradoraForm({ ...aseguradoraForm, completo_tasas: newTasas });
  };

  const updateTasaRango = (index, field, value) => {
    const newTasas = [...aseguradoraForm.completo_tasas];
    newTasas[index][field] = parseFloat(value) || 0;
    setAseguradoraForm({ ...aseguradoraForm, completo_tasas: newTasas });
  };

  // ===== VEHICULOS NO ASEGURABLES FUNCTIONS =====
  const fetchVehiculosNoAsegurables = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/admin/vehiculos-no-asegurables`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setVehiculosNoAsegurables(data);
      }
    } catch (error) {
      console.error('Error fetching vehiculos no asegurables:', error);
      setError('Error al cargar vehículos no asegurables');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVehiculo = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/vehiculos-no-asegurables`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(vehiculoForm)
      });

      if (response.ok) {
        setSuccess('Vehículo agregado a lista de exclusión');
        resetVehiculoForm();
        fetchVehiculosNoAsegurables();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const error = await response.json();
        setError(error.detail || 'Error al agregar vehículo');
      }
    } catch (error) {
      console.error('Error creating vehiculo:', error);
      setError('Error al agregar vehículo');
    }
  };

  const handleDeleteVehiculo = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este vehículo de la lista?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/admin/vehiculos-no-asegurables/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        setSuccess('Vehículo eliminado de la lista');
        fetchVehiculosNoAsegurables();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const error = await response.json();
        setError(error.detail || 'Error al eliminar vehículo');
      }
    } catch (error) {
      console.error('Error deleting vehiculo:', error);
      setError('Error al eliminar vehículo');
    }
  };

  const resetVehiculoForm = () => {
    setVehiculoForm({
      marca: '',
      modelo: '',
      año: null,
      razon: ''
    });
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header with back button */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Gestión de Aseguradoras</h1>
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
        >
          <ArrowLeft size={20} className="mr-2" />
          Volver al Dashboard
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded flex items-center">
          <AlertCircle className="mr-2" size={20} />
          {error}
          <button onClick={() => setError('')} className="ml-auto">
            <X size={20} />
          </button>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded flex items-center">
          <AlertCircle className="mr-2" size={20} />
          {success}
          <button onClick={() => setSuccess('')} className="ml-auto">
            <X size={20} />
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-300">
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveTab('aseguradoras')}
            className={`px-4 py-2 font-semibold ${
              activeTab === 'aseguradoras'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Aseguradoras
          </button>
          <button
            onClick={() => setActiveTab('no-asegurables')}
            className={`px-4 py-2 font-semibold ${
              activeTab === 'no-asegurables'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Vehículos No Asegurables
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'aseguradoras' && (
        <div>
          {/* Add/Edit Aseguradora Button */}
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="mb-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center"
            >
              <Plus size={20} className="mr-2" />
              Agregar Aseguradora
            </button>
          )}

          {/* Aseguradora Form */}
          {showForm && (
            <div className="mb-6 p-6 border border-gray-300 rounded-lg bg-white shadow">
              <h2 className="text-xl font-semibold mb-4">
                {editingId ? 'Editar Aseguradora' : 'Nueva Aseguradora'}
              </h2>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre de Aseguradora *
                  </label>
                  <input
                    type="text"
                    value={aseguradoraForm.nombre}
                    onChange={(e) =>
                      setAseguradoraForm({ ...aseguradoraForm, nombre: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">% IVA</label>
                  <input
                    type="number"
                    step="0.01"
                    value={aseguradoraForm.iva}
                    onChange={(e) =>
                      setAseguradoraForm({ ...aseguradoraForm, iva: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Número de Cuotas
                  </label>
                  <input
                    type="number"
                    value={aseguradoraForm.cuotas}
                    onChange={(e) =>
                      setAseguradoraForm({ ...aseguradoraForm, cuotas: parseInt(e.target.value) || 12 })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select
                    value={aseguradoraForm.activo}
                    onChange={(e) =>
                      setAseguradoraForm({ ...aseguradoraForm, activo: e.target.value === 'true' })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="true">Activa</option>
                    <option value="false">Inactiva</option>
                  </select>
                </div>
              </div>

              {/* Seguro Completo Section */}
              <div className="mb-4 p-4 bg-blue-50 rounded">
                <h3 className="text-lg font-semibold mb-3 text-blue-800">Seguro Completo</h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Gastos de Emisión (Q)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={aseguradoraForm.completo_gastos_emision}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          completo_gastos_emision: parseFloat(e.target.value) || 0
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Asistencia (Q)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={aseguradoraForm.completo_asistencia}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          completo_asistencia: parseFloat(e.target.value) || 0
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prima Mínima (Q)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={aseguradoraForm.completo_prima_minima}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          completo_prima_minima: parseFloat(e.target.value) || 0
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                      placeholder="Ej: 800"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Si (Suma × Tasa%) {'<'} Prima Mínima, usa Prima Mínima
                    </p>
                  </div>
                  <div></div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Año Desde
                    </label>
                    <input
                      type="number"
                      value={aseguradoraForm.completo_año_desde}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          completo_año_desde: parseInt(e.target.value) || 2000
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Año Hasta
                    </label>
                    <input
                      type="number"
                      value={aseguradoraForm.completo_año_hasta}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          completo_año_hasta: parseInt(e.target.value) || 2025
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Tasas Completo */}
                <div className="mb-2">
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-700">Tasas por Rango</label>
                    <button
                      onClick={() => addTasaRango()}
                      className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                    >
                      + Agregar Rango
                    </button>
                  </div>
                  {aseguradoraForm.completo_tasas.map((tasa, index) => (
                    <div key={index} className="grid grid-cols-4 gap-2 mb-2">
                      <input
                        type="number"
                        placeholder="Desde (Q)"
                        value={tasa.desde}
                        onChange={(e) => updateTasaRango(index, 'desde', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <input
                        type="number"
                        placeholder="Hasta (Q)"
                        value={tasa.hasta}
                        onChange={(e) => updateTasaRango(index, 'hasta', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Tasa (%)"
                        value={tasa.tasa}
                        onChange={(e) => updateTasaRango(index, 'tasa', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <button
                        onClick={() => removeTasaRango(index)}
                        className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Seguro RC Section */}
              <div className="mb-4 p-4 bg-green-50 rounded">
                <h3 className="text-lg font-semibold mb-3 text-green-800">Seguro RC</h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prima Neta (Q)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={aseguradoraForm.rc_prima_neta}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          rc_prima_neta: parseFloat(e.target.value) || 0
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Gastos de Emisión (Q)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={aseguradoraForm.rc_gastos_emision}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          rc_gastos_emision: parseFloat(e.target.value) || 0
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Asistencia (Q)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={aseguradoraForm.rc_asistencia}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          rc_asistencia: parseFloat(e.target.value) || 0
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div></div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Año Desde
                    </label>
                    <input
                      type="number"
                      value={aseguradoraForm.rc_año_desde}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          rc_año_desde: parseInt(e.target.value) || 2000
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Año Hasta
                    </label>
                    <input
                      type="number"
                      value={aseguradoraForm.rc_año_hasta}
                      onChange={(e) =>
                        setAseguradoraForm({
                          ...aseguradoraForm,
                          rc_año_hasta: parseInt(e.target.value) || 2025
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    if (editingId) {
                      handleUpdateAseguradora(editingId);
                    } else {
                      handleCreateAseguradora();
                    }
                  }}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 flex items-center"
                >
                  <Save size={20} className="mr-2" />
                  {editingId ? 'Actualizar' : 'Guardar'}
                </button>
                <button
                  onClick={resetAseguradoraForm}
                  className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 flex items-center"
                >
                  <X size={20} className="mr-2" />
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {/* Aseguradoras Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nombre
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IVA
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cuotas
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {aseguradoras.map((aseguradora) => (
                  <tr key={aseguradora.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{aseguradora.nombre}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{(aseguradora.iva * 100).toFixed(0)}%</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{aseguradora.cuotas}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          aseguradora.activo
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {aseguradora.activo ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => startEditAseguradora(aseguradora)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDeleteAseguradora(aseguradora.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'no-asegurables' && (
        <div>
          {/* Vehiculo Form */}
          <div className="mb-6 p-6 border border-gray-300 rounded-lg bg-white shadow">
            <h2 className="text-xl font-semibold mb-4">Agregar Vehículo No Asegurable</h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Marca *</label>
                <input
                  type="text"
                  value={vehiculoForm.marca}
                  onChange={(e) => setVehiculoForm({ ...vehiculoForm, marca: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Modelo *</label>
                <input
                  type="text"
                  value={vehiculoForm.modelo}
                  onChange={(e) => setVehiculoForm({ ...vehiculoForm, modelo: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Año (opcional)
                </label>
                <input
                  type="number"
                  value={vehiculoForm.año || ''}
                  onChange={(e) =>
                    setVehiculoForm({ ...vehiculoForm, año: e.target.value ? parseInt(e.target.value) : null })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  placeholder="Dejar vacío para todos los años"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Razón</label>
                <input
                  type="text"
                  value={vehiculoForm.razon}
                  onChange={(e) => setVehiculoForm({ ...vehiculoForm, razon: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  placeholder="Motivo de exclusión"
                />
              </div>
            </div>
            <button
              onClick={handleCreateVehiculo}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center"
            >
              <Plus size={20} className="mr-2" />
              Agregar a Lista
            </button>
          </div>

          {/* Vehiculos Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Marca
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Modelo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Año
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Razón
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {vehiculosNoAsegurables.map((vehiculo) => (
                  <tr key={vehiculo.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{vehiculo.marca}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{vehiculo.modelo}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {vehiculo.año || 'Todos los años'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{vehiculo.razon || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleDeleteVehiculo(vehiculo.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default InsuranceCompanyManagement;
