import React, { useState } from "react";
import { Icon , Eye, EyeOff} from "lucide-react";

const RegisterForm = () => {
    const [showPassword, setShowPassword] = useState(false);
    
    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };

    const inputType = showPassword ? "text" : "password";

    return (
        <div className="flex flex-col items-center border border-gray-300 p-8 rounded-lg gap-3 w-150 min-w-[300px] max-w-[500px]">
            <img src="./src/assets/PeerPrepLogo.png" alt="Peerpad Logo" className="w-40"/>
            <h2 className="font-bold">Sign Up</h2>
            <p>Create your PeerPrep account today!</p>
            <div className="w-full">
                <form className="flex flex-col gap-4">
                      <div className="flex flex-col gap-1">
                        <label className="font-ubuntu">Username</label>
                        <input type="text" placeholder="Your username" className="w-full border border-gray-300 p-2 rounded h-10" />
                    </div>
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
                        <p className="text-xs text-gray-500 mt-1">
                            Minimum 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character.
                        </p>
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="font-ubuntu">Confirm Password</label>
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
                <p>Already have an account? <a href="/login">Log in</a></p>
            </div>
        </div>
    )
}

export default RegisterForm;