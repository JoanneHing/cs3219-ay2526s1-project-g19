import { useAuth } from "../contexts/AuthContext";
import { LucideLockKeyhole, Verified } from "lucide-react";

const ProfilePage = () => {
    const { user } = useAuth();
    
    return (
        <div className="container mx-auto p-10">
            <h1 className="text-4xl font-bold mb-4">{user.display_name}</h1>
            <h4 className="text-gray-400 mb-2">Email: {user.email}</h4>
            <button className="mt-4 bg-primary text-white hover:bg-primary-dark font-semibold py-2 px-4 rounded">
                <LucideLockKeyhole className="inline-block mr-2" />
                Password Reset
            </button>
            {/* <button className="mt-4 ml-4 bg-green-500 text-white hover:bg-green-600 font-semibold py-2 px-4 rounded">
                <Verified className="inline-block mr-2" />
                Verify Account
            </button> */}
        </div>
    );
};

export default ProfilePage;
