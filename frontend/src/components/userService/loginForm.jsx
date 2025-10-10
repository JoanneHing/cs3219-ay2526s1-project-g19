import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, MessageSquareWarning} from "lucide-react";
import { userService } from "../../api/services/userService";
import { useAuth } from "../../contexts/AuthContext";

const validateEmail = (value, errors) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (value.length === 0) {
        errors.push("Email is required.");
        return errors;
    }

    if (!regex.test(value)) {
        errors.push("Invalid email format.");
    }

    return errors;
};

const validatePassword = (value, errors) => {
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])([A-Za-z\d!@#$%^&*(),.?":{}|<>]){8,}$/;

    if (value.length === 0) {
        errors.push("Password is required.");
        return errors;
    }

    if (regex.test(value) === false) {
        errors.push("Password format is invalid.");
    }

    return errors;
}

const ErrorMessage = ({ errorsArray }) => {
    if (!errorsArray || errorsArray.length === 0) return null;
    return (
        <div className="text-red-500 text-xs mt-1 space-y-0.5">
            {errorsArray.map((err, idx) => (
                <p key={idx}> <MessageSquareWarning className="inline w-3 h-3 mr-1"/> {err}</p>
            ))}
        </div>
    );
}

const LoginForm = () => {
    const navigate = useNavigate();
    const { login } = useAuth();

    const [formData, setFormData] = useState({
        email: "",
        password: ""
    });

    const [error, setError] = useState({
        email: [],
        password: []
    });

    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [loginError, setLoginError] = useState("");
    
    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };

    const inputType = showPassword ? "text" : "password";

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        
        setError(prev => ({ ...prev, [name]: [] }));
    }
    
    const handleBlur = (e) => {
        const { name, value } = e.target;
        
        const fieldErrors = getValidationErrors(name, value);
        setError(prev => ({ ...prev, [name]: fieldErrors }));
    }

    const handleSubmit = async (e) => {
        e.preventDefault();

        const finalErrors = {};
        let isValid = true;

        Object.keys(formData).forEach(name => {
            const fieldErrors = getValidationErrors(name, formData[name]);

            finalErrors[name] = fieldErrors;

            if (fieldErrors.length > 0) {
                isValid = false;
            }
        });

        setError(finalErrors);

        if (isValid) {
            setIsLoading(true);
            setLoginError("");

            try {
                const response = await userService.login({
                    email: formData.email,
                    password: formData.password
                });
                console.log(response)

                // Data is already unwrapped by the interceptor
                const { user, tokens, session_profile } = response.data;

                // Update auth context (this will also store in localStorage)
                login(user, tokens);

                console.log("Login successful:", { user, tokens, session_profile });

                // Navigate to home page
                navigate('/home');

            } catch (err) {
                console.error("Login failed:", err);

                if (err.response?.status === 401) {
                    setLoginError("Invalid email or password");
                } else if (err.response?.status === 403) {
                    setLoginError("Account is disabled");
                } else if (err.response?.status === 429) {
                    setLoginError("Too many failed login attempts. Please try again later");
                } else if (err.response?.status === 400) {
                    setLoginError("Invalid input data");
                } else {
                    setLoginError("An error occurred. Please try again");
                }
            } finally {
                setIsLoading(false);
            }
        } else {
            console.log("Validation errors.");
        }
    }

    const getValidationErrors = (name, value) => {
        const errors = [];
        if (name === "email") {
            return validateEmail(value, errors);
        }
        if (name === "password") {
            return validatePassword(value, errors);
        }
        return errors;
    }

    const getBorderColor = (name) => {
        const fieldErrors = error[name];

        if (!fieldErrors) return "border-gray-300";

        const hasError = Array.isArray(fieldErrors) && fieldErrors.length > 0;
        
        return hasError ? "border-red-500" : "border-gray-300";
    }

    return (
        <div className="flex flex-col items-center border border-gray-300 p-8 rounded-lg gap-5 w-150 min-w-[300px] max-w-[500px]">
            <img src="./src/assets/PeerPrepLogo.png" alt="Peerprep Logo" className="w-40"/>
            <h2 className="font-bold">Welcome Back</h2>
            <p className="text-gray-600">Sign in to continue your peer collaboration journey</p>
            <div className="w-full">
                <form className="flex flex-col gap-4" onSubmit={handleSubmit}>

                    {/* Email Field */}
                    <div className="flex flex-col gap-1">
                        <label className="font-ubuntu">Email</label>
                        <input 
                            type="text"
                            name="email"
                            placeholder="your.email@example.com" 
                            value={formData.email}
                            required
                            onChange={handleInputChange}
                            onBlur={handleBlur}
                            className={`w-full border ${getBorderColor("email")} p-2 rounded h-10`} />
                        <ErrorMessage errorsArray={error.email} />
                    </div>

                    {/* Password Field */}
                    <div className="flex flex-col gap-1">
                        <label className="font-ubuntu">Password</label>
                        <div className={`flex items-center w-full border ${getBorderColor("password")} p-2 rounded focus-within:border-primary focus-within:border-2 h-10`}>
                            <input 
                                type={inputType} 
                                name="password"
                                placeholder="Password"
                                value={formData.password}
                                required
                                onChange={handleInputChange}
                                onBlur={handleBlur}
                                className="focus:outline-none flex-grow"/>
                            <button
                                type="button"
                                onClick={togglePasswordVisibility}
                                className="focus:outline-none bg-transparent hover:bg-transparent hover:text-gray-500 text-gray-400">
                            {showPassword?
                                <Eye className="w-5 h-5"/>
                                :
                                <EyeOff className="w-5 h-5"/>
                            }
                            </button>
                        </div>
                        <ErrorMessage errorsArray={error.password} />
                    </div>

                    {/* Login Error Message */}
                    {loginError && (
                        <div className="text-red-500 text-sm text-center p-2 bg-red-50 rounded">
                            <MessageSquareWarning className="inline w-4 h-4 mr-1"/>
                            {loginError}
                        </div>
                    )}

                    <button type="submit" disabled={isLoading}>
                        {isLoading ? "Signing In..." : "Sign In"}
                    </button>
                </form>
            </div>
            <div className="flex flex-col items-center gap-2 text-sm ">
                <p><a href="/reset-password">Forgot your password?</a></p>
                <p>Don't have an account? <a href="/register">Create one</a></p>
            </div>
        </div>
    )
}

export default LoginForm;