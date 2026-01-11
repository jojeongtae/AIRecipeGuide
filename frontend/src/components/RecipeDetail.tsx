import { X, Clock, Users, ChefHat } from 'lucide-react';
import { Recipe } from './RecipeCard';
import { Button } from './ui/button';

interface RecipeDetailProps {
  recipe: Recipe;
  onClose: () => void;
}

export function RecipeDetail({ recipe, onClose }: RecipeDetailProps) {
  const title = recipe.name || recipe.title || '레시피';
  const image = recipe.image || 'https://via.placeholder.com/800x400?text=No+Image';
  const cookTime = recipe.cookTime || (recipe.cooking_time ? `${recipe.cooking_time}분` : '알 수 없음');
  const servings = recipe.servings || recipe.serving_size || 2;
  const difficulty = recipe.difficulty || '보통';
  const description = recipe.description || '';
  
  // 조리 방법 가져오기 (steps 또는 instructions)
  const instructions = recipe.steps 
    ? recipe.steps.map((step, idx) => ({
        step: step.step ?? idx + 1,
        description: step.description || ''
      }))
    : (recipe.instructions || []).map((inst, idx) => ({
        step: idx + 1,
        description: inst
      }));

  return (
    <div className="fixed inset-0 z-50 bg-black/50 overflow-y-auto">
      <div className="min-h-screen px-4 py-8">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-xl">
          {/* Header Image */}
          <div className="relative h-64 overflow-hidden rounded-t-lg">
            <img 
              src={image} 
              alt={title}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'https://via.placeholder.com/800x400?text=No+Image';
              }}
            />
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-4 right-4 bg-white/90 hover:bg-white"
              onClick={onClose}
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-6">
            <h1 className="mb-4">{title}</h1>
            
            {description && (
              <p className="text-gray-600 mb-6">{description}</p>
            )}

            {/* Recipe Info */}
            <div className="grid grid-cols-3 gap-4 mb-8 p-4 bg-gray-50 rounded-lg">
              <div className="text-center">
                <Clock className="w-5 h-5 mx-auto mb-1 text-gray-600" />
                <div className="text-sm text-gray-500">조리시간</div>
                <div>{cookTime}</div>
              </div>
              <div className="text-center">
                <Users className="w-5 h-5 mx-auto mb-1 text-gray-600" />
                <div className="text-sm text-gray-500">인분</div>
                <div>{servings}인분</div>
              </div>
              <div className="text-center">
                <ChefHat className="w-5 h-5 mx-auto mb-1 text-gray-600" />
                <div className="text-sm text-gray-500">난이도</div>
                <div>{difficulty}</div>
              </div>
            </div>

            {/* Ingredients */}
            {recipe.ingredients && recipe.ingredients.length > 0 && (
              <div className="mb-8">
                <h2 className="mb-4">재료</h2>
                <ul className="space-y-2">
                  {recipe.ingredients.map((ingredient, index) => {
                    // 대체재료인지 확인
                    const isSubstituted = recipe.substitutions?.substitution_list?.some(
                      (sub) => sub.substitute === ingredient
                    ) || false;
                    
                    return (
                      <li key={index} className="flex items-start">
                        <span className="inline-block w-2 h-2 bg-gray-400 rounded-full mt-2 mr-3"></span>
                        <div className="flex-1">
                          <span>{ingredient}</span>
                          {isSubstituted && (
                            <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                              대체재료
                            </span>
                          )}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Instructions */}
            {instructions.length > 0 && (
              <div>
                <h2 className="mb-4">조리 방법</h2>
                <ol className="space-y-4">
                  {instructions.map((instruction, index) => (
                    <li key={index} className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-black text-white rounded-full flex items-center justify-center">
                        {index + 1}
                      </div>
                      <p className="flex-1 pt-1">
                        {typeof instruction === 'string' ? instruction : instruction.description}
                      </p>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
