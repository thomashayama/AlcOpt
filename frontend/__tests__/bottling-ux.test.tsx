import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import {
  afterEach, beforeEach, expect, test, vi,
} from 'vitest';

import { BottleTab as BrewBottleTab } from '../src/app/brew/tabs/BottleTab';
import { BottleTab as BottleRegistrationTab } from '../src/app/bottles/page';
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

test('bottle registration shows created bottle id and next bottle id', async () => {
  mockedApi.get.mockResolvedValue([
    {
      id: 50,
      container_type: 'bottle',
      volume_liters: 0.75,
      empty_mass: 412,
      date_added: '2025-03-29',
    },
  ]);
  mockedApi.post.mockResolvedValue({
    id: 51,
    container_type: 'bottle',
    volume_liters: 0.5,
    empty_mass: 500,
    date_added: '2026-05-28',
  });

  render(<BottleRegistrationTab />);

  expect(await screen.findByText('Next bottle ID should be 51')).toBeDefined();

  fireEvent.click(screen.getByRole('button', { name: 'Add Bottle' }));

  await waitFor(() => {
    expect(screen.getByText('Bottle created: Container ID 51. Label this bottle 51. Next bottle ID: 52.')).toBeDefined();
  });
});

test('bottling can submit filled bottle mass instead of manual contents amount', async () => {
  mockedApi.get.mockResolvedValue({
    container: {
      id: 3,
      container_type: 'bottle',
      volume_liters: 0.75,
      empty_mass: 500,
      date_added: '2025-03-29',
    },
    fermentation: null,
    fermentation_log: null,
    ingredients: [],
    sg_measurements: [],
    reviews: [],
    abv: null,
    residual_sugar: null,
  });
  mockedApi.post.mockResolvedValue({
    id: 77,
    container_id: 3,
    fermentation_id: 1,
    start_date: '2026-05-28T12:00:00',
    amount: 342.5,
    unit: 'g',
    stage: 'bottled',
  });

  render(<BrewBottleTab />);

  fireEvent.change(screen.getByLabelText('To Container ID (bottle)'), {
    target: { value: '3' },
  });
  fireEvent.click(screen.getByLabelText('Filled bottle mass'));

  expect(await screen.findByText('Empty mass: 500g')).toBeDefined();

  fireEvent.change(screen.getByLabelText('Filled Bottle Mass (g)'), {
    target: { value: '842.5' },
  });

  expect(screen.getByText('842.5g - 500g = 342.5g contents')).toBeDefined();

  fireEvent.click(screen.getByRole('button', { name: 'Record Bottling' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/bottle', expect.objectContaining({
      from_container_id: 1,
      to_container_id: 3,
      filled_mass_g: 842.5,
    }));
  });
});

test('bottling exposes undo for the last bottling action in the current session', async () => {
  mockedApi.post
    .mockResolvedValueOnce({
      id: 77,
      container_id: 3,
      fermentation_id: 1,
      start_date: '2026-05-28T12:00:00',
      amount: 750,
      unit: 'mL',
      stage: 'bottled',
    })
    .mockResolvedValueOnce({ message: 'Bottling log 77 undone' });

  render(<BrewBottleTab />);

  fireEvent.change(screen.getByLabelText('To Container ID (bottle)'), {
    target: { value: '3' },
  });
  fireEvent.change(screen.getByLabelText('Amount'), {
    target: { value: '750' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Record Bottling' }));

  expect(await screen.findByRole('button', { name: 'Undo Last Bottling' })).toBeDefined();

  fireEvent.click(screen.getByRole('button', { name: 'Undo Last Bottling' }));

  await waitFor(() => {
    expect(mockedApi.post).toHaveBeenCalledWith('/api/brew/bottle/77/undo');
  });
  expect(await screen.findByText('Bottling log 77 undone')).toBeDefined();
});
