import React from 'react';

export default function ResumenPedido({ maletas, tipoServicio }) {
  const total = maletas.reduce(
    (acc, m) => ({
      pax: acc.pax + (parseInt(m.pax) || 0),
      emisores: acc.emisores + (parseInt(m.emisores) || 0)
    }), { pax: 0, emisores: 0 }
  );
  const textoTipo = { medioDia: 'Medio día', diaCompleto: 'Día completo', circuito: 'Circuito' }[tipoServicio] || tipoServicio;

  return (
    <div className="my-6 p-4 bg-gray-50 border rounded shadow-inner">
      <h3 className="text-lg font-semibold mb-2 text-indigo-600">Resumen del pedido:</h3>
      <ul className="text-sm text-gray-800 space-y-1">
        {maletas.map((m, i) => {
          const fecha = m.fechaInicio ? new Date(m.fechaInicio) : null;
          const fechaStr = fecha ? `${fecha.getDate()}/${fecha.getMonth()+1}` : '–';
          return (
            <li key={i}>
              {`Maleta ${i+1}: ${fechaStr} desde: ${m.entrega||'–'}, excursión: ${m.excursion||'–'}, ${m.pax||0} pax (${m.emisores||0} emis) por ${m.guia||'–'}`}
            </li>
          );
        })}
        <li className="mt-3 font-semibold text-indigo-700">Total de pax: {total.pax} | {total.emisores} emisores</li>
        <li className="mt-3 font-semibold text-indigo-700">Tipo de servicio: {textoTipo}</li>
      </ul>
    </div>
  );
}

