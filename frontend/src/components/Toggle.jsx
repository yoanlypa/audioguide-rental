export default function Toggle({ id, checked, onChange }) {
  return (
    <label htmlFor={id} className="relative inline-block w-11 h-6 cursor-pointer">
      <input
        type="checkbox"
        id={id}
        className="sr-only peer"
        checked={checked}
        onChange={onChange}
      />
      <div className="bg-gray-300 rounded-full w-full h-full peer-checked:bg-primary transition duration-200"></div>
      <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transform peer-checked:translate-x-5 transition duration-200"></div>
    </label>
  );
}