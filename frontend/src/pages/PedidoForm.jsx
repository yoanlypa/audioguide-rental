import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../api';
import ToggleIOS from './ToggleIOS';
import MaletaForm from './MaletaForm';

export default function PedidoForm() {
  const {
    register,
    handleSubmit,
    getValues,
  } = useForm();

  const [tipoServicio, setTipoServicio] = useState('medioDia');
  const [maletas, setMaletas] = useState([{ id: 1 }]);
  const [aplicarGeneral, setAplicarGeneral] = useState({
    grupo: false,
    excursion: false,
    lugarEntrega: false,
    lugarRecogida: false,
    fechaInicio: false,
    fechaFin: false,
    horaInicio: false,
    horaFin: false,
    guia: false,
    pax: false,
    emisores: false,
  });

  const toggleAplicarGeneral = (field) => {
    setAplicarGeneral((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const addMaleta = () => {
    const nuevaId = maletas.length + 1;
    setMaletas([...maletas, { id: nuevaId }]);
  };

  const removeMaleta = (id) => {
    const nuevas = maletas.filter((m) => m.id !== id);
    setMaletas(nuevas);
  };

  const onSubmit = async (data) => {
    try {
      const payload = {
        ...data,
        tipoServicio,
        maletas: maletas.map((m, i) => ({
          ...getValues(`maletas[${i}]`),
        })),
      };
      await api.post('/api/pedidos/', payload);
      alert('Pedido guardado exitosamente');
    } catch (err) {
      console.error('Error al guardar:', err);
    }
  };

  const onError = (errors) => {
    console.warn('Errores de validación:', errors);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit, onError)} className="space-y-6">
      <div className="bg-gray-50 p-4 rounded-lg border">
        <h2 className="text-lg font-semibold text-primary mb-2">Datos generales</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.keys(aplicarGeneral).map((key) => (
            <div key={key} className="flex flex-col">
              <label className="text-sm text-gray-700 mb-1 capitalize">
                {key.replace(/([A-Z])/g, ' $1')}
              </label>
              <div className="flex items-center gap-2">
                <input
                  type={key.includes('fecha') ? 'date' : key.includes('hora') ? 'time' : 'text'}
                  {...register(`datosGenerales.${key}`)}
                  className="flex-1 px-3 py-2 border rounded input-general"
                />
                <ToggleIOS
                  checked={aplicarGeneral[key]}
                  onChange={() => toggleAplicarGeneral(key)}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg border">
        <div className="flex gap-2 mb-4">
          {['medioDia', 'diaCompleto', 'circuito'].map((tipo) => (
            <button
              key={tipo}
              type="button"
              className={`tab-btn px-4 py-2 rounded font-medium border ${
                tipoServicio === tipo ? 'bg-primary text-white' : 'bg-gray-200'
              }`}
              onClick={() => setTipoServicio(tipo)}
            >
              {tipo === 'medioDia'
                ? 'Medio Día'
                : tipo === 'diaCompleto'
                ? 'Día Completo'
                : 'Circuito'}
            </button>
          ))}
        </div>

        <div id="maletasContainer" className="flex flex-col gap-4">
          {maletas.map((maleta, i) => (
            <MaletaForm
              key={maleta.id}
              index={i}
              tipoServicio={tipoServicio}
              aplicarGeneral={aplicarGeneral}
              register={register}
              datosGenerales={getValues('datosGenerales')}
              onRemove={() => removeMaleta(maleta.id)}
            />
          ))}
        </div>

        <button
          type="button"
          onClick={addMaleta}
          className="mt-4 bg-secondary text-white px-4 py-2 rounded shadow hover:bg-orange-500"
        >
          ➕ Añadir maleta
        </button>
      </div>

      <div id="resumenLista" className="bg-gray-50 p-4 border rounded">
        <h3 className="font-semibold text-indigo-700">Resumen dinámico</h3>
        {/* Aquí puedes añadir un componente de resumen */}
      </div>

      <button
        type="submit"
        className="bg-primary text-white px-6 py-2 rounded hover:bg-blue-700"
      >
        Guardar pedido
      </button>
    </form>
  );
}
