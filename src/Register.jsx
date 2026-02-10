import { useForm } from "react-hook-form";
import axios from "axios";

const BASE_URL = "https://mock.apidog.com/m1/1194510-1189388-1071073";

export default function Register() {
  const { register, handleSubmit } = useForm();

  const onSubmit = async (data) => {
    try {
      const response = await axios.post(`${BASE_URL}/auth/register`, data);
      console.log("Registration Success:", response.data);
      alert("Account created successfully! You can now log in.");
    } catch (error) {
      console.error("Registration Error:", error.response?.data || error.message);
      alert("Registration failed.");
    }
  };

  return (
    <div className="auth-container">
      <h2>Register</h2>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input {...register("username")} placeholder="Username" required />
        <input {...register("email")} type="email" placeholder="Email" required />
        <input {...register("password")} type="password" placeholder="Password" required />
        <button type="submit">Create Account</button>
      </form>
    </div>
  );
}
