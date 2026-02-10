import { useForm } from "react-hook-form";
import axios from "axios";

const BASE_URL = "https://mock.apidog.com/m1/1194510-1189388-1071073";

export default function Login() {
  const { register, handleSubmit } = useForm();

  const onSubmit = async (data) => {
    try {
      const response = await axios.post(`${BASE_URL}/auth/login`, data);
      console.log("Login Success:", response.data);
      alert(`Welcome back, ${response.data.user.username}!`);
      localStorage.setItem("token", response.data.token);
    } catch (error) {
      console.error("Login Error:", error.response?.data || error.message);
      alert("Login failed. Check the console for details.");
    }
  };

  return (
    <div className="auth-container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input {...register("email")} type="email" placeholder="Email" required />
        <input {...register("password")} type="password" placeholder="Password" required />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}
