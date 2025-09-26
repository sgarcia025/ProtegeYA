import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({
    name: "",
    email: "",
    password: "",
    role: "broker"
  });
  const [showEditModal, setShowEditModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [editUser, setEditUser] = useState({
    name: "",
    email: "",
    role: ""
  });
  const [resetPasswordData, setResetPasswordData] = useState({
    new_password: ""
  });
  const { isAdmin } = useAuth();

  useEffect(() => {
    if (isAdmin) {
      fetchUsers();
    }
  }, [isAdmin]);

  const fetchUsers = async () => {
    try {
      // Obtener usuarios de autenticación y brokers
      const [authUsersResponse, brokersResponse] = await Promise.all([
        axios.get(`${API}/auth/users`), // Obtener todos los usuarios de auth
        axios.get(`${API}/brokers`)     // Obtener todos los brokers
      ]);

      // Combinar datos de usuarios
      const allUsers = [];
      
      // Procesar usuarios de auth
      authUsersResponse.data.forEach(authUser => {
        if (authUser.role === 'admin') {
          allUsers.push({
            id: authUser.id,
            name: authUser.name,
            email: authUser.email,
            role: 'admin',
            subscription_status: authUser.active ? 'Active' : 'Inactive',
            created_at: authUser.created_at
          });
        } else if (authUser.role === 'broker') {
          // Buscar el broker correspondiente
          const broker = brokersResponse.data.find(b => b.user_id === authUser.id);
          allUsers.push({
            id: authUser.id,
            name: authUser.name,
            email: authUser.email,
            role: 'broker',
            subscription_status: broker ? broker.subscription_status : (authUser.active ? 'Active' : 'Inactive'),
            created_at: authUser.created_at
          });
        }
      });

      setUsers(allUsers);
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoading(false);
    }
  };

  const createUser = async (e) => {
    e.preventDefault();
    try {
      // Crear usuario de autenticación
      const userResponse = await axios.post(`${API}/auth/register`, newUser);
      
      // Si es broker, crear perfil de broker también
      if (newUser.role === "broker") {
        const brokerData = {
          user_id: userResponse.data.id,
          name: newUser.name,
          email: newUser.email,
          phone_number: "", // Se completará después
          whatsapp_number: "",
          corretaje_name: "", // Se completará después
          subscription_status: "Inactive",
          monthly_lead_quota: 50,
          commission_percentage: 10.0
        };
        
        await axios.post(`${API}/brokers`, brokerData);
      }
      
      setNewUser({
        name: "",
        email: "",
        password: "",
        role: "broker"
      });
      setShowCreateModal(false);
      fetchUsers();
      alert("Usuario creado exitosamente");
    } catch (error) {
      console.error("Error creating user:", error);
      alert("Error al crear usuario: " + (error.response?.data?.detail || "Error desconocido"));
    }
  };

  const resetPassword = async (user) => {
    setSelectedUser(user);
    setResetPasswordData({ new_password: "" });
    setShowResetPasswordModal(true);
  };

  const submitPasswordReset = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/auth/users/${selectedUser.id}/reset-password`, resetPasswordData);
      setShowResetPasswordModal(false);
      alert("Contraseña actualizada exitosamente");
    } catch (error) {
      console.error("Error resetting password:", error);
      alert("Error al resetear contraseña: " + (error.response?.data?.detail || "Error desconocido"));
    }
  };

  const editUserInfo = async (user) => {
    setSelectedUser(user);
    setEditUser({
      name: user.name,
      email: user.email,
      role: user.role
    });
    setShowEditModal(true);
  };

  const submitUserEdit = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/auth/users/${selectedUser.id}`, editUser);
      setShowEditModal(false);
      fetchUsers(); // Reload users
      alert("Usuario actualizado exitosamente");
    } catch (error) {
      console.error("Error updating user:", error);
      alert("Error al actualizar usuario: " + (error.response?.data?.detail || "Error desconocido"));
    }
  };

  const toggleUserStatus = async (userId, currentStatus) => {
    const action = currentStatus === 'Active' ? 'desactivar' : 'activar';
    if (window.confirm(`¿Estás seguro de que quieres ${action} este usuario?`)) {
      try {
        await axios.put(`${API}/auth/users/${userId}/toggle-status`);
        fetchUsers(); // Recargar lista
        alert(`Usuario ${action === 'desactivar' ? 'desactivado' : 'activado'} exitosamente`);
      } catch (error) {
        console.error("Error toggling user status:", error);
        alert("Error al cambiar estado del usuario: " + (error.response?.data?.detail || "Error desconocido"));
      }
    }
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
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Gestión de Usuarios</h1>
            <p className="text-slate-600">Administra usuarios, roles y permisos del sistema</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            + Nuevo Usuario
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {users.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z"></path>
              </svg>
              <h3 className="text-lg font-medium text-slate-800 mb-2">No hay usuarios registrados</h3>
              <p className="text-slate-600">Crea el primer usuario para comenzar.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Usuario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Rol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Último Acceso
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-slate-800">{user.name}</div>
                          <div className="text-sm text-slate-500">{user.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.role === 'admin' 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {user.role === 'admin' ? 'Administrador' : 'Corredor'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.subscription_status === 'Active' 
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.subscription_status === 'Active' ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        {new Date(user.created_at).toLocaleDateString('es-GT')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => resetPassword(user.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Reset Password
                        </button>
                        <button
                          onClick={() => toggleUserStatus(user.id, user.subscription_status)}
                          className={`${
                            user.subscription_status === 'Active'
                              ? "text-red-600 hover:text-red-900" 
                              : "text-emerald-600 hover:text-emerald-900"
                          }`}
                        >
                          {user.subscription_status === 'Active' ? 'Desactivar' : 'Activar'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal para crear usuario */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-800">Crear Nuevo Usuario</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <form onSubmit={createUser} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Nombre Completo
                  </label>
                  <input
                    type="text"
                    value={newUser.name}
                    onChange={(e) => setNewUser({...newUser, name: e.target.value})}
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
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                    minLength="6"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Rol del Usuario
                  </label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  >
                    <option value="broker">Corredor</option>
                    <option value="admin">Administrador</option>
                  </select>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
                  >
                    Crear Usuario
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
      </div>
    </div>
  );
};

export default UserManagement;