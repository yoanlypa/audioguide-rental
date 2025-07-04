import { useEffect, useState } from 'react';
import api from '../services/api';
import Modal from '../components/Modal.jsx';
import PedidoForm from '../components/PedidoForm.jsx';


    export default function MisPedidos() {
        const [pedidos, setPedidos] = useState([]);
        const [loading, setLoading] = useState(true);
        const [modalOpen, setModalOpen] = useState(false);

        useEffect(() => {
            const fetchPedidos = async () => {
            try {
                const res = await api.get('/mis-pedidos/');
                setPedidos(res.data);
            } catch (err) {
                console.error('Error al obtener pedidos:', err);
            } finally {
                setLoading(false);
            }
            };

            fetchPedidos();
        }, []);

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
            <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)}>
            <PedidoForm onClose={() => setModalOpen(false)} />
            </Modal>
            {loading ? (
                <p>Cargando...</p>
            ) : pedidos.length === 0 ? (
                <p>No tienes pedidos aún.</p>
            ) : (
                <ul className="space-y-4">
                {pedidos.map((pedido) => (
                    <li
                    key={pedido.id}
                    className="border p-4 rounded shadow bg-white hover:shadow-md transition"
                    >
                    <p><strong>Empresa:</strong> {pedido.empresa_nombre}</p>
                    <p><strong>Fecha:</strong> {new Date(pedido.created_at).toLocaleDateString()}</p>
                    <p><strong>Estado:</strong> {pedido.estado}</p>
                    {/* Agrega más campos según el modelo */}
                    </li>
                ))}
                </ul>
            )}
            </div>
        );
        }
