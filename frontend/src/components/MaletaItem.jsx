import { useEffect } from 'react';
import classNames from 'classnames';

export default function MaletaItem({ id, tipoServicio, generales, onUpdate, onRemove }) {
  const campos = [
    { id: 'grupo', label: 'Grupo', type: 'text', required: false },
    { id: 'excursion', label: 'Excursión', type: 'text', required: true },
    { id: 'entrega', label: 'Lugar entrega', type: 'text', required: true },
    { id: 'recogida', label: 'Lugar recogida', type: 'text', required: false },
    { id: 'fechaInicio', label: 'Fecha inicio', type: 'date', required: true },
    { id: 'fechaFin', label: 'Fecha fin', type: 'date', required: false },
    { id: 'horaInicio', label: 'Hora inicio', type: 'time', required: false },
    { id: 'horaFin', label: 'Hora fin', type: 'time', required: false },
    { id: 'guia', label: 'Guía', type: 'text', required: true },
    { id: 'pax', label: 'Pax', type: 'number', required: true },
    { id: 'emisores', label: 'Emisores', type: 'number', required: true },
    { id: 'bono', label: 'Bono', type: 'text', required: false },
  ];

  useEffect(() => {
    // aplicar sincronización de campos generales
    Object.keys(generales).forEach(key => {
      if (generales[key].enabled) {
        onUpdate(id, key, generales[key].value);
      }
    });
  }, [generales, id, onUpdate]);

  return (
    <div className="mb-4 p-4 border border-gray-200 rounded-lg bg-gray-50 animate-pop relative" data-id={id}>
      <button
        type="button"
        className="absolute top-2 right-2 text-red-500 hover:text-red-700 text-sm"
        onClick={() => onRemove(id)}
      >✕</button>
      <h3 className="font-semibold text-indigo-700 mb-3">Maleta {id}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {campos.map(c => {
          const hiddenTime = ['diaCompleto', 'circuito'].includes(tipoServicio) && (c.id === 'horaInicio' || c.id === 'horaFin');
          return (
            <div key={c.id} className={classNames({ 'hidden': hiddenTime })}>
              <label className="block text-gray-700 mb-1">
                {c.label}
                {c.required && <span className="text-red-500"> *</span>}
              </label>
              <input
                type={c.type}
                className="input-general w-full px-3 py-2 border rounded shadow-input"
                required={c.required}
                name={`maleta-${id}-${c.id}`}
                onChange={(e) => onUpdate(id, c.id, e.target.value)}
              />
            </div>
          );
        })}
        <div>
          <label className="block text-gray-700 mb-1">Notas</label>
          <textarea
            className="input-general w-full px-3 py-2 border rounded shadow-input resize-none h-8"
            name={`maleta-${id}-notas`}
            onChange={e => onUpdate(id, 'notas', e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

