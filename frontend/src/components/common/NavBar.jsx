import { LogOut } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useNotification } from "../../contexts/NotificationContext";
import { useNavigate } from "react-router-dom";

const Link = ({ to, children }) => {
    return (
        <a href={to} className="text-primary-light text-bold text-2xl hover:primary">
            {children}
        </a>
    ); 
};

const NavBar = () => {
    const { logout } = useAuth();
    const { showSuccess, showError } = useNotification();
    const navigate = useNavigate();

    const handleLogout = async () => {
        const result = await logout();
        
        if (result.success) {
            showSuccess('Success', 'You have been logged out successfully');
        } else {
            // Handle different error types notification
            let errorTitle = 'Logout Error';
            let errorMessage = result.error?.message || 'An unexpected error occurred';
            
            switch (result.error?.type) {
                case 'auth':
                    errorTitle = 'Authentication Error';
                    errorMessage = 'Session expired - you have been logged out locally';
                    break;
                case 'bad_request':
                    errorTitle = 'Logout Failed';
                    errorMessage = 'Server error during logout - you have been logged out locally';
                    break;
                case 'network':
                    errorTitle = 'Network Error';
                    errorMessage = 'Could not connect to server - you have been logged out locally';
                    break;
            }
            
            showError(errorTitle, errorMessage);
        }
        
        // Always redirect to login page after logout attempt
        navigate('/login');
    }

    const navPages = [
        { name: 'Home', path: '/home' },
        { name: 'Matching', path: '/matching' },
    ]

    return (
        <nav className="flex justify-between items-center bg-background shadow-md border-b border-gray-600 w-full p-4">
            <div className="flex items-center space-x-2">
                <img src="./src/assets/PeerPrepLogoLight.png" alt="PeerPrep Logo" className="h-10 ml-4"/>
            </div>

            <div className="flex space-x-10">
                {navPages.map((page) => (
                    <Link key={page.name} to={page.path}>
                        {page.name}
                    </Link>
                ))}
            </div>

            <div className="flex items-center space-x-4">
                <button
                    onClick={handleLogout}
                    className="bg-red-500 text-white hover:bg-red-600 font-semibold py-2 px-4 rounded">
                    <LogOut className="inline-block mr-2" />
                    Logout
                </button>
            </div>
        </nav>

    );
};

export default NavBar;