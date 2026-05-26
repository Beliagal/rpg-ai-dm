import '@testing-library/jest-dom';
import { beforeEach, vi } from 'vitest';

beforeEach(() => {
  // Limpia los mocks de red antes de cada test para que no se arrastren estados ficticios
  vi.clearAllMocks();
});