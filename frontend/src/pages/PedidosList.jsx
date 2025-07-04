import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api.js';
import Modal from '../components/Modal.jsx';
import PedidoForm from '../components/PedidoForm.jsx';

export default function PedidosList() {
  const queryClient = useQueryClient();
  const { data: pedidos = [], isLoading, isError } = useQuery({
    queryKey: ['pedidos'],
    queryFn: async () => (await api.get('/pedidos/')).data,
  });

  const [modalOpen, setModalOpen] = useState(false);
  const addPedido = useMutation({
    mutationFn: newPedido => api.post('/pedidos/', newPedido),
    onSuccess: () => {
      queryClient.invalidateQueries(['pedidos']);
      setModalOpen(false);
    }
  });

  if (isLoading) return <p>Cargando...</p>;
  if (isError) return <p>Error al cargar pedidos</p>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">Mis pedidos</h1>
      <button
        onClick={() => setModalOpen(true)}
        className="fixed bottom-6 right-6 bg-indigo-600 text-white p-4 rounded-full shadow-lg hover:bg-indigo-700 transition"
        aria-label="Nuevo Pedido"
      >
        +
      </button>

      {pedidos.length === 0 ? (
        <p>No tienes pedidos todavía.</p>
      ) : (
        <table className="min-w-full bg-white rounded-2xl shadow">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Fecha</th>
              <th className="px-4 py-2 text-left">Estado</th>
            </tr>
          </thead>
          <tbody>
            {pedidos.map((p) => (
              <tr key={p.id} className="border-t last:border-b-0 hover:bg-blue-50 transition">
                <td className="px-4 py-2">{p.id}</td>
                <td className="px-4 py-2">{new Date(p.fecha).toLocaleDateString()}</td>
                <td className="px-4 py-2">{p.estado}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)}>
        <h2 className="text-2xl font-bold mb-4">Nuevo Pedido</h2>
        <PedidoForm onSubmit={data => addPedido.mutate(data)} />
      </Modal>
    </div>
  );
}
