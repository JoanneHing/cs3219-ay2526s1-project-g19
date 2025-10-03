import React, { useState } from "react";
import { Icon , Eye, EyeOff} from "lucide-react";

const LoginForm = () => {
    const [showPassword, setShowPassword] = useState(false);
    
    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };

    const inputType = showPassword ? "text" : "password";

    return (
        <div className="flex flex-col items-center border border-gray-300 p-8 rounded-lg gap-6 w-150">
            <img src="./src/assets/PeerPrepLogo.png" alt="Peerpad Logo" className="w-40"/>
            <h2 className="font-bold">Welcome Back</h2>
            <p>Sign in to continue your peer collaboration journey</p>
            <div className="w-full">
                <form className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1">
                        <label className="font-ubuntu">Email</label>
                        <input type="text" placeholder="your.email@example.com" className="w-full border border-gray-300 p-2 rounded h-10" />
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="font-ubuntu">Password</label>
                        <div className="flex items-center w-full border border-gray-300 p-2 rounded focus-within:border-primary focus-within:border-2 h-10">
                            <input type={inputType} placeholder="Password" className="focus:outline-none flex-grow"/>
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
                    </div>
                    <button type="submit">Sign In</button>
                </form>
            </div>
            <div className="flex flex-col items-center gap-2 text-sm ">
                <p><a href="/reset-password">Forgot your password?</a></p>
                <p><a href="/register">Don't have an account? Create one</a></p>
            </div>
        </div>
    )
}

export default LoginForm;