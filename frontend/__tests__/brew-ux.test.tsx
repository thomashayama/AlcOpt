import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import {
  afterEach, beforeEach, expect, test, vi,
} from 'vitest';

import { IngredientsTab } from '../src/app/brew/tabs/IngredientsTab';
import { MassTab } from '../src/app/brew/tabs/MassTab';
import { RackTab } from '../src/app/brew/tabs/RackTab';
import { SgTab } from '../src/app/brew/tabs/SgTab';
import { StartTab } from '../src/app/brew/tabs/StartTab';
import { api } from '../src/lib/api';

vi.mock('../src/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  cleanup();
});

test('start and rack confirmations include fermentation and log ids', async () => {
  mockedApi.get.mockResolvedValue([]);
  mockedApi.post
    .mockResolvedValueOnce({
      id: 21,
      container_id: 4,
      fermentation_id: 9,
      start_date: '2026-05-28T00:00:00',
      stage: 'primary',
    })
    .mockResolvedValueOnce({
      id: 22,
      container_id: 2,
      fermentation_id: 9,
      source_container_id: 1,
      start_date: '2026-05-29T00:00:00',
      stage: 'secondary',
    });

  const startView = render(<StartTab />);
  fireEvent.change(screen.getByLabelText('Container ID'), {
    target: { value: '4' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Start Fermentation' }));

  expect(await screen.findByText('Fermentation 9 started in container 4 (log 21).')).toBeDefined();
  startView.unmount();

  render(<RackTab />);
  fireEvent.click(screen.getByRole('button', { name: 'Record Racking' }));

  expect(await screen.findByText('Rack recorded: fermentation 9 moved from container 1 to 2 (log 22).')).toBeDefined();
});

test('sg and mass measurements show ids and can undo the last current-session record', async () => {
  mockedApi.get.mockResolvedValue([]);
  mockedApi.post
    .mockResolvedValueOnce({
      id: 10,
      fermentation_id: 2,
      measurement_date: '2026-05-28',
      specific_gravity: 1.045,
    })
    .mockResolvedValueOnce({ message: 'SG measurement 10 undone' })
    .mockResolvedValueOnce({
      id: 20,
      fermentation_id: 2,
      measurement_date: '2026-05-28',
      mass: 5200,
    })
    .mockResolvedValueOnce({ message: 'Mass measurement 20 undone' });

  const sgView = render(<SgTab />);
  fireEvent.change(screen.getByLabelText('Specific Gravity'), {
    target: { value: '1.045' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Record Measurement' }));

  expect(await screen.findByText('SG measurement 10 recorded for fermentation 2: 1.045.')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Undo Last SG Measurement' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/sg-measurements/10/undo');
  });
  expect(await screen.findByText('SG measurement 10 undone')).toBeDefined();
  sgView.unmount();

  render(<MassTab />);
  fireEvent.change(screen.getByLabelText('Mass (g)'), {
    target: { value: '5200' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Record Measurement' }));

  expect(await screen.findByText('Mass measurement 20 recorded for fermentation 2: 5200g.')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: 'Undo Last Mass Measurement' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/mass-measurements/20/undo');
  });
  expect(await screen.findByText('Mass measurement 20 undone')).toBeDefined();
});

test('ingredient creation selects it, addition previews amount, table renders API shape, and undo works', async () => {
  mockedApi.get.mockImplementation(async (path: string) => {
    if (path === '/api/brew/ingredients') return [];
    if (path === '/api/brew/additions') {
      return [
        {
          id: 1,
          container_id: 1,
          ingredient_id: 1,
          ingredient_name: 'Existing Juice',
          added_at: '2026-05-27T10:00:00',
          amount: 125,
          unit: 'mL',
        },
      ];
    }
    return [];
  });
  mockedApi.post
    .mockResolvedValueOnce({
      id: 12,
      name: 'Honey',
      sugar_content: 800,
      ingredient_type: 'Liquid',
      density: 1.4,
      price: 12,
      notes: '',
    })
    .mockResolvedValueOnce({
      id: 34,
      fermentation_id: 2,
      message: 'Ingredient added',
    })
    .mockResolvedValueOnce({ message: 'Ingredient addition 34 undone' });

  render(<IngredientsTab />);

  expect(await screen.findByText('Existing Juice')).toBeDefined();
  expect(screen.getByText('125')).toBeDefined();

  fireEvent.change(screen.getByLabelText('Name'), {
    target: { value: 'Honey' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Create Ingredient' }));

  expect(await screen.findByText('Ingredient 12 created: Honey. It is selected below.')).toBeDefined();
  expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/ingredients', expect.objectContaining({
    name: 'Honey',
    sugar_content: 0,
    density: 1,
    price: 0,
    notes: '',
  }));
  expect((screen.getByLabelText('Ingredient Name') as HTMLInputElement).value).toBe('Honey');

  fireEvent.change(screen.getByLabelText('Starting Amount'), {
    target: { value: '0' },
  });
  fireEvent.change(screen.getByLabelText('Ending Amount'), {
    target: { value: '500' },
  });

  expect(screen.getByText('500 - 0 = 500 g amount change')).toBeDefined();

  fireEvent.click(screen.getByRole('button', { name: 'Add to Container' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/additions', expect.objectContaining({
      container_id: 1,
      ingredient_name: 'Honey',
      starting_amount: 0,
      ending_amount: 500,
      unit: 'g',
    }));
  });
  expect(await screen.findByText('Addition 34 recorded for container 1: Honey 500 g (fermentation 2).')).toBeDefined();

  fireEvent.click(screen.getByRole('button', { name: 'Undo Last Addition' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/additions/34/undo');
  });
  expect(await screen.findByText('Ingredient addition 34 undone')).toBeDefined();
});
