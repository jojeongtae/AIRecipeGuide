import { Clock, Users } from 'lucide-react';
import { Card } from './ui/card';

export interface Recipe {
  id: number | string;
  name?: string;
  title?: string;
  image?: string;
  cooking_time?: number | string;
  cookTime?: string;
  servings?: number;
  serving_size?: number;
  difficulty?: string;
  category?: string;
  description?: string;
  ingredients?: string[];
  instructions?: string[];
  steps?: Array<{ step?: number; description: string; [key: string]: any }>;
  match_rate?: number;
  popularity_display?: string;
  substitutions?: {
    has_substitutions?: boolean;
    substitution_list?: Array<{
      original: string;
      substitute: string;
      reason?: string;
      taste_change?: string;
      usage_tip?: string;
    }>;
    summary?: string;
  };
}

interface RecipeCardProps {
  recipe: Recipe;
  onClick: () => void;
}

export function RecipeCard({ recipe, onClick }: RecipeCardProps) {
  const title = recipe.name || recipe.title || '레시피';
  const image = recipe.image || 'https://via.placeholder.com/400x300?text=No+Image';
  const difficulty = recipe.difficulty || '보통';
  const cookTime = recipe.cookTime || (recipe.cooking_time ? `${recipe.cooking_time}분` : '알 수 없음');
  const servings = recipe.servings || recipe.serving_size || 2;
  const description = recipe.description || '';

  return (
    <Card 
      className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onClick}
    >
      <div className="relative h-48 overflow-hidden">
        <img 
          src={image} 
          alt={title}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x300?text=No+Image';
          }}
        />
        <div className="absolute top-2 right-2 bg-white px-2 py-1 rounded-full text-sm font-medium shadow-md">
          {difficulty}
        </div>
        {recipe.match_rate !== undefined && (
          <div className="absolute top-2 left-2 bg-orange-500 text-white px-2 py-1 rounded-full text-xs font-medium shadow-md">
            {Math.round(recipe.match_rate * 100)}% 매칭
          </div>
        )}
      </div>
      <div className="p-4">
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        {description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {description}
          </p>
        )}
        {recipe.popularity_display && (
          <p className="text-xs text-orange-600 mb-2 font-medium">{recipe.popularity_display}</p>
        )}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{cookTime}</span>
          </div>
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            <span>{servings}인분</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
