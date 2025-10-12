import { LogOut } from "lucide-react";

const useAuth = () => {
    // TODO: Replace with actual authentication logic
    return {
        user: { name: "John Doe" },
        logout: () => console.log("Logged out")
    };
}

const Link = ({ to, children }) => {
    return (
        <a href={to} className="text-primary-light text-bold text-2xl hover:primary">
            {children}
        </a>
    );
};

const NavBar = () => {
    const {logout, user} = useAuth();

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
                    onClick={logout}
                    className="bg-red-500 text-white hover:bg-red-600 font-semibold py-2 px-4 rounded">
                    <LogOut className="inline-block mr-2" />
                    Logout
                </button>
            </div>
        </nav>

    );
};

export default NavBar;