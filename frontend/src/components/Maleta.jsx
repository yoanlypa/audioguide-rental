import { useEffect } from "react";

export default function Maleta({
  index,
  data,
  tipoServicio,
  onChange,
  onRemove,
  datosGenerales
}) {
  useEffect(() => {
    if (tipoServicio === "medioDia") {
      onChange(index, { horaInicioRequired: true, horaFinRequired: true });
    } else {
      onChange(index, { horaInicio: "", horaFin: "", horaInicioRequired: false, horaFinRequired: false });
    }
  }, [tipoServicio, index, onChange]);

  useEffect(() => {
    onChange(index, datosGenerales);
  }, [datosGenerales, index, onChange]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    onChange(index, { [name]: value });
  };

  return (
    <div className="mb-4 p-4 border border-gray-200 rounded-lg bg-gray-50 relative animate-pop">
      <button
        type="button"
        onClick={() => onRemove(index)}
        className="absolute top-2 right-2 text-red-500 hover:text-red-700 text-sm"
      >
        ✕
      </button>
      <h3 className="font-semibold text-indigo-700 mb-3">Maleta <span className="maleta-num">{index + 1}</span></h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <input type="hidden" name="tipoServicio" value={tipoServicio} />
        {[
          { label: "Grupo", name: "grupo", required: false },
          { label: "Excursión", name: "excursion", required: true },
          { label: "Lugar entrega", name: "lugarEntrega", required: true },
          { label: "Lugar recogida", name: "lugarRecogida", required: false },
          { label: "Fecha inicio", name: "fechaInicio", type: "date", required: true },
          { label: "Fecha fin", name: "fechaFin", type: "date", required: false },
          { label: "Guía", name: "guia", required: true },
          { label: "Pax", name: "pax", type: "number", required: true },
          { label: "Emisores", name: "emisores", type: "number", required: true },
          { label: "Bono", name: "bono", required: false },
        ].map((field) => (
          <div key={field.name}>
            <label>{field.label}</label>
            <input
              name={field.name}
              type={field.type || "text"}
              value={data[field.name] || ""}
              onChange={handleInputChange}
              required={field.required}
              className="w-full px-3 py-2 border rounded"
            />
          </div>
        ))}

        {tipoServicio === "medioDia" && (
          <>
            <div>
              <label>Hora inicio</label>
              <input
                type="time"
                name="horaInicio"
                value={data.horaInicio || ""}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label>Hora fin</label>
              <input
                type="time"
                name="horaFin"
                value={data.horaFin || ""}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border rounded"
              />
            </div>
          </>
        )}

        <div className="md:col-span-2">
          <label>Notas</label>
          <textarea
            name="notas"
            rows="1"
            value={data.notas || ""}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border rounded"
            placeholder="Añade alguna observación sobre esta maleta..."
          />
        </div>
      </div>
    </div>
  );
}