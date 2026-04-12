export interface ContainerOut {
  id: number;
  container_type: string;
  volume_liters?: number | null;
  material?: string | null;
  empty_mass?: number | null;
  date_added?: string | null;
  notes?: string | null;
}

export interface IngredientOut {
  id: number;
  name: string;
  sugar_content?: number | null;
  ingredient_type?: string | null;
  density?: number | null;
  price?: number | null;
  notes?: string | null;
}

export interface FermentationOut {
  id: number;
  start_date: string;
  end_date?: string | null;
  end_mass?: number | null;
}

export interface ContainerLogOut {
  id: number;
  container_id: number;
  fermentation_id: number;
  start_date: string;
  end_date?: string | null;
  source_container_id?: number | null;
  amount?: number | null;
  unit?: string | null;
  stage?: string | null;
}

export interface ReviewOut {
  id: number;
  container_id: number;
  name?: string | null;
  fermentation_id: number;
  overall_rating: number;
  boldness: number;
  tannicity: number;
  sweetness: number;
  acidity: number;
  complexity: number;
  review_date: string;
}

export interface SgMeasurementOut {
  id: number;
  fermentation_id: number;
  measurement_date: string;
  specific_gravity?: number | null;
}

export interface MassMeasurementOut {
  id: number;
  fermentation_id: number;
  measurement_date: string;
  mass: number;
}

export interface LeaderboardEntry {
  rank: number;
  fermentation_id: number;
  avg_rating: number;
  num_ratings: number;
}

export interface UserInfo {
  email: string;
  picture: string;
  is_admin: boolean;
}

export interface IngredientAdditionOut {
  id: number;
  name: string;
  amount?: number | null;
  unit?: string | null;
  date_added?: string | null;
  ingredient_type?: string | null;
  sugar_content?: number | null;
  notes?: string | null;
}

export interface ContainerInfoResponse {
  container: ContainerOut;
  fermentation?: FermentationOut | null;
  fermentation_log?: ContainerLogOut | null;
  ingredients: IngredientAdditionOut[];
  sg_measurements: SgMeasurementOut[];
  reviews: ReviewOut[];
  abv?: number | null;
  residual_sugar?: number | null;
}
