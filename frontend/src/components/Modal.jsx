import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import classNames from 'classnames';

export default function Modal({ isOpen, onClose, children }) {
  useEffect(() => {
    const onEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onEsc);
    return () => document.removeEventListener('keydown', onEsc);
  }, [onClose]);

  if (!isOpen) return null;

  return ReactDOM.createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Fondo semitransparente */}
      <div
        className="absolute inset-0 bg-black opacity-50"
        onClick={onClose}
      />
      {/* Contenido del modal */}
      <div
        className={classNames(
          'relative bg-white rounded-2xl shadow-lg max-w-4xl w-full mx-4 p-6 overflow-auto',
          'max-h-[90vh]'
        )}
      >
        <button
          className="absolute top-4 right-4 text-gray-600 hover:text-gray-800"
          onClick={onClose}
          aria-label="Cerrar modal"
        >
          ✕
        </button>
        {children}
      </div>
    </div>,
    document.body
  );
}
