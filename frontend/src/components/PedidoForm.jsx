// src/components/PedidoForm.jsx
import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../services/api.js';
import MaletaForm from './MaletaForm';
import Toggle from './Toggle';

export default function PedidoForm() {
  const { handleSubmit } = useForm();
  const [tipoServicio, setTipoServicio] = useState('medioDia');
  const [maletas, setMaletas] = useState([]);
  const [datosGenerales, setDatosGenerales] = useState({
    grupo: '',
    excursion: '',
    lugarEntrega: '',
    lugarRecogida: '',
    fechaInicio: '',
    fechaFin: '',
    horaInicio: '',
    horaFin: '',
    guia: '',
    pax: '',
    emisores: '',
  });
  const [aplicarGeneral, setAplicarGeneral] = useState(
    Object.fromEntries(Object.keys(datosGenerales).map(key => [key, false]))
  );

  useEffect(() => {
    setMaletas([{ id: 1 }]);
  }, []);

  const addMaleta = () => {
    const nuevaId = maletas.length ? Math.max(...maletas.map(m => m.id)) + 1 : 1;
    setMaletas([...maletas, { id: nuevaId }]);
  };

  const removeMaleta = (id) => {
    setMaletas(prev => prev.filter(m => m.id !== id));
  };

  const updateDatosGenerales = (field, value) => {
    setDatosGenerales(prev => ({ ...prev, [field]: value }));
  };

  const toggleAplicarGeneral = (field) => {
    setAplicarGeneral(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const onSubmit = async () => {
    const payload = {
      tipoServicio,
      generales: datosGenerales,
      maletas: maletas.map(m => m.datos || {}),
    };
    console.log('Datos enviados:', payload);
    try {
      await api.post('/api/pedidos/', payload);
      alert('Pedido guardado con éxito');
    } catch (error) {
      console.error('Error al guardar:', error);
      alert('Error al guardar el pedido');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 p-4 max-w-5xl mx-auto">
      <div className="bg-gray-100 p-4 rounded shadow">
        <h2 className="text-xl font-bold mb-4 text-blue-700">Datos Generales</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(datosGenerales).map(([key, value]) => (
            <div key={key} className="flex flex-col">
              <label className="capitalize text-sm font-medium">{key.replace(/([A-Z])/g, ' $1')}</label>
              <div className="flex items-center gap-2">
                <input
                  type={key.includes('fecha') ? 'date' : key.includes('hora') ? 'time' : 'text'}
                  value={value}
                  onChange={(e) => updateDatosGenerales(key, e.target.value)}
                  className="flex-1 px-3 py-2 border rounded"
                />
                <Toggle
                  checked={aplicarGeneral[key]}
                  onChange={() => toggleAplicarGeneral(key)}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white p-4 rounded shadow">
        <h3 className="text-lg font-semibold mb-4">Tipo de servicio</h3>
        <div className="flex gap-2 mb-4">
          {['medioDia', 'diaCompleto', 'circuito'].map(tipo => (
            <button
              key={tipo}
              type="button"
              className={`px-4 py-2 rounded border ${
                tipoServicio === tipo ? 'bg-blue-600 text-white' : 'bg-gray-200'
              }`}
              onClick={() => setTipoServicio(tipo)}
            >
              {tipo === 'medioDia' ? 'Medio Día' : tipo === 'diaCompleto' ? 'Día Completo' : 'Circuito'}
            </button>
          ))}
        </div>

        <div className="space-y-4">
          {maletas.map((maleta, i) => (
            <MaletaForm
              key={maleta.id}
              id={maleta.id}
              index={i + 1}
              tipoServicio={tipoServicio}
              datosGenerales={datosGenerales}
              aplicarGeneral={aplicarGeneral}
              onRemove={() => removeMaleta(maleta.id)}
              onChange={(datos) =>
                setMaletas(prev =>
                  prev.map(m => (m.id === maleta.id ? { ...m, datos } : m))
                )
              }
            />
          ))}
        </div>

        <button
          type="button"
          onClick={addMaleta}
          className="mt-4 bg-orange-500 text-white px-4 py-2 rounded"
        >
          ➕ Añadir maleta
        </button>
      </div>

      <div className="text-center">
        <button
          type="submit"
          className="bg-blue-700 text-white px-6 py-2 rounded hover:bg-blue-800"
        >
          Guardar pedido
        </button>
      </div>
    </form>
  );
}
