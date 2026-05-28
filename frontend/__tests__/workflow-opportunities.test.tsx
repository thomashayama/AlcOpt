import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import {
  afterEach, beforeEach, expect, test, vi,
} from 'vitest';

import BottlesPage from '../src/app/bottles/page';
import { CalculatorTab } from '../src/app/brew/tabs/CalculatorTab';
import InfoPageWrapper from '../src/app/info/page';
import LabelsPage from '../src/app/labels/page';
import TastingPageWrapper from '../src/app/tasting/page';
import { api } from '../src/lib/api';

vi.mock('../src/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const authState = {
  user: {
    email: 'user@test.com',
    name: 'User',
    picture: '',
    is_admin: true,
  },
  loading: false,
  login: vi.fn(),
  logout: vi.fn(),
};

vi.mock('../src/components/AuthProvider', () => ({
  useAuth: () => authState,
}));

const routerPush = vi.fn();
let searchParams = new URLSearchParams();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: routerPush }),
  useSearchParams: () => searchParams,
}));

const mockedApi = vi.mocked(api);

beforeEach(() => {
  vi.resetAllMocks();
  authState.user = {
    email: 'user@test.com',
    name: 'User',
    picture: '',
    is_admin: true,
  };
  authState.loading = false;
  searchParams = new URLSearchParams();
});

afterEach(() => {
  cleanup();
});

test('calculator renders sugar concentration and volume returned by the backend', async () => {
  mockedApi.get.mockResolvedValue([
    {
      id: 1,
      name: 'Grape Juice',
      sugar_content: 200,
      ingredient_type: 'Liquid',
      density: 1.05,
    },
  ]);
  mockedApi.post.mockResolvedValue({
    max_abv: 6.7,
    sugar_content_g_per_l: 115.4,
    volume_l: 1.25,
  });

  render(<CalculatorTab />);

  fireEvent.click(await screen.findByLabelText('Grape Juice (Liquid)'));
  fireEvent.change(screen.getByPlaceholderText('Amount'), {
    target: { value: '1250' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Calculate ABV' }));

  expect(await screen.findByText('115.4 g/L')).toBeDefined();
  expect(await screen.findByText('1.25 L')).toBeDefined();
});

test('calculator uses a unit dropdown with valid backend units', async () => {
  mockedApi.get.mockResolvedValue([
    {
      id: 1,
      name: 'Grape Juice',
      sugar_content: 200,
      ingredient_type: 'Liquid',
      density: 1.05,
    },
  ]);
  mockedApi.post.mockResolvedValue({
    max_abv: 6.7,
    sugar_content_g_per_l: 115.4,
    volume_l: 1.25,
  });

  render(<CalculatorTab />);

  fireEvent.click(await screen.findByLabelText('Grape Juice (Liquid)'));
  fireEvent.change(screen.getByPlaceholderText('Amount'), {
    target: { value: '1250' },
  });
  fireEvent.change(screen.getByLabelText('Unit for Grape Juice'), {
    target: { value: 'mL' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Calculate ABV' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/calculate-abv', expect.objectContaining({
      ingredients: [expect.objectContaining({ unit: 'mL' })],
    }));
  });
});

test('vessel creation tells the user which container id to label', async () => {
  mockedApi.get.mockResolvedValue([]);
  mockedApi.post.mockResolvedValue({
    id: 42,
    container_type: 'carboy',
    volume_liters: 2,
    material: 'Glass',
    empty_mass: 792,
    date_added: '2026-05-28',
  });

  render(<BottlesPage />);

  fireEvent.click(screen.getByRole('button', { name: 'Add Vessel' }));

  expect(await screen.findByText('Vessel created: Container ID 42. Label this vessel 42.')).toBeDefined();
});

test('tasting submission shows review ids and can undo the last logged-in review', async () => {
  mockedApi.get.mockResolvedValue([]);
  mockedApi.post
    .mockResolvedValueOnce({
      id: 44,
      container_id: 3,
      name: 'user@test.com',
      fermentation_id: 8,
      overall_rating: 3,
      boldness: 3,
      tannicity: 3,
      sweetness: 3,
      acidity: 3,
      complexity: 3,
      review_date: '2026-05-28',
    })
    .mockResolvedValueOnce({ message: 'Review 44 undone' });

  render(<TastingPageWrapper />);

  fireEvent.change(screen.getByLabelText('Container ID'), {
    target: { value: '3' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Submit Review' }));

  expect(await screen.findByText('Review 44 submitted for container 3 (fermentation 8).')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Undo Last Review' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/reviews/44/undo');
  });
  expect(await screen.findByText('Review 44 undone')).toBeDefined();
});

test('info page displays the active container log details', async () => {
  mockedApi.get.mockResolvedValue({
    container: {
      id: 12,
      container_type: 'bottle',
      volume_liters: 0.75,
      empty_mass: 500,
    },
    fermentation: {
      id: 6,
      start_date: '2026-05-01T00:00:00',
    },
    fermentation_log: {
      id: 99,
      container_id: 12,
      fermentation_id: 6,
      source_container_id: 2,
      start_date: '2026-05-28T12:00:00',
      amount: 342.5,
      unit: 'g',
      stage: 'bottled',
    },
    ingredients: [],
    sg_measurements: [],
    reviews: [],
    abv: null,
    residual_sugar: null,
  });

  render(<InfoPageWrapper />);

  fireEvent.change(screen.getByLabelText('Container ID'), {
    target: { value: '12' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Look Up' }));

  expect(await screen.findByText('Container Log #99')).toBeDefined();
  expect(screen.getByText('bottled')).toBeDefined();
  expect(screen.getByText('2')).toBeDefined();
  expect(screen.getByText('342.5 g')).toBeDefined();
});

test('labels page shows current container id range helpers', async () => {
  mockedApi.get.mockResolvedValue([
    { id: 7, container_type: 'carboy' },
    { id: 12, container_type: 'bottle' },
  ]);

  render(<LabelsPage />);

  expect(await screen.findByText('Highest container ID: 12')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Use 1-12' }));

  expect(
    (screen.getByLabelText('Min Container ID') as HTMLInputElement).value,
  ).toBe('1');
  expect(
    (screen.getByLabelText('Max Container ID') as HTMLInputElement).value,
  ).toBe('12');
});
