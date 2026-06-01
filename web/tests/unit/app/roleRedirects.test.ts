import { describe, it, expect } from 'vitest';
import { ROLE_REDIRECT } from '@/app/roleRedirects';

describe('ROLE_REDIRECT', () => {
  it('redirects parents to /feed', () => {
    expect(ROLE_REDIRECT['PAR']).toBe('/feed');
  });

  it('redirects students to /student/home', () => {
    expect(ROLE_REDIRECT['STD']).toBe('/student/home');
  });

  it('redirects teachers to /teacher', () => {
    expect(ROLE_REDIRECT['TCH']).toBe('/teacher');
  });

  it('redirects admins to /admin', () => {
    expect(ROLE_REDIRECT['ADM']).toBe('/admin');
  });

  it('redirects directors to /admin', () => {
    expect(ROLE_REDIRECT['DIR']).toBe('/admin');
  });

  it('redirects supervisors to /notifications', () => {
    expect(ROLE_REDIRECT['SUP']).toBe('/notifications');
  });

  it('redirects content managers to /cms', () => {
    expect(ROLE_REDIRECT['CONTENT_MGR']).toBe('/cms');
  });

  it('covers all known roles', () => {
    const expectedRoles = ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP', 'CONTENT_MGR'];
    expectedRoles.forEach((role) => {
      expect(ROLE_REDIRECT[role]).toBeDefined();
      expect(typeof ROLE_REDIRECT[role]).toBe('string');
    });
  });

  it('all redirects start with /', () => {
    Object.values(ROLE_REDIRECT).forEach((path) => {
      expect(path).toMatch(/^\//);
    });
  });

  it('unknown role returns undefined', () => {
    expect(ROLE_REDIRECT['UNKNOWN_ROLE']).toBeUndefined();
  });

  it('has exactly 7 entries', () => {
    expect(Object.keys(ROLE_REDIRECT)).toHaveLength(7);
  });
});
