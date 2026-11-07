import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import {
  afterEach, beforeEach, expect, test, vi,
} from 'vitest';

import BottlesPage from '../src/app/bottles/page';
import { BottleTab as BrewBottleTab } from '../src/app/brew/tabs/BottleTab';
import { CalculatorTab } from '../src/app/brew/tabs/CalculatorTab';
import { IngredientsTab } from '../src/app/brew/tabs/IngredientsTab';
import InfoPageWrapper from '../src/app/info/page';
import LabelsPage from '../src/app/labels/page';
import TastingPageWrapper from '../src/app/tasting/page';
import { api } from '../src/lib/api';

vi.mock('../src/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
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

const mockedApi = vi.mocked(api) as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
};

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

  fireEvent.change(screen.getByLabelText('Container ID'), {
    target: { value: '1' },
  });
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

  fireEvent.change(screen.getByLabelText('Container ID'), {
    target: { value: '1' },
  });
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

test('ingredients and calculator use active fermentation container choices', async () => {
  const active = [
    {
      fermentation_id: 9,
      start_date: '2026-05-01T00:00:00',
      container_id: 4,
      container_type: 'carboy',
      stage: 'primary',
      log_start_date: '2026-05-01T00:00:00',
    },
  ];

  mockedApi.get.mockImplementation(async (path: string) => {
    if (path === '/api/brew/fermentations/active') return active;
    if (path === '/api/brew/ingredients') {
      return [
        {
          id: 1,
          name: 'Grape Juice',
          sugar_content: 200,
          ingredient_type: 'Liquid',
          density: 1.05,
        },
      ];
    }
    if (path === '/api/brew/additions') return [];
    return [];
  });
  mockedApi.post
    .mockResolvedValueOnce({
      id: 34,
      fermentation_id: 9,
      message: 'Ingredient added',
    })
    .mockResolvedValueOnce({
      max_abv: 6.7,
      sugar_content_g_per_l: 115.4,
      volume_l: 1.25,
    });

  const { unmount } = render(<IngredientsTab />);

  expect(
    await screen.findByText('Container 4 - fermentation 9 - primary - carboy - started 2026-05-01'),
  ).toBeDefined();
  await waitFor(() => {
    expect((screen.getByLabelText('Container ID') as HTMLInputElement).value).toBe('4');
  });
  fireEvent.change(screen.getByLabelText('Ingredient Name'), {
    target: { value: 'Grape Juice' },
  });
  fireEvent.change(screen.getByLabelText('Ending Amount'), {
    target: { value: '1250' },
  });
  fireEvent.change(screen.getByLabelText('Unit'), {
    target: { value: 'mL' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Add to Container' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/additions', expect.objectContaining({
      container_id: 4,
      unit: 'mL',
    }));
  });

  unmount();
  render(<CalculatorTab />);

  expect(
    await screen.findByText('Container 4 - fermentation 9 - primary - carboy - started 2026-05-01'),
  ).toBeDefined();
  await waitFor(() => {
    expect((screen.getByLabelText('Container ID') as HTMLInputElement).value).toBe('4');
  });
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
      container_id: 4,
      ingredients: [expect.objectContaining({ unit: 'mL' })],
    }));
  });
});

test('finish fermentation records end date and optional end mass', async () => {
  mockedApi.get.mockImplementation(async (path: string) => {
    if (path === '/api/brew/fermentations/active') {
      return [
        {
          fermentation_id: 9,
          start_date: '2026-05-01T00:00:00',
          container_id: 4,
          container_type: 'carboy',
          stage: 'primary',
          log_start_date: '2026-05-01T00:00:00',
        },
      ];
    }
    return [];
  });
  mockedApi.patch.mockResolvedValue({
    id: 9,
    start_date: '2026-05-01T00:00:00',
    end_date: '2026-05-28T00:00:00',
    end_mass: 1780,
  });

  render(<BrewBottleTab />);

  expect(await screen.findByLabelText('Active Fermentation to Finish')).toBeDefined();
  fireEvent.change(screen.getByLabelText('End Mass (g)'), {
    target: { value: '1780' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Finish Fermentation' }));

  await waitFor(() => {
    expect(mockedApi.patch).toHaveBeenCalledWith('/api/brew/fermentations/9', {
      end_date: expect.any(String),
      end_mass: 1780,
    });
  });
  expect(await screen.findByText('Fermentation 9 finished.')).toBeDefined();
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

test('bottle and vessel registration expose common presets', async () => {
  mockedApi.get.mockResolvedValue([]);

  render(<BottlesPage />);

  fireEvent.change(screen.getByLabelText('Vessel Preset'), {
    target: { value: 'glass-2l-carboy' },
  });
  expect((screen.getByLabelText('Type') as HTMLSelectElement).value).toBe('carboy');
  expect((screen.getByLabelText('Material') as HTMLSelectElement).value).toBe('Glass');
  expect((screen.getByLabelText('Volume (L)') as HTMLInputElement).value).toBe('2');

  fireEvent.click(screen.getByRole('tab', { name: 'New Bottle' }));
  fireEvent.change(await screen.findByLabelText('Bottle Preset'), {
    target: { value: '750ml-wine-bottle' },
  });
  expect((screen.getByLabelText('Volume (L)') as HTMLInputElement).value).toBe('0.75');
  expect((screen.getByLabelText('Empty Mass (g)') as HTMLInputElement).value).toBe('500');
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

test('tasting form can verify container context before submitting', async () => {
  mockedApi.get.mockImplementation(async (path: string) => {
    if (path === '/api/reviews/mine') return [];
    if (path === '/api/containers/12') {
      return {
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
        abv: 6.4,
        residual_sugar: 14.2,
      };
    }
    return [];
  });

  render(<TastingPageWrapper />);

  expect((screen.getByLabelText('Container ID') as HTMLInputElement).value).toBe('');
  fireEvent.change(screen.getByLabelText('Container ID'), {
    target: { value: '12' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Check Container' }));

  expect(await screen.findByText('Container #12')).toBeDefined();
  expect(screen.getByText('bottle')).toBeDefined();
  expect(screen.getByText('Fermentation #6')).toBeDefined();
  expect(screen.getByText('Stage: bottled')).toBeDefined();
  expect(screen.getByText('ABV: 6.40%')).toBeDefined();
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

test('labels page can target recent bottles and the next label run', async () => {
  mockedApi.get.mockResolvedValue([
    { id: 7, container_type: 'carboy' },
    { id: 12, container_type: 'bottle' },
    { id: 14, container_type: 'bottle' },
  ]);

  render(<LabelsPage />);

  expect(await screen.findByText('Highest container ID: 14')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Use recent bottles' }));
  expect((screen.getByLabelText('Min Container ID') as HTMLInputElement).value).toBe('12');
  expect((screen.getByLabelText('Max Container ID') as HTMLInputElement).value).toBe('14');

  fireEvent.change(screen.getByLabelText('Next label count'), {
    target: { value: '6' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Use next labels' }));
  expect((screen.getByLabelText('Min Container ID') as HTMLInputElement).value).toBe('15');
  expect((screen.getByLabelText('Max Container ID') as HTMLInputElement).value).toBe('20');
});
