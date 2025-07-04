import { useState } from 'react';
import classNames from 'classnames';

export default function DatosGenerales({ syncState, onChange }) {
  const [open, setOpen] = useState(false);
  const toggle = () => setOpen(o => !o);

  // syncState: { campo: { enabled, value } }
  const campos = [
    { id: 'grupo', label: 'Grupo', type: 'text' },
    { id: 'excursion', label: 'Excursión', type: 'text' },
    { id: 'entrega', label: 'Lugar entrega', type: 'text' },
    { id: 'recogida', label: 'Lugar recogida', type: 'text' },
    { id: 'fechaInicio', label: 'Fecha inicio', type: 'date' },
    { id: 'fechaFin', label: 'Fecha fin', type: 'date' },
    { id: 'horaInicio', label: 'Hora inicio', type: 'time' },
    { id: 'horaFin', label: 'Hora fin', type: 'time' },
    { id: 'guia', label: 'Guía', type: 'text' },
    { id: 'pax', label: 'Pax', type: 'number' },
    { id: 'emisores', label: 'Emisores', type: 'number' },
  ];

  return (
    <div className="mb-6 p-4 bg-indigo-50 rounded-lg">
      <button
        type="button"
        className="w-full flex justify-between items-center px-4 py-2 bg-indigo-100 text-indigo-800 font-semibold rounded hover:bg-indigo-200 transition"
        onClick={toggle}
      >
        Datos Generales (sincronización opcional)
        <svg
          className={classNames('w-5 h-5 transform transition-transform duration-300', { 'rotate-180': open })}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div className={classNames('grid grid-cols-1 mt-4 p-4 md:grid-cols-2 gap-4 transition-all duration-300', { 'hidden': !open })}>
        {campos.map(c => (
          <div key={c.id}>
            <label htmlFor={c.id} className="flex items-center justify-between gap-4 text-sm text-gray-700 w-full">
              <span>{c.label}</span>
              <div className="relative">
                <input
                  type="checkbox"
                  id={c.id}
                  checked={syncState[c.id]?.enabled || false}
                  onChange={e => onChange(c.id, { enabled: e.target.checked, value: syncState[c.id]?.value || '' })}
                  className="sr-only peer"
                />
                <div className="w-10 h-5 bg-gray-300 rounded-full peer-checked:bg-[#005dab] transition-colors duration-300" />
                <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-300 peer-checked:translate-x-[1.25rem] shadow-md" />
              </div>
            </label>
            <input
              type={c.type}
              name={c.id}
              className={classNames('input-general w-full px-3 py-2 border rounded', {
                'campo-sincronizado': syncState[c.id]?.enabled
              })}
              value={syncState[c.id]?.value || ''}
              onChange={e => onChange(c.id, { enabled: syncState[c.id]?.enabled || false, value: e.target.value })}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
