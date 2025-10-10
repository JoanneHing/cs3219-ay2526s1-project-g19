import { Outlet } from 'react-router-dom';

const AppLayout = () => {
  return (
    <div className="min-h-screen bg-background font-inter">
      <main>
        <Outlet /> 
      </main>
    </div>
  );
};

export default AppLayout;
