import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import React from 'react';

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should provide auth context', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    expect(result.current.token).toBe(null);
  });

  it('should login and store token', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => {
      result.current.login('test-token', { id: '1', name: 'Test User' });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe('test-token');
    expect(result.current.user?.name).toBe('Test User');
  });

  it('should logout and clear token', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => {
      result.current.login('test-token', { id: '1', name: 'Test User' });
    });

    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBe(null);
    expect(result.current.user).toBe(null);
  });
});



