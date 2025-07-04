// src/components/MaletaForm.jsx
import React, { useEffect, useState } from 'react';

export default function MaletaForm({
  id,
  index,
  tipoServicio,
  datosGenerales,
  aplicarGeneral,
  onRemove
}) {
  const [maleta, setMaleta] = useState({
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
    bono: '',
    notas: ''
  });

  useEffect(() => {
    const nuevaMaleta = { ...maleta };
    Object.keys(datosGenerales).forEach((key) => {
      if (aplicarGeneral[key]) {
        nuevaMaleta[key] = datosGenerales[key];
      }
    });
    setMaleta(nuevaMaleta);
  }, [datosGenerales, aplicarGeneral, maleta]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setMaleta({ ...maleta, [name]: value });
  };

  const isHoraVisible = tipoServicio === 'medioDia';

  return (
    <div className="border p-4 rounded bg-white shadow mb-4" key={id}>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-semibold text-primary">Maleta {index}</h3>
        <button
          type="button"
          onClick={onRemove}
          className="text-red-600 hover:text-red-800 text-sm"
        >
          ✖ Eliminar
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(maleta).map(([key, value]) => {
          if (['bono', 'notas'].includes(key)) return null; // se colocan aparte

          const label = key.replace(/([A-Z])/g, ' $1');
          const type = key.includes('fecha')
            ? 'date'
            : key.includes('hora')
            ? 'time'
            : 'text';

          const shouldShow =
            !(key.includes('hora') && !isHoraVisible);

          return shouldShow ? (
            <div key={key} className="flex flex-col">
              <label className="text-sm text-gray-600 mb-1 capitalize">
                {label}
              </label>
              <input
                name={key}
                type={type}
                value={value}
                onChange={handleChange}
                className="border rounded px-3 py-2"
              />
            </div>
          ) : null;
        })}

        <div className="flex flex-col md:col-span-2">
          <label className="text-sm text-gray-600 mb-1">Bono</label>
          <input
            name="bono"
            type="text"
            value={maleta.bono}
            onChange={handleChange}
            className="border rounded px-3 py-2"
          />
        </div>

        <div className="flex flex-col md:col-span-2">
          <label className="text-sm text-gray-600 mb-1">Notas</label>
          <textarea
            name="notas"
            value={maleta.notas}
            onChange={handleChange}
            rows="2"
            className="border rounded px-3 py-2"
          ></textarea>
        </div>
      </div>
    </div>
  );
}
