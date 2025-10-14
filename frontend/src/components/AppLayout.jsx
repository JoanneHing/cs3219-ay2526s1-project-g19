import { Outlet } from 'react-router-dom';
import NavBar from './common/NavBar';

const AppLayout = () => {
  return (
    <div className="min-h-screen bg-background font-inter w-full">
      <NavBar />
      <main>
        <Outlet /> 
      </main>
    </div>
  );
};

export default AppLayout;
