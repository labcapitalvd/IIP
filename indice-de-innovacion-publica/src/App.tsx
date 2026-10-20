/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import { FormSubmissionProvider } from './context/FormSubmissionContext';
import { LoginView } from './components/auth/LoginView';
import { AdminApp } from './components/admin/AdminApp';
import { EntityApp } from './components/entity/EntityApp';

const MainContent: React.FC = () => {
  const { user, role } = useAuth();

  if (!user) return <LoginView />;

  // Dos portales independientes: administración y entidades.
  return role === 'admin' ? <AdminApp /> : <EntityApp />;
};

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <FormSubmissionProvider>
          <MainContent />
        </FormSubmissionProvider>
      </AppProvider>
    </AuthProvider>
  );
}
