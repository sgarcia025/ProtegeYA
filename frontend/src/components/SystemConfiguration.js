import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SystemConfiguration = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState(""); // 'success' or 'error'
  const { isAdmin } = useAuth();

  const [formData, setFormData] = useState({
    ultramsg_instance_id: "",
    ultramsg_token: "",
    ultramsg_webhook_secret: "",
    openai_api_key: "",
    use_emergent_llm: true,
    whatsapp_enabled: false,
    ai_chat_prompt: ""
  });

  // Test message form data
  const [testForm, setTestForm] = useState({
    phone_number: "+502",
    message: "🔧 Mensaje de prueba de ProtegeYa - Configuración exitosa ✅"
  });

  const [testSending, setTestSending] = useState(false);
  const [syncingBrokers, setSyncingBrokers] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [fixingLeads, setFixingLeads] = useState(false);
  const [fixResult, setFixResult] = useState(null);

  useEffect(() => {
    if (isAdmin) {
      fetchConfiguration();
    }
  }, [isAdmin]);

  const fetchConfiguration = async () => {
    try {
      const response = await axios.get(`${API}/admin/configuration`);
      setConfig(response.data);
      setFormData({
        ultramsg_instance_id: response.data.ultramsg_instance_id || "",
        ultramsg_token: response.data.ultramsg_token || "",
        ultramsg_webhook_secret: response.data.ultramsg_webhook_secret || "",
        openai_api_key: response.data.openai_api_key || "",
        use_emergent_llm: response.data.use_emergent_llm ?? true,
        whatsapp_enabled: response.data.whatsapp_enabled ?? false,
        ai_chat_prompt: response.data.ai_chat_prompt || ""
      });
    } catch (error) {
      console.error("Error fetching configuration:", error);
      showMessage("Error al cargar configuración", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      await axios.put(`${API}/admin/configuration`, formData);
      showMessage("Configuración actualizada exitosamente", "success");
      fetchConfiguration(); // Reload config
    } catch (error) {
      console.error("Error updating configuration:", error);
      showMessage("Error al actualizar configuración", "error");
    } finally {
      setSaving(false);
    }
  };

  const showMessage = (text, type) => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => {
      setMessage("");
      setMessageType("");
    }, 5000);
  };

  const testWhatsAppConnection = async () => {
    try {
      setTestSending(true);
      
      // Validate phone number
      if (!testForm.phone_number || testForm.phone_number.length < 8) {
        showMessage("Por favor ingresa un número de teléfono válido", "error");
        return;
      }

      // Validate message
      if (!testForm.message.trim()) {
        showMessage("Por favor ingresa un mensaje de prueba", "error");
        return;
      }
      
      const response = await axios.post(`${API}/whatsapp/send`, {
        phone_number: testForm.phone_number,
        message: testForm.message
      });
      
      if (response.data.success) {
        showMessage(`Mensaje enviado exitosamente a ${testForm.phone_number}`, "success");
      } else {
        showMessage("Error al enviar mensaje de prueba", "error");
      }
    } catch (error) {
      console.error("Error testing WhatsApp:", error);
      showMessage("Error en prueba de WhatsApp: " + (error.response?.data?.detail || "Error desconocido"), "error");
    } finally {
      setTestSending(false);
    }
  };

  const syncBrokerUsers = async () => {
    if (!window.confirm("¿Estás seguro de que deseas sincronizar los usuarios de brokers? Esto creará usuarios faltantes y regenerará contraseñas si es necesario.")) {
      return;
    }

    try {
      setSyncingBrokers(true);
      setSyncResult(null);
      
      const response = await axios.post(`${API}/admin/sync-broker-users`);
      
      if (response.data.success) {
        setSyncResult(response.data.results);
        const { users_created, passwords_fixed } = response.data.results;
        
        if (users_created > 0 || passwords_fixed > 0) {
          showMessage(
            `Sincronización completada: ${users_created} usuario(s) creado(s), ${passwords_fixed} contraseña(s) reparada(s)`,
            "success"
          );
        } else {
          showMessage("Todos los brokers ya estaban sincronizados correctamente", "success");
        }
      }
    } catch (error) {
      console.error("Error syncing brokers:", error);
      showMessage("Error al sincronizar brokers: " + (error.response?.data?.detail || "Error desconocido"), "error");
    } finally {
      setSyncingBrokers(false);
    }
  };

  const fixBrokerLeads = async () => {
    if (!window.confirm("¿Deseas diagnosticar y reparar automáticamente los leads de brokers? Esto reasignará leads huérfanos y verificará la configuración.")) {
      return;
    }

    try {
      setFixingLeads(true);
      setFixResult(null);
      
      const response = await axios.post(`${API}/admin/fix-broker-leads`);
      
      if (response.data.success) {
        setFixResult(response.data.results);
        const fixCount = response.data.results.fixes_applied.length;
        
        if (fixCount > 0) {
          showMessage(`Reparación completada: ${fixCount} corrección(es) aplicada(s)`, "success");
        } else {
          showMessage("No se encontraron problemas. Todo está correcto.", "success");
        }
      }
    } catch (error) {
      console.error("Error fixing broker leads:", error);
      showMessage("Error al reparar leads: " + (error.response?.data?.detail || "Error desconocido"), "error");
    } finally {
      setFixingLeads(false);
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
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Configuración del Sistema</h1>
          <p className="text-slate-600">Gestiona las integraciones de WhatsApp, OpenAI y otras configuraciones</p>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            messageType === 'success' 
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' 
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}>
            <div className="flex items-center">
              {messageType === 'success' ? (
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                </svg>
              ) : (
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                </svg>
              )}
              {message}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* WhatsApp Configuration */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-green-100 rounded-lg mr-4">
                <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.886 3.75"/>
                </svg>
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-slate-800">Configuración WhatsApp (UltraMSG)</h2>
                <p className="text-slate-600">Configura la integración con UltraMSG para mensajería WhatsApp</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Instance ID
                </label>
                <input
                  type="text"
                  value={formData.ultramsg_instance_id}
                  onChange={(e) => setFormData({...formData, ultramsg_instance_id: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="instance123456"
                />
                <p className="text-xs text-slate-500 mt-1">ID de instancia de UltraMSG</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Token API
                </label>
                <input
                  type="password"
                  value={formData.ultramsg_token}
                  onChange={(e) => setFormData({...formData, ultramsg_token: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="your-ultramsg-token"
                />
                <p className="text-xs text-slate-500 mt-1">Token de autenticación de UltraMSG</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Webhook Secret
                </label>
                <input
                  type="password"
                  value={formData.ultramsg_webhook_secret}
                  onChange={(e) => setFormData({...formData, ultramsg_webhook_secret: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="webhook-secret"
                />
                <p className="text-xs text-slate-500 mt-1">Secret para validar webhooks (opcional)</p>
              </div>

              <div className="flex items-center">
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.whatsapp_enabled}
                      onChange={(e) => setFormData({...formData, whatsapp_enabled: e.target.checked})}
                      className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                    />
                    <span className="ml-2 text-sm font-medium text-slate-700">
                      Habilitar WhatsApp
                    </span>
                  </label>
                  <p className="text-xs text-slate-500 mt-1">Activar envío de mensajes por WhatsApp</p>
                </div>
              </div>
            </div>

            {formData.whatsapp_enabled && (
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="text-lg font-semibold text-green-800 mb-4">
                  🧪 Prueba de Mensajería WhatsApp
                </h3>
                <p className="text-sm text-green-700 mb-4">
                  Envía un mensaje de prueba para verificar que la integración con UltraMSG funciona correctamente.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-green-700 mb-2">
                      Número de WhatsApp
                    </label>
                    <input
                      type="tel"
                      value={testForm.phone_number}
                      onChange={(e) => setTestForm({...testForm, phone_number: e.target.value})}
                      className="w-full px-3 py-2 border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      placeholder="+50212345678"
                    />
                    <p className="text-xs text-green-600 mt-1">
                      Incluye el código de país de Guatemala (+502)
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-green-700 mb-2">
                      Estado de Conexión
                    </label>
                    <div className="flex items-center px-3 py-2 bg-white border border-green-300 rounded-lg">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                      <span className="text-sm text-green-700">
                        {formData.ultramsg_instance_id ? `Conectado (${formData.ultramsg_instance_id})` : 'Sin configurar'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-green-700 mb-2">
                    Mensaje de Prueba
                  </label>
                  <textarea
                    value={testForm.message}
                    onChange={(e) => setTestForm({...testForm, message: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Escribe tu mensaje de prueba aquí..."
                  />
                  <p className="text-xs text-green-600 mt-1">
                    Máximo 1000 caracteres. Puedes usar emojis 😊
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-xs text-green-600">
                    <p>✅ Se enviará usando la configuración actual de UltraMSG</p>
                    <p>📱 El mensaje aparecerá desde tu instancia de WhatsApp Business</p>
                  </div>
                  
                  <button
                    type="button"
                    onClick={testWhatsAppConnection}
                    disabled={testSending || !formData.ultramsg_instance_id || !formData.ultramsg_token || !testForm.phone_number || !testForm.message.trim()}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center"
                  >
                    {testSending ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Enviando...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                        </svg>
                        Enviar Mensaje
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* AI Configuration */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-blue-100 rounded-lg mr-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                </svg>
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-slate-800">Configuración de Inteligencia Artificial</h2>
                <p className="text-slate-600">Gestiona las claves API para OpenAI y configuración de IA</p>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <label className="flex items-center mb-4">
                  <input
                    type="radio"
                    name="ai_provider"
                    checked={formData.use_emergent_llm}
                    onChange={(e) => setFormData({...formData, use_emergent_llm: true})}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="ml-2 text-sm font-medium text-slate-700">
                    Usar Emergent LLM Key (Recomendado)
                  </span>
                </label>
                <div className="ml-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <div className="flex items-start">
                    <svg className="w-5 h-5 text-emerald-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                    </svg>
                    <div>
                      <p className="text-sm text-emerald-700">
                        <strong>Emergent LLM Key configurada:</strong> Acceso a GPT-4o + Whisper incluido.
                      </p>
                      <p className="text-xs text-emerald-600 mt-1">
                        No necesitas configurar claves adicionales. El sistema usa la clave universal de Emergent.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label className="flex items-center mb-4">
                  <input
                    type="radio"
                    name="ai_provider"
                    checked={!formData.use_emergent_llm}
                    onChange={(e) => setFormData({...formData, use_emergent_llm: false})}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="ml-2 text-sm font-medium text-slate-700">
                    Usar OpenAI API Key Personal
                  </span>
                </label>

                {!formData.use_emergent_llm && (
                  <div className="ml-6">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      OpenAI API Key
                    </label>
                    <input
                      type="password"
                      value={formData.openai_api_key}
                      onChange={(e) => setFormData({...formData, openai_api_key: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      placeholder="sk-..."
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Tu clave API personal de OpenAI para GPT y Whisper
                    </p>
                  </div>
                )}
              </div>

              {/* Custom AI Prompt Section */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="text-lg font-semibold text-blue-800 mb-3">
                  🤖 Personalizar Prompt de IA
                </h4>
                <p className="text-sm text-blue-700 mb-3">
                  Personaliza las instrucciones que recibe la IA para interactuar con los clientes via WhatsApp.
                </p>
                
                <div>
                  <label className="block text-sm font-medium text-blue-700 mb-2">
                    Prompt Personalizado del ChatBot
                  </label>
                  <textarea
                    value={formData.ai_chat_prompt}
                    onChange={(e) => setFormData({...formData, ai_chat_prompt: e.target.value})}
                    rows={8}
                    className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Ejemplo de prompt completo con cotización y PDF:

Eres María, asistente virtual de ProtegeYa 🇬🇹 

PROCESO COMPLETO:
1. Saludar amigablemente y preguntar por seguro vehicular
2. Recopilar: marca, modelo, año, valor en GTQ, municipio
3. CUANDO TENGAS TODOS LOS DATOS → GENERAR_COTIZACION:{marca},{modelo},{año},{valor},{municipio}
4. Mostrar cotizaciones disponibles con precios mensuales
5. Preguntar cuál aseguradora y tipo de seguro le interesa
6. CUANDO SELECCIONEN → SELECCIONAR_ASEGURADORA:{nombre_aseguradora},{tipo_seguro},{precio_mensual}

Ejemplos de respuestas especiales:
- 'GENERAR_COTIZACION:Toyota,Corolla,2020,150000,Guatemala'
- 'SELECCIONAR_ASEGURADORA:Seguros El Roble,Seguro Completo,1250.00'

IMPORTANTE:
- Sé amigable y usa emojis guatemaltecos 🚗💙🇬🇹
- Usa 'vos' y frases chapinas
- Explica que somos comparadores, no vendemos seguros
- Los precios son indicativos, confirmás con un corredor
- Después de seleccionar, se envía PDF automático con detalles

¡Sé súper eficiente y 100% chapín! 🇬🇹"
                  />
                  <p className="text-xs text-blue-600 mt-1">
                    Deja vacío para usar el prompt predeterminado. Máximo 2000 caracteres.
                  </p>
                </div>

                <div className="mt-3 p-3 bg-blue-100 rounded-lg">
                  <p className="text-xs text-blue-700">
                    <strong>💡 Tip:</strong> Incluye instrucciones sobre el tono, idioma, información a recopilar, 
                    y cómo manejar diferentes tipos de consultas de seguros vehiculares.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-purple-100 rounded-lg mr-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-slate-800">Estado del Sistema</h2>
                <p className="text-slate-600">Estado actual de las integraciones y servicios</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border border-slate-200 rounded-lg">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    formData.whatsapp_enabled ? 'bg-emerald-500' : 'bg-slate-400'
                  }`}></div>
                  <div>
                    <p className="font-medium text-slate-800">WhatsApp</p>
                    <p className="text-sm text-slate-600">
                      {formData.whatsapp_enabled ? 'Activo' : 'Inactivo'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 border border-slate-200 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-emerald-500 rounded-full mr-3"></div>
                  <div>
                    <p className="font-medium text-slate-800">IA Chat</p>
                    <p className="text-sm text-slate-600">
                      {formData.use_emergent_llm ? 'Emergent LLM' : 'OpenAI Personal'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 border border-slate-200 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-emerald-500 rounded-full mr-3"></div>
                  <div>
                    <p className="font-medium text-slate-800">Base de Datos</p>
                    <p className="text-sm text-slate-600">Conectada</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              {saving ? "Guardando..." : "Guardar Configuración"}
            </button>
          </div>
        </form>

        {/* System Maintenance Section */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-slate-200">
            <h2 className="text-xl font-bold text-slate-800">🔧 Mantenimiento del Sistema</h2>
            <p className="text-slate-600 text-sm mt-1">Herramientas de diagnóstico y reparación</p>
          </div>
          
          <div className="p-6">
            {/* Broker Leads Fix Section */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex items-start">
                <svg className="w-6 h-6 text-red-600 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-red-800 mb-1">
                    🔧 Diagnóstico y Reparación de Leads
                  </h3>
                  <p className="text-sm text-red-700 mb-3">
                    <strong>ÚSALO SI:</strong> Los brokers no ven sus leads asignados aunque tú sí los ves en el admin dashboard.
                    Este proceso diagnostica automáticamente y repara problemas de asignación.
                  </p>
                  <button
                    onClick={fixBrokerLeads}
                    disabled={fixingLeads}
                    className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors inline-flex items-center"
                  >
                    {fixingLeads ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Diagnosticando...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Diagnosticar y Reparar
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Broker Sync Section */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex items-start">
                <svg className="w-6 h-6 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-yellow-800 mb-1">
                    Sincronización de Usuarios de Brokers
                  </h3>
                  <p className="text-sm text-yellow-700 mb-3">
                    Si los brokers no pueden ver sus leads asignados o no pueden hacer login, ejecuta esta sincronización. 
                    Creará usuarios faltantes y reparará contraseñas corruptas.
                  </p>
                  <button
                    onClick={syncBrokerUsers}
                    disabled={syncingBrokers}
                    className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors inline-flex items-center"
                  >
                    {syncingBrokers ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Sincronizando...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Sincronizar Brokers
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Sync Results */}
            {syncResult && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <h4 className="font-semibold text-slate-800 mb-3">Resultados de Sincronización</h4>
                
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-2xl font-bold text-emerald-600">{syncResult.brokers_checked}</div>
                    <div className="text-xs text-slate-600">Brokers revisados</div>
                  </div>
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-2xl font-bold text-blue-600">{syncResult.users_created}</div>
                    <div className="text-xs text-slate-600">Usuarios creados</div>
                  </div>
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-2xl font-bold text-orange-600">{syncResult.passwords_fixed}</div>
                    <div className="text-xs text-slate-600">Contraseñas reparadas</div>
                  </div>
                </div>

                <div className="space-y-2">
                  {syncResult.brokers.map((broker, index) => (
                    <div key={index} className="bg-white p-3 rounded border border-slate-200">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-slate-800">{broker.name}</div>
                          <div className="text-sm text-slate-600">{broker.email}</div>
                          <div className="text-xs text-slate-500 mt-1">
                            Leads asignados: {broker.leads_assigned}
                          </div>
                        </div>
                        <div>
                          {broker.status === 'ok' && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                              ✓ OK
                            </span>
                          )}
                          {broker.status === 'user_created' && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              ✨ Usuario creado
                            </span>
                          )}
                          {broker.status === 'password_fixed' && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                              🔧 Password reparado
                            </span>
                          )}
                          {broker.status === 'error' && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              ❌ Error
                            </span>
                          )}
                        </div>
                      </div>
                      {broker.temp_password && (
                        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm">
                          <strong>⚠️ Contraseña temporal:</strong> <code className="bg-yellow-100 px-2 py-0.5 rounded">{broker.temp_password}</code>
                          <div className="text-xs text-yellow-700 mt-1">El broker debe cambiarla al hacer login</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {syncResult.errors.length > 0 && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded p-3">
                    <div className="font-semibold text-red-800 mb-2">Errores encontrados:</div>
                    {syncResult.errors.map((error, index) => (
                      <div key={index} className="text-sm text-red-700">
                        • {error.broker}: {error.error}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemConfiguration;